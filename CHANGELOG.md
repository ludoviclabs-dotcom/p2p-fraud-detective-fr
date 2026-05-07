# Changelog

Toutes les évolutions notables sont documentées ici. Format inspiré de
[Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) ; le projet suit
[SemVer](https://semver.org/).

## [Unreleased]

### Ajouté
- ADR-0001 « Repositionnement produit » (Vendor & Payment Integrity FR-native).
- ADR-0002 « Benford rétrogradé » (scoping orienté risque, hors score consolidé par défaut).
- ADR-0003 « Streamlit façade démo, FastAPI prévu en M3 ».
- Sprint 1 — Master data history :
  - Modèle `VendorMasterEvent` (typé : IBAN, nom, adresse, SIREN, contact, statut, dormant).
  - Détecteur `master_data_changes` : changement d'IBAN sans 4-eyes, dormant réactivé,
    changement nom + IBAN même jour.
  - Génération synthétique d'événements master data avec ground truth `bec_iban_swap`,
    `dormant_reactivation`.
  - Page Streamlit `🏦 Master data history` avec timeline + diff coloré.
- Sprint 2 — Sanctions / PEP :
  - Client `sanctions_client` (snapshot CSV embarqué + interface OpenSanctions Yente
    optionnelle), normalisation accents/casse, scoring nominatif RapidFuzz.
  - Détecteur `sanctions` : flag `vendor_sanctioned` (CRITICAL) et `vendor_pep` (HIGH).
  - Page Streamlit `⚖️ Sanctions PEP`.
- Sprint 3 — Case management v0 :
  - Modèles `Case`, `CaseEvent`, statuts (NEW → CLOSED_*).
  - Audit log immutable chaîné par hash SHA-256 (vérification d'intégrité).
  - Service `cases.service` avec garde-fous (clôture motivée obligatoire,
    pas de modification post-clôture).
  - Page Streamlit `🗂️ File d'investigation` + `📜 Audit trail`.

### Modifié
- README repositionné « Vendor & Payment Integrity FR-native ».
- `streamlit_app.py` : landing repositionnée, retrait de la mention « MindBridge ».
- `weights.yaml` : `benford = 0.0` par défaut, commentaire explicatif.
- `risk_engine.py` : filtre les findings `benford` avant agrégation si poids = 0.
- Page `2_🔢_Benford.py` renommée logiquement « Scoping orienté risque » (titre interne).

### Déprécié
- Le finding direct produit par Benford n'est plus pris en compte dans le score
  consolidé par défaut. La compatibilité est préservée via override explicite.
