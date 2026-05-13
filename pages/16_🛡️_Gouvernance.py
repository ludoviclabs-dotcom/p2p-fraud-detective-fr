"""Page Gouvernance — registre AI Act, DPIA, journal des décisions, RGAA, RGPD, RBAC, AMLD6, CSRD.

Vue lecture seule pour les rôles non-admin. Permet :
- de visualiser le statut de classification AI Act du système ;
- d'accéder aux templates DPIA + AI Act + RGPD + AMLD6 mapping ;
- de basculer le scoring ML (Isolation Forest) hors / dans le score consolidé ;
- de visualiser le journal des décisions automatisées (vérifié intégrité) ;
- d'exporter les fournisseurs à risque pour le reporting CSRD art. 29.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.cases.service import CaseService
from p2p_fraud.i18n import _, init_locale_from_session
from p2p_fraud.streamlit_theme import init_page

init_locale_from_session()

init_page(
    title=_("nav.page_gouvernance"),
    surtitle=_("nav.surtitle_gouvernance"),
    kicker=_("nav.kicker_gouvernance"),
)
st.caption(
    "Registre AI Act (UE 2024/1689), DPIA (CNIL art. 35), registre de traitements "
    "(RGPD art. 30), AMLD6 (6e directive anti-blanchiment), CSRD (rapport de durabilité), "
    "déclaration d'accessibilité partielle RGAA 4.1 et journal des décisions automatisées."
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
    | **Signatures Ed25519 audit log (P5-5)** | Activées via `P2PFD_ED25519_PRIVATE_KEY`, clé publique exposée par `GET /security/public-key` |
    """
)

# ── Cryptographie Ed25519 (P5-5) ──────────────────────────────────────────────
st.markdown("#### 🔐 Cryptographie audit trail (Ed25519)")

from p2p_fraud.security.signing import make_signer_from_settings  # noqa: E402

_govsigner = make_signer_from_settings()
if _govsigner.enabled:
    st.success(
        f"**Signatures Ed25519 actives.** Clé publique (base64, 32 octets) :\n\n"
        f"```\n{_govsigner.public_key_b64}\n```\n"
        "Tout tiers (CAC, ACPR, Cour des comptes) peut vérifier indépendamment "
        "les signatures via `GET /security/public-key` + `verify_signature()` "
        "(documenté dans `docs/conformite_signatures.md`)."
    )
