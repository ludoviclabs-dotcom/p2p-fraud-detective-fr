# Model Card — risk-engine-demo-v1

## Objectif

`risk-engine-demo-v1` est un moteur de scoring déterministe et explicable pour
scénarios synthétiques de fraude P2P, SEPA, instant payment et Procure-to-Pay.

## Entrées

Le moteur utilise uniquement des données synthétiques :

- transaction, montant, rail et canal ;
- bénéficiaire, IBAN masqué ou fictif, historique simulé ;
- narration textuelle ;
- signaux device/session non intrusifs simulés ;
- payload QR textuel ;
- graphe synthétique ;
- signaux sanctions/PEP mockés.

## Sorties

- score borné entre 0 et 100 ;
- niveau `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` ;
- décision recommandée `ALLOW`, `MONITOR`, `MANUAL_REVIEW`,
  `BLOCK_RECOMMENDED` ;
- typologie probable ;
- reason codes explicables ;
- actions recommandées.

## Détecteurs

- Beneficiary / IBAN Trust Check
- APP Fraud & Scam Narrative Detector
- Velocity Checks
- Device & Session Risk Lite
- QR Code Fraud Analyzer
- Mule Account / Fraud Graph
- Document / RIB / Invoice Fraud Check
- Sanctions / PEP / AML Screening

## Limites

Le moteur n'est pas production-grade. Il ne remplace pas une revue humaine, ne
fait pas de fingerprinting réel, ne fait pas de dark web scraping et ne fournit
pas de certification réglementaire.

## Gouvernance de démonstration

- Version du moteur : `risk-engine-demo-v1`.
- Données : synthétiques, locales ou chargées côté serveur depuis Hugging Face.
- Décision : recommandation de revue uniquement, décision finale humaine.
- Export : evidence pack JSON/HTML pour documenter le raisonnement, pas pour
  exécuter un vrai blocage bancaire.
- Qualité minimale : score borné 0-100, scénarios critiques attendus,
  reason codes explicables, route de case et export vérifiés.
