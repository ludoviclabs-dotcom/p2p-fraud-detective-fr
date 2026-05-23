"""Sécurité des webhooks entrants — Sprint 5 MandateGuard.

Selon le spec §05 :
- Vérifie la signature HMAC-SHA256 sur le corps brut
- Refuse les requêtes hors fenêtre temporelle (anti-replay)
- Persiste un idempotency_key pour rejeter les redéliveries
- Headers normalisés : `X-MG-Timestamp` (ISO 8601), `X-MG-Signature`
  (préfixe `sha256=` + hex)

Conçu en FastAPI dependency : `Depends(verify_webhook)` sur n'importe quel
endpoint. Le secret est lu depuis `Settings.webhook_inbound_secret` (nouveau).
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Final

from fastapi import HTTPException, Request, status
from sqlalchemy import Engine, text

from p2p_fraud.config import get_settings
from p2p_fraud.persistence import Base, make_engine

log = logging.getLogger(__name__)

HEADER_TIMESTAMP: Final[str] = "X-MG-Timestamp"
HEADER_SIGNATURE: Final[str] = "X-MG-Signature"
HEADER_IDEMPOTENCY: Final[str] = "X-MG-Idempotency-Key"
SIGNATURE_PREFIX: Final[str] = "sha256="

# Fenêtre de tolérance temporelle anti-replay
DEFAULT_TOLERANCE_SECONDS: Final[int] = 300  # 5 min


class WebhookVerificationError(HTTPException):
    """Erreur de validation d'un webhook entrant."""

    def __init__(self, detail: str, *, code: str = "WEBHOOK_REJECTED") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED
            if code == "WEBHOOK_UNAUTHORIZED"
            else status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": code, "message": detail}},
        )


@dataclass(frozen=True)
class VerifiedWebhook:
    """Résultat d'une vérification réussie — passé au handler."""

    body: bytes
    timestamp: datetime
    idempotency_key: str | None
    signature: str


def compute_signature(body: bytes, secret: bytes) -> str:
    """HMAC-SHA256(secret, body) → hex avec préfixe `sha256=`."""
    digest = hmac.new(secret, body, hashlib.sha256).hexdigest()
    return f"{SIGNATURE_PREFIX}{digest}"


def constant_time_equals(a: str, b: str) -> bool:
    """Comparaison constant-time (anti-timing attack)."""
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def parse_timestamp(value: str | None) -> datetime:
    if not value:
        raise WebhookVerificationError(
            f"En-tête {HEADER_TIMESTAMP} manquant",
            code="WEBHOOK_MISSING_TIMESTAMP",
        )
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise WebhookVerificationError(
            f"Format timestamp invalide : {value!r}",
            code="WEBHOOK_INVALID_TIMESTAMP",
        ) from exc


def verify_signature(
    body: bytes,
    *,
    timestamp_header: str | None,
    signature_header: str | None,
    secret: bytes,
    tolerance_seconds: int = DEFAULT_TOLERANCE_SECONDS,
    now: datetime | None = None,
) -> datetime:
    """Vérifie le timestamp + la signature HMAC. Retourne le timestamp parsé.

    Lève `WebhookVerificationError` si la signature est invalide ou si le
    timestamp est en dehors de la fenêtre.
    """
    ts = parse_timestamp(timestamp_header)
    current = now or datetime.now(UTC)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    delta = abs((current - ts).total_seconds())
    if delta > tolerance_seconds:
        raise WebhookVerificationError(
            f"Timestamp hors fenêtre ({int(delta)}s > {tolerance_seconds}s)",
            code="WEBHOOK_REPLAY",
        )
    if not signature_header:
        raise WebhookVerificationError(
            f"En-tête {HEADER_SIGNATURE} manquant",
            code="WEBHOOK_MISSING_SIGNATURE",
        )
    if not signature_header.startswith(SIGNATURE_PREFIX):
        raise WebhookVerificationError(
            f"Signature mal formée (attendu '{SIGNATURE_PREFIX}<hex>')",
            code="WEBHOOK_INVALID_SIGNATURE",
        )
    expected = compute_signature(body, secret)
    if not constant_time_equals(signature_header, expected):
        raise WebhookVerificationError(
            "Signature HMAC invalide",
            code="WEBHOOK_UNAUTHORIZED",
        )
    return ts


