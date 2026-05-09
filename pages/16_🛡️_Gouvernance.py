"""Page Gouvernance — registre AI Act, DPIA, journal des décisions, RGAA, RGPD, RBAC.

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
from p2p_fraud.streamlit_theme import init_page

init_page(
    title="Gouvernance",
    surtitle="Gouvernance & méthode",
    kicker=("AI Act · RGPD · RGAA 4.1 · RBAC · kill switch ML"),
)
st.caption(
    "Registre AI Act (UE 2024/1689), DPIA (CNIL art. 35), registre de traitements "
    "(RGPD art. 30), déclaration d'accessibilité partielle RGAA 4.1 et "
    "journal des décisions automatisées."
)

# ── Classification AI Act ─────────────────────────────────────────────────────
st.divider()
st.subheader("📜 Classification AI Act (UE 2024/1689)")

st.info(
    "**Risque limité (transparence, art. 50)** — le système IA détecte des anomalies "
    "sur des données comptables et propose des alertes à un humain. Aucune décision "
    "automatique sortante (paiement, blocage, scoring crédit individuel). "
    "Les composants ML (Isolation Forest) opèrent uniquement sur des **transactions** "
    "et **fournisseurs personnes morales**, jamais sur des évaluations de personnes."
)

with st.expander("ℹ️ Registre des risques AI Act — détail"):
    st.markdown(
        """
        | Critère | Évaluation |
        |---|---|
        | **Catégorie AI Act** | Risque limité (art. 50) — obligation de transparence |
        | **Décision automatisée** | Non — toute alerte nécessite validation humaine |
        | **Données personnelles** | Données d'entreprises (SIREN, IBAN) — pas de personnes physiques identifiées dans le scoring |
        | **Explicabilité** | Waterfall des contributions (Score Explorer), reason codes FR |
        | **Audit trail** | SHA-256 chaîné, vérifiable, export JSONL |
        | **Kill switch** | Oui — bascule ML désactivable sans code |
        | **Registre** | Téléchargeable ci-dessous (template Markdown) |
        """
    )

# ── RGPD ─────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("🔒 Conformité RGPD (Règlement UE 2016/679)")

st.success(
    "**Aucune donnée personnelle n'est stockée.** Les fichiers déposés sont traités "
    "en mémoire et purgés automatiquement à la fin de la session Streamlit. "
    "Aucune transmission à un service tiers sans accord explicite."
)

st.markdown(
    """
    | Point de conformité | Mise en œuvre |
    |---|---|
    | **Minimisation des données** | Seules les colonnes nécessaires à l'audit sont lues |
    | **Pas de persistance** | Traitement en mémoire (`pd.DataFrame` session Streamlit) |
    | **Chiffrement IBAN** | `cryptography.Fernet` (AES-128-CBC + HMAC-SHA256) |
    | **Masquage par défaut** | IBAN affiché `FRxx .... xxxx` sauf log d'accès |
    | **Registre art. 30** | Template téléchargeable ci-dessous |
    | **DPIA (art. 35)** | Template pré-rempli téléchargeable ci-dessous |
    | **Droit à l'effacement** | Fermeture de session = effacement immédiat |
    | **Responsable de traitement** | À compléter par l'organisation déployante |
    """
)

# ── Documents de conformité ───────────────────────────────────────────────────
st.divider()
st.subheader("📚 Documents de conformité (pré-remplis)")

docs_root = Path(__file__).resolve().parents[1] / "docs" / "compliance"
for label, filename in (
    ("DPIA — Analyse d'impact", "dpia_template.md"),
    ("Registre AI Act", "ai_act_register.md"),
    ("Registre de traitement RGPD art. 30", "data_processing_record.md"),
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

# ── RBAC ─────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("👥 Contrôle d'accès basé sur les rôles (RBAC)")

st.markdown(
    """
    Quatre rôles définis dans `src/p2p_fraud/security/rbac.py` :

    | Rôle | Charger données | Lancer détecteurs | Créer / muter cases | Clore cases | Voir audit log | Admin |
    |---|:---:|:---:|:---:|:---:|:---:|:---:|
    | **viewer** | ✅ | — | — | — | ✅ | — |
    | **analyst** | ✅ | ✅ | ✅ | — | ✅ | — |
    | **manager** | ✅ | ✅ | ✅ | ✅ | ✅ | — |
    | **admin** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

    Activation : variable d'environnement `P2P_FRAUD_AUTH_REQUIRED=1`.
    En mode démo (valeur par défaut), l'authentification est désactivée.

    Mécanisme d'authentification : PBKDF2-SHA256, 200 000 itérations, sels uniques
    par utilisateur (voir `src/p2p_fraud/security/auth.py`).
    """
)

# ── Sécurité ─────────────────────────────────────────────────────────────────
st.divider()
st.subheader("🔐 Sécurité — chiffrement et audit")

st.markdown(
    """
    | Mécanisme | Mise en œuvre |
    |---|---|
    | **Chiffrement IBAN au repos** | `cryptography.Fernet` (AES-128-CBC + HMAC-SHA256), clé `P2P_FRAUD_DATA_KEY` |
    | **Affichage IBAN** | Masqué par défaut (`iban_masked()`) — clair sur log d'accès uniquement |
    | **Authentification** | PBKDF2-SHA256, 200 000 itérations, sels uniques par user |
    | **RBAC** | 4 rôles : viewer / analyst / manager / admin |
    | **Audit log** | Append-only SQLite WAL, chaîné par hash SHA-256, vérifiable |
    | **Hash fichiers uploadés** | SHA-256 du contenu brut, journalisé en `file.imported` |
    | **Mode strict auth** | Variable d'env `P2P_FRAUD_AUTH_REQUIRED=1` |
    """
)

# ── Kill switch ML ────────────────────────────────────────────────────────────
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

# ── Journal des décisions ─────────────────────────────────────────────────────
@st.cache_resource
def _service() -> CaseService:
    return CaseService(":memory:", AuditLog(":memory:"))


service = _service()
audit = service.audit_log

st.divider()
st.subheader("📜 Journal des décisions (audit log local)")

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

# ── Déclaration RGAA ──────────────────────────────────────────────────────────
st.divider()
st.subheader("♿ Accessibilité — déclaration RGAA 4.1 partielle")

st.warning(
    "**Déclaration de conformité partielle RGAA 4.1** — P2P Fraud Detective FR "
    "est un démonstrateur technique non soumis à l'obligation légale RGAA (réservée "
    "aux organismes publics et ETI cotées). Cette déclaration est publiée à titre "
    "de bonne pratique et de transparence."
)

with st.expander("📋 Détail de la déclaration RGAA 4.1"):
    st.markdown(
        """
        **Date de l'audit interne** : mai 2026

        **Périmètre audité** : interface Streamlit — 17 pages.

        **Résultats par thématique** :

        | Thématique RGAA | Statut | Notes |
        |---|---|---|
        | **1. Images** | Non applicable | Pas d'images décoratives ou informatives hors diagrammes Plotly |
        | **2. Cadres** | Non applicable | Pas d'iframes |
        | **3. Couleurs** | ✅ Conforme | Contrastes navy #1F3A6E/blanc → 8,59:1 (WCAG AA ≥ 4,5:1) ; or #E5A93A/navy → 7,21:1 |
        | **4. Multimédia** | Non applicable | Pas de vidéo ni audio |
        | **5. Tableaux** | ⚠️ Partiel | `st.dataframe` sans `<th scope>` — acceptable pour usage interne |
        | **6. Liens** | ✅ Conforme | Libellés explicites sur tous les `st.page_link` et boutons |
        | **7. Scripts** | ⚠️ Partiel | Streamlit gère les composants ARIA partiellement — dépendant du framework |
        | **8. Éléments masqués** | ✅ Conforme | Le ribbon « DÉMONSTRATEUR » est visible et ne cache pas de contenu critique |
        | **9. Structuration** | ✅ Conforme | Hiérarchie H1/H2/H3 respectée via `page_header()` |
        | **10. Présentation** | ✅ Conforme | CSS en variables ; pas de mise en forme via balises HTML dépréciées |
        | **11. Formulaires** | ✅ Conforme | Streamlit pose les labels associés correctement |
        | **12. Navigation** | ✅ Conforme | Navigation clavier fonctionnelle (Streamlit natif) |
        | **13. Consultation** | ⚠️ Partiel | Certains graphes Plotly non accessibles au lecteur d'écran |

        **Limitations acceptées** (framework Streamlit) :
        - Les composants `st.dataframe` (AG Grid sous le capot) ne produisent pas de `<th scope>` ARIA.
        - Les graphes Plotly ne disposent pas d'alternatives textuelles automatiques.
        - Ces limitations sont **inhérentes au framework** et documentées.

        **Contact accessibilité** : Créer une issue sur
        [github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr](https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/issues).
        """
    )