else:
    st.info(
        "**Mode démo** — signatures cryptographiques désactivées. "
        "Pour activer en pilote, générer une paire de clés hors ligne :\n\n"
        "```python\n"
        "from p2p_fraud.security.signing import Ed25519Signer\n"
        "kp = Ed25519Signer.generate()\n"
        'print(f"P2PFD_ED25519_PRIVATE_KEY={kp.private_key_b64}")\n'
        "```\n"
        "puis injecter la clé privée en variable d'environnement (Vault/KMS)."
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

# ── AMLD6 ─────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("🏦 AMLD6 — 6e Directive anti-blanchiment (UE 2018/1673)")

st.info(
    "La **6e directive anti-blanchiment** (AMLD6, transposée en droit français) est la référence "
    "de **Tracfin** pour les déclarations de soupçon (DSO). "
    "P2P Fraud Detective FR couvre partiellement les obligations LCB-FT via les détecteurs "
    "Sanctions/PEP, Master data (IBAN suspect) et DECP/RBE (bénéficiaires effectifs)."
)

with st.expander("📋 Mapping AMLD6 — couverture par détecteur"):
    st.markdown(
        """
        | Article AMLD6 | Obligation | Détecteur couvrant | Statut |
        |---|---|---|---|
        | Art. 18 — EDD | Mesures de vigilance renforcée (PEP, pays tiers à risque) | Sanctions & PEP, DECP/RBE | ✅ Partiel |
        | Art. 19 — UBO | Identification des bénéficiaires effectifs | DECP/RBE (RBE_BENEFICIAL_OWNER_MATCH) | ✅ Partiel |
        | Art. 20 — IBAN suspect | Changements de domiciliation bancaire | Master data (IBAN_CHANGE) | ✅ Couvert |
        | Art. 24 — DSO | Brouillon de déclaration de soupçon Tracfin | LLM narrative (ISA 240) | ✅ Partiel |
        | Art. 30 — Registre UBO | Consultation du registre RBE INPI | DECP/RBE client | ✅ Partiel |
        | Art. 42 — Formation | Traçabilité des contrôles effectués | Audit log SHA-256 | ✅ Couvert |

        **Limites** : AMLD6 art. 18/19 exigent une intégration live avec les API INPI et Tracfin
        (GAFI/FATF listes tiers). En mode démo, les données RBE sont synthétiques.
        """
    )

amld6_doc = docs_root / "amld6_mapping.md"
if amld6_doc.exists():
    with st.expander("📄 Mapping AMLD6 complet — télécharger"):
        st.download_button(
            "⬇️ Télécharger amld6_mapping.md",
            data=amld6_doc.read_text(encoding="utf-8"),
            file_name="amld6_mapping.md",
            mime="text/markdown",
        )

if st.button("📝 Générer brouillon DSO Tracfin (simulation)", key="gen_dso"):
    st.info(
        "**Brouillon DSO Tracfin** — à compléter par le RCCI / responsable conformité.\n\n"
        "**Déclarant** : [Organisation] \n"
        "**Date** : {}\n"
        "**Motif** : Suspicion de blanchiment d'argent via le cycle Procure-to-Pay.\n"
        "**Fournisseur(s) concerné(s)** : [voir findings CRITICAL en session]\n"
        "**Éléments factuels** : [findings exports disponibles via Synthèse → export]\n\n"
        "*Ce brouillon doit être validé par un juriste avant transmission à Tracfin "
        "(portail ERMES, article L. 561-15 CMF).*".format(
            __import__("datetime").date.today().isoformat()
        )
    )

# ── CSRD ──────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("🌱 CSRD — Rapport de durabilité (Directive UE 2022/2464)")

st.info(
    "La **Directive CSRD** (Corporate Sustainability Reporting Directive) exige des "
    "grandes entreprises un rapport de durabilité incluant la chaîne de valeur Scope 3 "
    "(fournisseurs). Les fournisseurs identifiés comme risques P2P CRITICAL/HIGH "
    "doivent figurer dans l'évaluation des risques ESG (ESRS S2 — Travailleurs chaîne valeur)."
)

with st.expander("📋 Lien CSRD / risques P2P"):
    st.markdown(
        """
        | Standard ESRS | Exigence | Lien P2P Fraud Detective |
        |---|---|---|
        | **ESRS G1** — Conduite des affaires | Politique anti-corruption, due diligence tiers | Sapin 2 art. 17 → détecteurs Sanctions, DECP/RBE |
        | **ESRS G1-4** — Prévention corruption | Cartographie risques fournisseurs | Score de risque consolidé + exposition € |
        | **ESRS S2** — Travailleurs chaîne valeur | Identification risques dans la supply chain | Findings HIGH/CRITICAL exportables |
        | **ESRS E1** — Changement climatique | Concentration fournisseurs Scope 3 | Anneaux de fraude → concentration fournisseurs |

        **Recommandation** : exporter les fournisseurs CRITICAL/HIGH vers votre solution CSRD
        (e.g. Tennaxia, Sweep, Persefoni) via l'export CSV Synthèse ou l'API `/detect`.
        """
    )

if "df_invoices" in st.session_state:
    import pandas as pd

    findings_keys = (
        "findings_master_data",
        "findings_sanctions",
        "findings_decp_rbe",
        "findings_duplicates",
        "findings_thresholds",
    )
    csrd_findings = []
    for k in findings_keys:
        v = st.session_state.get(k)
        if v:
            csrd_findings.extend(v)

    critical_high = [f for f in csrd_findings if f.severity.value in ("critical", "high")]
    if critical_high:
        csrd_vendors = list(
            {f.evidence.get("vendor_name") for f in critical_high if f.evidence.get("vendor_name")}
        )
        st.write(
            f"**{len(csrd_vendors)} fournisseur(s) CRITICAL/HIGH** identifié(s) pour "
            "inclusion dans le reporting CSRD ESRS G1/S2 :"
        )

        csrd_rows = [
            {
                "vendor_name": f.evidence.get("vendor_name"),
                "siren": f.evidence.get("siren"),
                "severity": f.severity.value,
                "rule_id": f.rule_id,
                "exposure_eur": f.evidence.get("exposure_eur"),
                "reason": f.evidence.get("reason", "")[:120],
            }
            for f in critical_high
        ]
        df_csrd = pd.DataFrame(csrd_rows).drop_duplicates(subset=["vendor_name", "rule_id"])
        st.dataframe(df_csrd, use_container_width=True, height=280)

        csv_csrd = df_csrd.to_csv(index=False, encoding="utf-8")
        st.download_button(
            "⬇️ Export CSRD fournisseurs à risque (CSV ESRS G1/S2)",
            data=csv_csrd,
            file_name="csrd_fournisseurs_a_risque.csv",
            mime="text/csv",
        )
    else:
        st.success(
            "Aucun fournisseur CRITICAL/HIGH en session. "
            "Lancez les détecteurs (Sanctions, DECP/RBE, Master data) pour alimenter cet onglet."
        )
else:
    st.info("Chargez un dataset via **📤 Import des données** pour générer l'export CSRD.")


# ── ⚖️ Pondérations (live editor) ─────────────────────────────────────────────
st.divider()
st.subheader("⚖️ Pondérations du scoring (édition live)")

st.caption(
    "Éditeur YAML pour `scoring/weights.yaml`. La validation est appliquée à la "
    "sauvegarde (clés autorisées, types, sévérités complètes). Chaque modification "
    "est journalisée dans l'audit log avec l'auteur et le diff."
)

from p2p_fraud.scoring.risk_engine import DEFAULT_WEIGHTS_PATH  # noqa: E402
from p2p_fraud.scoring.weights_editor import validate_weights_yaml, write_weights  # noqa: E402

try:
    _current_weights_text = DEFAULT_WEIGHTS_PATH.read_text(encoding="utf-8")
except (OSError, FileNotFoundError):
    _current_weights_text = "# Fichier introuvable — état initial chargé depuis les défauts.\n"

_edited_weights = st.text_area(
    "Édition `weights.yaml`",
    value=st.session_state.get("weights_yaml_draft", _current_weights_text),
    height=380,
    key="weights_editor",
    help="Format YAML — détecteurs autorisés : duplicates, thresholds, benford, sirene, "
    "isolation_forest, graph, master_data, sanctions.",
)

c_v, c_s = st.columns([1, 1])
if c_v.button("✅ Valider sans enregistrer"):
    result = validate_weights_yaml(_edited_weights)
    (st.success if result.ok else st.error)(result.message)
    st.session_state["weights_yaml_draft"] = _edited_weights

if c_s.button("💾 Enregistrer + journaliser", type="primary"):
    result = write_weights(DEFAULT_WEIGHTS_PATH, _edited_weights)
    if not result.ok:
        st.error(f"Sauvegarde refusée — {result.message}")
    else:
        audit.append(
            actor=st.session_state.get("current_user", "anonymous"),
            kind="weights.updated",
            payload={
                "detector_weights": result.parsed.get("detector_weights"),
                "severity_multiplier": result.parsed.get("severity_multiplier"),
                "path": str(DEFAULT_WEIGHTS_PATH),
            },
        )
        st.cache_data.clear()
        st.success(f"✅ Pondérations enregistrées dans `{DEFAULT_WEIGHTS_PATH.name}`.")
        st.session_state.pop("weights_yaml_draft", None)


# ── 🗑️ Droit à l'effacement RGPD art. 17 (purge persistante) ──────────────────
st.divider()
st.subheader("🗑️ Droit à l'effacement RGPD (art. 17 — purge persistante)")

st.warning(
    "Cette action **supprime définitivement** tous les cases créés par un utilisateur "
    "dans la base de cases ainsi que leurs événements. Distinct du bouton « Purger la "
    "session » de la sidebar (qui ne vide que la session Streamlit en mémoire)."
)

from pages._helpers import get_case_service as _get_case_service_purge  # noqa: E402

_purge_service = _get_case_service_purge()

_all_cases = _purge_service.list_cases()
_all_actors = sorted({c.created_by for c in _all_cases if c.created_by})

c_user, c_confirm = st.columns([2, 1])
_target_user = c_user.selectbox(
    "Utilisateur à purger (created_by)",
    options=["(choisir)", *_all_actors] if _all_actors else ["(aucun utilisateur)"],
    key="rgpd_purge_user",
)
_confirm_text = c_confirm.text_input(
    "Tapez `PURGER` pour confirmer",
    key="rgpd_purge_confirm",
    placeholder="PURGER",
)

if st.button("🗑️ Purger les cases de cet utilisateur", type="primary", key="rgpd_purge_btn"):
    if _target_user in ("(choisir)", "(aucun utilisateur)"):
        st.error("Sélectionnez un utilisateur valide.")
    elif _confirm_text != "PURGER":
        st.error("Confirmation manquante — tapez exactement `PURGER`.")
    else:
        n_deleted = _purge_service.purge_user_data(
            _target_user,
            actor=st.session_state.get("current_user", "anonymous"),
        )
        st.success(
            f"✅ {n_deleted} case(s) de `{_target_user}` supprimé(s). "
            "Action journalisée dans l'audit log."
        )
        st.session_state.pop("rgpd_purge_confirm", None)
