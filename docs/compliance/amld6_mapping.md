# AMLD6 — Mapping de conformité P2P Fraud Detective FR

**Référence** : Directive (UE) 2018/1673 du Parlement européen et du Conseil du 23 octobre 2018
visant à lutter contre le blanchiment de capitaux au moyen du droit pénal (6e directive AML).
**Transposition française** : Ordonnance n°2020-115 du 12 février 2020, articles L. 561-1 et s. du CMF.

**Date de mise à jour** : mai 2026  
**Version du produit** : 0.3.0  
**Statut** : Couverture partielle — démonstrateur (non opérationnel)

---

## 1. Périmètre d'application

P2P Fraud Detective FR est un **outil de contrôle interne P2P** destiné à identifier des signaux
de fraude et de blanchiment dans le cycle Achats-Comptabilité. Il n'est pas un système de conformité
LCB-FT au sens de l'art. L. 561-2 CMF (assujettis), mais un **outil d'aide à la décision** pour :
- les fonctions d'audit interne (IA, CAC, IGF, CRC) ;
- les fonctions compliance et RCCI ;
- les directions financières d'ETI soumises à Sapin 2 art. 17.

---

## 2. Tableau de couverture AMLD6

| Article AMLD6 | Titre | Obligation | Détecteur P2P | Statut | Gap |
|---|---|---|---|---|---|
| Art. 3 — Définitions | Infractions sous-jacentes | Identification des 22 infractions prédicats | Sanctions & PEP (OFAC, UE, Trésor FR) | ✅ Partiel | Infractions prédicats hors listes officielles non couvertes |
| Art. 6 — Complicité | Extension responsabilité | Due diligence accrue sur tiers | DECP/RBE (is_opaque_structure) | ✅ Partiel | Pas d'évaluation de la complicité effective |
| Art. 18 — EDD | Vigilance renforcée | Mesures vis-à-vis des PEP, clients/fournisseurs à risque élevé, pays tiers | Sanctions PEP (seuil ≥ 90), DECP/RBE (RBE_BENEFICIAL_OWNER_MATCH) | ✅ Partiel | PEP liste ouverte limitée ; pas d'intégration live Tracfin |
| Art. 19 — UBO | Bénéficiaires effectifs | Identification ≥ 25 % du capital | DECP/RBE (RBEClient, RBE_BENEFICIAL_OWNER_MATCH) | ✅ Partiel | Données RBE synthétiques en mode démo ; INPI API non intégrée |
| Art. 20 — Risque IBAN | Changement domiciliation | Détection modifications IBAN suspectes | Master data (IBAN_CHANGE_NO_PO, BEC_IBAN_CHANGE_PROXIMITY) | ✅ Couvert | — |
| Art. 23 — Gel avoirs | Mesures de gel | Vérification listes gel avoirs UE et Trésor FR | Sanctions (SANCTIONS_VENDOR_HIT, severity=CRITICAL) | ✅ Couvert | — |
| Art. 24 — DSO Tracfin | Déclaration de soupçon | Brouillon DSO pour RCCI / Compliance | LLM narrative (ISA 240) — brouillon manuel | ✅ Partiel | Pas de transmission automatique via ERMES |
| Art. 29 — Formation | Sensibilisation AML | Traçabilité des contrôles | Audit log SHA-256 (file.imported, case.closed) | ✅ Couvert | — |
| Art. 30 — UBO public | Registre public | Consultation registre RBE | RBEClient (demo_mode / live) | ✅ Partiel | Intégration INPI API requise pour le live |

---

## 3. Procédure de déclaration de soupçon (DSO) — aide-mémoire

Lorsqu'un finding CRITICAL est émis sur un fournisseur (SANCTIONS_VENDOR_HIT, RBE_BENEFICIAL_OWNER_MATCH) :

1. **Exporter le rapport de findings** via `pages/11_📊_Synthèse_export.py` (Excel/PDF).
2. **Valider le finding** avec le RCCI ou le Responsable Conformité.
3. **Bloquer le paiement** en attente de diligence renforcée.
4. **Rédiger la DSO** sur le portail **ERMES** de Tracfin (art. L. 561-15 CMF).
   - Rubrique : `Blanchiment de capitaux — cycle Achats-Fournisseurs`
   - Pièces jointes : export findings + audit trail SHA-256
5. **Journaliser la décision** dans la Piste d'audit (`pages/13_📜_Audit_trail.py`).
6. **Conserver les preuves** 5 ans (art. L. 561-12 CMF).

---

## 4. Limites et recommandations

| Limite | Recommandation |
|---|---|
| Données RBE synthétiques en démo | Intégrer l'API INPI (data.inpi.fr/rne/rbe) en production |
| Listes PEP limitées | Enrichir via OpenSanctions Yente (CC-BY 4.0) ou Refinitiv WC |
| Pas de transmission automatique Tracfin | Construire un connecteur ERMES REST (OAuth2) |
| Mono-session Streamlit | Déployer avec backend PostgreSQL pour les équipes > 1 personne |
| Pas de monitoring continu | Ajouter un scheduler APScheduler (PR P3-6) |

---

## 5. Références réglementaires

- **Directive (UE) 2018/1673** (AMLD6) — JOUE L 284/22
- **Ordonnance n°2020-115** du 12 février 2020 (transposition AMLD5/6)
- **Code Monétaire et Financier** — articles L. 561-1 à L. 561-50
- **GAFI / FATF** — 40 recommandations (2012, révisées 2023)
- **EBA Guidelines** — ML/TF risk factors (EBA/GL/2021/02)
- **ACPR** — lignes directrices conjointes LCB-FT (janvier 2020)

---

*Document généré automatiquement — à compléter par le RCCI de l'organisation déployante.*
