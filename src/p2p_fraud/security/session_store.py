"""Sessions HTTP signées via `itsdangerous` (HMAC-SHA256).

Deux usages :
- **Cookie de session OIDC** (`SessionSerializer`) — stocke `sub`, `email`,
  `name`, `groups`, `role`, `exp` après authentification réussie.
- **Cookie d'état OAuth** (`StateSerializer`) — stocke `state`, `nonce`,
  `code_verifier`, `redirect_after` durant le round-trip browser → IdP →
  callback. TTL court (10 min).

Pas de stockage côté serveur — tout est self-contained dans le cookie signé.
Cohérent avec un déploiement scale-out (Cloud Run, Aiven, sans state shared).

Sécurité :
- Cookies marqués `httponly`, `samesite=lax`, `secure` (en prod via reverse proxy TLS).
- Signature HMAC-SHA256 dérivée de `oidc_session_secret` (≥ 32 octets recommandés).
- Expiration vérifiée à la désérialisation (`max_age` côté lecture).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

log = logging.getLogger(__name__)

SESSION_COOKIE_NAME = "p2pfd_session"
STATE_COOKIE_NAME = "p2pfd_oidc_state"
STATE_MAX_AGE = 600  # 10 minutes — round-trip OAuth maximum


@dataclass
class SessionSerializer:
    """Signe et vérifie un payload arbitraire (dict JSON-sérialisable).

    Args:
        secret_key: clé HMAC partagée (au moins 32 octets aléatoires).
        salt: domaine de signature — sépare les usages (session vs state).
        max_age_seconds: durée maximale de validité du token (8 h par défaut).
    """

    secret_key: str
    salt: str = "p2pfd-session"
    max_age_seconds: int = 8 * 3600

    def __post_init__(self) -> None:
        if not self.secret_key:
            raise ValueError(
                "secret_key vide — configurez `OIDC_SESSION_SECRET` (≥ 32 octets aléatoires)."
            )
        self._serializer = URLSafeTimedSerializer(self.secret_key, salt=self.salt)

    def dumps(self, payload: dict[str, Any]) -> str:
        """Sérialise + signe le payload."""
        return self._serializer.dumps(payload)

    def loads(self, token: str) -> dict[str, Any] | None:
        """Vérifie la signature + l'expiration. Retourne `None` si invalide."""
        try:
            data = self._serializer.loads(token, max_age=self.max_age_seconds)
        except SignatureExpired:
            log.info("Session token expiré.")
            return None
        except BadSignature:
            log.warning("Signature de session invalide — possible tampering.")
            return None
        if not isinstance(data, dict):
            return None
        return data


def make_session_serializer(secret_key: str, *, max_age: int = 8 * 3600) -> SessionSerializer:
    """Helper : SessionSerializer pour les sessions utilisateur (8 h par défaut)."""
    return SessionSerializer(secret_key=secret_key, salt="p2pfd-session", max_age_seconds=max_age)


def make_state_serializer(secret_key: str) -> SessionSerializer:
    """Helper : SessionSerializer pour le state OAuth (10 min, salt distinct)."""
    return SessionSerializer(
        secret_key=secret_key, salt="p2pfd-oidc-state", max_age_seconds=STATE_MAX_AGE
    )
