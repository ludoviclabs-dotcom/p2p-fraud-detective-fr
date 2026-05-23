"""Evidence Pack — dossier de preuve exportable et vérifiable.

Selon le spec MandateGuard §09 : pour chaque alerte ou litige critique,
construire un dossier de preuve déterministe contenant :
- métadonnées (tenant, sujet, domaine, engine_version)
- événement source (DebitEvent masqué)
- assessment (signaux, score, décision, level)
- match (mandat matché ou candidats inactifs)
- timeline (audit chain entries liées au sujet)
- hash d'intégrité + ancrage chain

Garanties :
- **Déterministe** : 2 builds successifs du même sujet → même `pack_hash`.
- **Sans PII** : IBAN toujours fingerprinté ou masqué, jamais en clair.
- **Vérifiable** : `EvidenceVerifier.verify()` recalcule le hash et confronte
  à l'ancrage audit chain.
- **Rejouable** : `engine_version` figée dans le pack.
"""

from p2p_fraud.evidence.builder import EvidenceBuilder
from p2p_fraud.evidence.canonical import canonical_json, sha256_hex
from p2p_fraud.evidence.renderer import render_html_report
from p2p_fraud.evidence.service import EvidenceService
from p2p_fraud.evidence.types import (
    EvidencePackInput,
    EvidencePackRecord,
    EvidenceVerificationResult,
)
from p2p_fraud.evidence.verifier import EvidenceVerifier

__all__ = [
    "EvidenceBuilder",
    "EvidencePackInput",
    "EvidencePackRecord",
    "EvidenceService",
    "EvidenceVerificationResult",
    "EvidenceVerifier",
    "canonical_json",
    "render_html_report",
    "sha256_hex",
]
