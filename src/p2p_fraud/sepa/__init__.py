"""SEPA Mandate Guard — coffre-fort de mandats et ingestion prélèvements.

Module conçu selon le spec MandateGuard §07. Trois services principaux :

- `MandateService` : CRUD du coffre-fort (create, sign, revoke, find).
- `DebitEventService` : ingestion idempotente d'un prélèvement observé.
- `MandateMatcher` : appariement déterministe d'un prélèvement à un mandat.

Toute mutation crée un événement dans l'audit log existant (hash-chain
Ed25519). Les IBAN ne sont jamais persistés en clair — chiffrement Fernet
+ fingerprint HMAC (cf. `security/iban.py`, `security/crypto.py`).
"""

from p2p_fraud.sepa.analyzer import (
    SEPA_ENGINE_VERSION,
    AnalyzedDebit,
    SepaAnalyzer,
    build_sepa_engine,
)
from p2p_fraud.sepa.debit_event import DebitEventInput, DebitEventRecord, DebitEventService
from p2p_fraud.sepa.mandate import (
    MandateInput,
    MandateNotFoundError,
    MandateRecord,
    MandateService,
    MandateStateError,
)
from p2p_fraud.sepa.matcher import MandateMatcher, MatchResult, MatchWarning
from p2p_fraud.sepa.rules import SepaRiskContext, build_sepa_rules
from p2p_fraud.sepa.types import MandateScheme, MandateStatus, SequenceType

__all__ = [
    "SEPA_ENGINE_VERSION",
    "AnalyzedDebit",
    "DebitEventInput",
    "DebitEventRecord",
    "DebitEventService",
    "MandateInput",
    "MandateMatcher",
    "MandateNotFoundError",
    "MandateRecord",
    "MandateScheme",
    "MandateService",
    "MandateStateError",
    "MandateStatus",
    "MatchResult",
    "MatchWarning",
    "SepaAnalyzer",
    "SepaRiskContext",
    "SequenceType",
    "build_sepa_engine",
    "build_sepa_rules",
]
