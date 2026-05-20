# Typologies Fraude FR/EU

Le Workbench couvre les typologies synthétiques suivantes :

- Faux conseiller bancaire : manipulation APP, urgence, compte sécurisé,
  nouveau bénéficiaire et virement instantané.
- Changement RIB fournisseur : demande de modification IBAN, facture ou RIB
  incohérent, contrôle 4-eyes.
- QR code falsifié : payload URL suspect, IBAN extrait divergent, domaine
  proche du domaine attendu.
- Mule account network : compte relais, payeurs multiples, IBAN ou appareil
  partagé, cluster graphe.
- Romance / investment scam : pression émotionnelle, crypto, promesse de
  rendement, urgence.
- Sanctions / PEP / fournisseur sensible : match synthétique AML, pays sensible,
  escalade conformité.

Ces typologies servent uniquement à la démonstration et à la documentation d'un
processus d'investigation. Elles ne constituent pas un avis réglementaire.

## Parcours de test attendu

Chaque typologie doit pouvoir être testée dans `/p2p-scenarios`, expliquée dans
`/detection-studio`, investiguée dans `/fraud-case-360/[caseId]` et documentée
via l'evidence pack. Les actions analyste restent simulées et ne déclenchent
aucun vrai flux bancaire.
