"""Dispatcher webhook sortant — POST signé HMAC-SHA256, retry tenacity.

Singleton instancié au boot de l'API ou de Streamlit, branché sur le
`CaseService` via injection. Si `Settings.webhook_url` est vide, le
dispatcher est désactivé (no-op silencieux).

Sécurité :
- Signature HMAC-SHA256 calculée sur le **payload JSON complet**.
- Header `X-P2PFD-Signature: sha256=<hex>` pour validation côté récepteur.
- Le `webhook_secret` doit être partagé hors-bande (NEVER dans les logs).
- Timeout strict (`Settings.webhook_timeout`, défaut 5s) pour éviter le
  blocage de la chaîne d'audit en cas de SIEM injoignable.

Fiabilité :
- Retry tenacity 3 tentatives, backoff exponentiel (1s → 2s → 4s).
- Retry uniquement sur erreurs réseau (`ConnectionError`, `Timeout`,
  `HTTPError` 5xx). Les 4xx sont des erreurs de configuration, on ne
  retry pas — un log.error structuré est émis.
- Échec final → `WebhookDeliveryError` levée, captée par le caller qui
  log mais ne casse pas l'opération métier (l'audit log local fait foi).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Any

import requests
from tenacity import (
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from p2p_fraud.webhooks.events import WebhookEvent

log = logging.getLogger(__name__)

SIGNATURE_HEADER = "X-P2PFD-Signature"
SIGNATURE_ALGO = "sha256"
USER_AGENT = "p2p-fraud-detective-fr/0.5.0"


class WebhookDeliveryError(RuntimeError):
    """Le webhook n'a pas pu être livré après les retries."""


def sign_payload(payload: bytes | str, secret: str) -> str:
    """Calcule la signature HMAC-SHA256 et la formate `sha256=<hex>`.

    Args:
        payload: corps JSON brut (str ou bytes).
        secret: clé HMAC partagée avec le récepteur (jamais loguée).

    Returns:
        Chaîne `sha256=<hex>` à placer dans l'en-tête `X-P2PFD-Signature`.
    """
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    if isinstance(secret, str):
        secret = secret.encode("utf-8")  # type: ignore[assignment]
    digest = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return f"{SIGNATURE_ALGO}={digest}"


_RETRYABLE = (
    requests.ConnectionError,
    requests.Timeout,
    # 5xx HTTP est levé en `HTTPError` après resp.raise_for_status()
    requests.HTTPError,
)


class WebhookDispatcher:
    """Émet les `WebhookEvent` vers `webhook_url` avec signature et retry.

    Args:
        url: URL du SIEM/ERP destinataire (`""` → dispatcher désactivé).
        secret: secret HMAC partagé.
        timeout: timeout HTTP (connect + read).
        session: session `requests` (utile pour mocks dans les tests).
    """

    def __init__(
        self,
        *,
        url: str = "",
        secret: str = "",
        timeout: float = 5.0,
        session: requests.Session | None = None,
    ) -> None:
        self.url = url
        self.secret = secret
        self.timeout = timeout
        self._session = session or requests.Session()
        self._sent: list[dict[str, Any]] = []  # historique en mémoire (debug UI)

    @property
    def enabled(self) -> bool:
        return bool(self.url)

    @property
    def sent_history(self) -> list[dict[str, Any]]:
        """Liste des dernières émissions (pour la page Alertes — UI debug)."""
        return list(self._sent[-50:])  # cap

    def dispatch(self, event: WebhookEvent) -> dict[str, Any]:
        """POST signé synchrone. Idempotent côté caller (no-op si désactivé).

        Returns:
            Dict avec le résultat : `{"status": int, "ok": bool, "duration_ms": ...}`.

        Raises:
            WebhookDeliveryError: si toutes les tentatives ont échoué.
        """
        if not self.enabled:
            return {"status": 0, "ok": False, "skipped": True, "reason": "disabled"}

        payload = event.to_signed_json()
        signature = sign_payload(payload, self.secret) if self.secret else ""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        }
        if signature:
            headers[SIGNATURE_HEADER] = signature

        result: dict[str, Any] = {"event_id": event.id, "type": str(event.type)}
        try:
            response = self._post_with_retry(payload, headers)
            result.update(
                status=response.status_code,
                ok=True,
                duration_ms=int(response.elapsed.total_seconds() * 1000),
            )
        except _RETRYABLE as exc:
            log.error(
                "webhook delivery failed after retries: %s | url=%s event_id=%s",
                exc,
                self.url,
                event.id,
            )
            result.update(status=0, ok=False, error=str(exc))
            self._sent.append(result)
            raise WebhookDeliveryError(str(exc)) from exc
        self._sent.append(result)
        return result

    def _post_with_retry(self, payload: str, headers: dict[str, str]) -> requests.Response:
        attempts = Retrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=4),
            retry=retry_if_exception_type(_RETRYABLE),
            reraise=True,
        )
        for attempt in attempts:
            with attempt:
                response = self._session.post(
                    self.url,
                    data=payload.encode("utf-8"),
                    headers=headers,
                    timeout=self.timeout,
                )
                # 4xx → ne PAS retry, lever immédiatement une exception
                # non-retryable pour ne pas masquer un problème de config.
                if 400 <= response.status_code < 500:
                    log.error(
                        "webhook returned 4xx (non-retryable): %s | url=%s",
                        response.status_code,
                        self.url,
                    )
                    raise WebhookDeliveryError(
                        f"HTTP {response.status_code} (client error, no retry)"
                    )
                response.raise_for_status()  # 5xx → retry
                return response
        raise WebhookDeliveryError("retry loop exited unexpectedly")  # pragma: no cover


def make_dispatcher_from_settings(settings=None) -> WebhookDispatcher:
    """Construit un dispatcher en lisant `Settings.webhook_url` etc."""
    from p2p_fraud.config import get_settings

    s = settings or get_settings()
    return WebhookDispatcher(
        url=s.webhook_url,
        secret=s.webhook_secret,
        timeout=s.webhook_timeout,
    )


def verify_signature(*, payload: bytes | str, signature_header: str, secret: str) -> bool:
    """Vérifie une signature `X-P2PFD-Signature` reçue côté SIEM.

    Méthode statique utile pour le récepteur (équivalent côté serveur du
    `sign_payload`). Documentée dans le SDK pour réutilisation.
    """
    if not signature_header or not signature_header.startswith(f"{SIGNATURE_ALGO}="):
        return False
    expected = sign_payload(payload, secret)
    return hmac.compare_digest(expected, signature_header)


# Pour des intégrations tierces qui veulent juste signer sans HTTP :
__all__ = [
    "WebhookDeliveryError",
    "WebhookDispatcher",
    "make_dispatcher_from_settings",
    "sign_payload",
    "verify_signature",
]


# Stub pour json import (mypy ne se plaint pas, json est utilisé par Pydantic)
_ = json
