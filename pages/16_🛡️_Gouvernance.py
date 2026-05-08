"""Page Gouvernance — registre AI Act, DPIA, journal des décisions, bouton kill ML.

Vue lecture seule pour les rôles non-admin. Permet :
- de visualiser le statut de classification AI Act du système ;
- d'accéder aux templates DPIA + AI Act + RGPD ;
- de basculer le scoring ML (Isolation Forest) hors / dans le score consolidé ;
- de visualiser le journal des décisions automatisées (vérifié intégrité).
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.cases.service import CaseService

st.set_page_config(
    page_title="Gouvernance — P2P Fraud Detective",
    page_icon="🛡️",
    layout="wide",
)
st.title("🛡️ Gouvernance IA et données")
st.caption(
    "Registre AI Act (UE 2024/1689), DPIA (CNIL art. 35), registre traitements "
    "(RGPD art. 30) et journal des décisions automatisées."
)

st.divider()
st.subheader("📜 Classification AI Act")

st.info(
    "**Risque limité (transparence, art. 50)** — le système IA détecte des anomalies "
    "sur des données comptables et propose des alertes à un humain. Aucune décision "
    "automatique sortante (paiement, blocage, scoring crédit individuel). "
    "Les composants ML (Isolation Forest) opèrent uniquement sur des **transactions** "
    "et **fournisseurs personnes morales**, jamais sur des évaluations de personnes."
)

st.divider()
st.subheader("📚 Documents de conformité (pré-remplis)")

docs_root = Path(__file__).resolve().parents[1] / "docs" / "compliance"
for label, filename in (
    ("DPIA — Analyse d'impact", "dpia_template.md"),
    ("Registre AI Act", "ai_act_register.md"),
    ("Registre de traitement RGPD", "data_processing_record.md"),
):
    path = docs_root / filename
    if path.exists():
        with st.expander(f"📄 {label} — `{filename}`"):
            st.download_button(
                "⬇️ Télécharger Markdown",
                data=path.read_text(encoding="utf-8"),
                file_name=filename,
                mime="text/markdown",
            )
            st.markdown(path.read_text(encoding="utf-8"))

st.divider()
st.subheader("⚙️ Bascule scoring ML (Isolation Forest)")

ml_enabled = st.session_state.get("ml_scoring_enabled", True)
new_state = st.toggle(
    "Activer le scoring ML (Isolation Forest)",
    value=ml_enabled,
    help=(
        "Désactive l'apport ML au score consolidé. Les détecteurs déterministes "
        "(master data, sanctions, doublons, seuils, sirene, graphe) restent actifs."
    ),
)
if new_state != ml_enabled:
    st.session_state["ml_scoring_enabled"] = new_state
    st.success(
        f"Scoring ML {'activé' if new_state else 'désactivé'}. "
        "L'agrégation tiendra compte de cette bascule au prochain calcul."
    )


@st.cache_resource
def _service() -> CaseService:
    return CaseService(":memory:", AuditLog(":memory:"))


service = _service()
audit = service.audit_log

st.divider()
st.subheader("📜 Journal des décisions (audit log)")

c1, c2 = st.columns(2)
c1.metric("Entrées", len(audit))
if st.button("Vérifier l'intégrité de la chaîne hash"):
    valid, invalid = audit.verify_chain()
    if valid:
        st.success(f"✅ Chaîne valide ({len(audit)} entrées).")
    else:
        st.error(f"❌ Chaîne altérée. Séquences invalides : {invalid}")

if len(audit) > 0:
    import pandas as pd

    rows = audit.all()
    df = pd.DataFrame(
        [
            {
                "seq": e.seq,
                "at": e.at,
                "actor": e.actor,
                "kind": e.kind,
                "payload_summary": str(e.payload)[:120],
            }
            for e in rows[-100:]
        ]
    )
    st.dataframe(df, use_container_width=True, height=300)

st.divider()
st.subheader("🔐 Sécurité — chiffrement et RBAC")

st.markdown(
    """
    | Mécanisme | Mise en œuvre |
    |---|---|
    | **Chiffrement IBAN au repos** | `cryptography.Fernet` (AES-128-CBC + HMAC-SHA256), clé `P2P_FRAUD_DATA_KEY` |
    | **Affichage IBAN** | Masqué par défaut (`iban_masked()`) — clair sur log d'accès uniquement |
    | **Authentification** | PBKDF2-SHA256, 200 000 itérations, sels uniques par user |
    | **RBAC** | 4 rôles : viewer / analyst / manager / admin |
    | **Audit log** | Append-only SQLite, chaîné par hash SHA-256, vérifiable |
    | **Mode strict auth** | Variable d'env `P2P_FRAUD_AUTH_REQUIRED=1` |
    """
)