class WebhookIdempotencyStore:
    """Store d'idempotency_keys reçues — empêche le replay applicatif.

    Backend SQLAlchemy, partage le même Engine que les autres services. Les
    entrées expirent automatiquement après 48h (purge périodique optionnelle
    via cron).
    """

    _TABLE = "webhook_events"

    def __init__(self, *, engine: Engine | None = None, db_path: str = ":memory:") -> None:
        self._engine = engine or make_engine(db_path=db_path)
        Base.metadata.create_all(self._engine, checkfirst=True)
        self._ensure_table()

    def _ensure_table(self) -> None:
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    f"CREATE TABLE IF NOT EXISTS {self._TABLE} ("
                    "idempotency_key VARCHAR(255) PRIMARY KEY, "
                    "received_at TEXT NOT NULL, "
                    "source VARCHAR(64) NOT NULL, "
                    "signature VARCHAR(80) NOT NULL"
                    ")"
                )
            )

    def already_seen(self, key: str) -> bool:
        with self._engine.begin() as conn:
            row = conn.execute(
                text(
                    f"SELECT idempotency_key FROM {self._TABLE} WHERE idempotency_key = :k LIMIT 1"
                ),
                {"k": key},
            ).first()
        return row is not None

    def remember(self, key: str, *, source: str, signature: str) -> None:
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    f"INSERT OR IGNORE INTO {self._TABLE} "
                    "(idempotency_key, received_at, source, signature) "
                    "VALUES (:k, :now, :src, :sig)"
                ),
                {
                    "k": key,
                    "now": datetime.now(UTC).isoformat(),
                    "src": source,
                    "sig": signature,
                },
            )

    def purge_older_than(self, days: int = 2) -> int:
        """Retire les entrées plus vieilles que `days` jours."""
        cutoff = (datetime.now(UTC) - timedelta(days=days)).isoformat()
        with self._engine.begin() as conn:
            result = conn.execute(
                text(f"DELETE FROM {self._TABLE} WHERE received_at < :c"),
                {"c": cutoff},
            )
        return result.rowcount or 0


async def verify_inbound_webhook(
    request: Request,
    *,
    secret: bytes | None = None,
    store: WebhookIdempotencyStore | None = None,
    tolerance_seconds: int = DEFAULT_TOLERANCE_SECONDS,
    source: str = "default",
) -> VerifiedWebhook:
    """Dependency FastAPI : vérifie signature + timestamp + idempotence.

    Lit le body brut (UNE seule fois — le caller doit le mémoriser et ne plus
    appeler `request.body()` ensuite). Pour faciliter l'usage en routes, le
    body brut est aussi exposé dans `VerifiedWebhook.body`.
    """
    if secret is None:
        cfg_secret = get_settings().webhook_inbound_secret
        if not cfg_secret:
            raise WebhookVerificationError(
                "webhook_inbound_secret non configuré côté serveur",
                code="WEBHOOK_NOT_CONFIGURED",
            )
        secret = cfg_secret.encode("utf-8")

    body = await request.body()
    timestamp_header = request.headers.get(HEADER_TIMESTAMP)
    signature_header = request.headers.get(HEADER_SIGNATURE)
    idempotency_key = request.headers.get(HEADER_IDEMPOTENCY)

    ts = verify_signature(
        body,
        timestamp_header=timestamp_header,
        signature_header=signature_header,
        secret=secret,
        tolerance_seconds=tolerance_seconds,
    )

    if store is not None and idempotency_key:
        if store.already_seen(idempotency_key):
            raise WebhookVerificationError(
                f"idempotency_key déjà reçue : {idempotency_key}",
                code="WEBHOOK_DUPLICATE",
            )
        store.remember(idempotency_key, source=source, signature=signature_header)  # type: ignore[arg-type]

    return VerifiedWebhook(
        body=body,
        timestamp=ts,
        idempotency_key=idempotency_key,
        signature=signature_header,  # type: ignore[arg-type]
    )
