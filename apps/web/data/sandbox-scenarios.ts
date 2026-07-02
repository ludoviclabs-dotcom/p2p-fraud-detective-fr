// Catalogue de scénarios sandbox pré-chargés (offline-first).
//
// Objectif : faire tourner la démo `/sandbox` SANS backend ni clé Claude. Chaque
// scénario porte un `narrative` statique riche (même forme que la sortie IA
// `ScenarioNarrative`) pour que le panneau « Narratif du scénario » s'affiche
// hors-ligne ; l'appel Claude ne reste qu'un fallback pour les scénarios backend
// purs (cf. ScenarioNarrativePanel + sandbox/page.tsx).
//
// Données 100 % fictives mais plausibles (SIREN 9 chiffres, IBAN factices,
// montants/dates ~2026). Les `detectors` utilisent les IDs réels résolus par
// DETECTOR_TO_PAGE (sandbox/page.tsx) → les liens « Explorer /{page} » du parcours
// pointent vers des routes existantes. 10 typologies sur 3 secteurs :
// collectivités publiques · industrie manufacturière · services professionnels.

import type { Schemas } from "@p2pfd/shared-types";
import type { ScenarioNarrative } from "@/lib/api-client";

type ScenarioMeta = Schemas["ScenarioMeta"];

/** Métadonnées de scénario (forme backend) enrichies d'un narratif statique. */
export interface SandboxScenario extends ScenarioMeta {
  narrative: ScenarioNarrative;
}

export const SANDBOX_SCENARIOS: SandboxScenario[] = [
  // ── 1 · BEC / détournement d'IBAN — industrie manufacturière ──────────────
  {
    name: "bec_iban_swap",
    title: "BEC — détournement d'IBAN fournisseur",
    pillar: "Business Email Compromise",
    severity: "CRITICAL",
    short: "Un fournisseur légitime voit son IBAN modifié 48 h avant un règlement.",
    target_vendor: "V00007",
    detectors: ["master_data_changes", "score_explorer"],
    storyline:
      "Le fournisseur Aciers Nord-Est SAS (V00007, SIREN 812 446 901, référencé depuis 18 mois) " +
      "est habituellement réglé vers l'IBAN FR76…4521. Le 12 mars 2026, un email usurpant le " +
      "commercial habituel demande la mise à jour du RIB vers FR76…9988, domicilié hors de la zone " +
      "bancaire usuelle. Le détecteur master_data_changes flagge une modification non précédée d'un " +
      "workflow 4-eyes, corrélée 48 h plus tard à un règlement de 47 800 €. Le score consolidé atteint " +
      "92/100 (CRITIQUE) et l'alerte est routée au CAC avant exécution du paiement.",
    narrative: {
      pitch:
        "Fraude au faux fournisseur : le RIB d'un partenaire de confiance est détourné par email, " +
        "puis un règlement de 47 800 € part vers le nouveau compte avant toute contre-vérification.",
      fraud_story: [
        { text: "Le RIB de V00007 est modifié le 12/03 sans contre-signature 4-eyes obligatoire au-delà de 25 000 € d'exposition.", source_ids: ["MDM-2291", "POL-4EYES"] },
        { text: "La demande provient d'un domaine sosie (aciers-nordest-fr.co) au lieu du domaine vérifié du fournisseur.", source_ids: ["EML-IN-8841"] },
        { text: "Le nouvel IBAN FR76…9988 n'a aucun historique de règlement et appartient à un établissement hors zone SEPA habituelle du tiers.", source_ids: ["IBAN-NEW-9988"] },
        { text: "Un règlement de 47 800 € est ordonné 48 h après le changement, fenêtre typique des compromissions BEC.", source_ids: ["RGL-47829"] },
      ],
      expected_detectors: ["master_data_changes", "score_explorer"],
      false_positive_traps: [
        "Un changement de banque légitime existe — mais il est normalement contre-signé et notifié par le canal fournisseur vérifié.",
        "Un domaine proche n'est pas toujours malveillant : vérifier l'enregistrement WHOIS et la date de création.",
      ],
      human_review_required: true,
    },
  },

  // ── 2 · Fractionnement / structuring — collectivités publiques ────────────
  {
    name: "structuring_cosi",
    title: "Fractionnement sous seuils COSI",
    pillar: "Structuring / COSI",
    severity: "HIGH",
    short: "Multiples factures juste sous les seuils de délégation 5 000 € et 10 000 €.",
    target_vendor: null,
    detectors: ["under_thresholds", "score_explorer"],
    storyline:
      "Sur la commande publique de voirie de la commune, le prestataire BTP Voirie Municipale SARL " +
      "(SIREN 311 998 220) émet 12 factures comprises entre 4 760 € et 4 990 € sur 14 jours, juste sous " +
      "le seuil de délégation de 5 000 € qui déclencherait une seconde validation. Le détecteur " +
      "under_thresholds repère une densité anormale dans la fenêtre [seuil−ε, seuil[ (+820 % vs base), " +
      "avec le même approbateur sur 11 des 12 pièces. Aucun marché formalisé n'est rattaché. Le score " +
      "atteint 81/100 (HIGH) : signal de contournement de contrôle interne, à instruire.",
    narrative: {
      pitch:
        "Un prestataire de collectivité saucissonne une dépense en douze factures calibrées juste sous " +
        "le seuil de délégation, pour éviter la double validation et l'appel d'offres.",
      fraud_story: [
        { text: "12 factures dans [4 760 € ; 4 990 €] émises sur 14 jours, toutes sous le seuil de délégation de 5 000 €.", source_ids: ["THR-COSI-5K"] },
        { text: "Pic de +820 % du volume hebdomadaire par rapport à la ligne de base du fournisseur.", source_ids: ["BASE-14J"] },
        { text: "Même approbateur (USER-LDU221) sur 11 des 12 pièces — concentration anormale de la validation.", source_ids: ["APPR-LDU221"] },
        { text: "Aucun marché ni bon de commande cadre n'est rattaché à ces règlements directs.", source_ids: ["PO-ABSENT"] },
      ],
      expected_detectors: ["under_thresholds", "score_explorer"],
      false_positive_traps: [
        "Des petits travaux récurrents peuvent légitimement rester sous le seuil — corroborer avec les bons de livraison distincts.",
        "Un pic d'activité saisonnier (voirie au printemps) peut expliquer le volume sans intention de contournement.",
      ],
      human_review_required: true,
    },
  },

  // ── 3 · Doublons fournisseurs — services professionnels ───────────────────
  {
    name: "supplier_duplicates",
    title: "Doublons fournisseurs (fuzzy + IBAN partagé)",
    pillar: "Doublons fournisseurs",
    severity: "MEDIUM",
    short: "Un même prestataire référencé sous deux noms proches partageant un IBAN.",
    target_vendor: "V01188",
    detectors: ["duplicates", "master_data_changes"],
    storyline:
      "Le cabinet Conseil Audit & Cie est référencé deux fois : « Conseil Audit & Cie » (V01188) et " +
      "« Conseil-Audit et Compagnie » (V01207), noms à distance de Levenshtein faible mais SIREN " +
      "identique 443 109 887. Les deux fiches partagent l'IBAN FR76…6741. Le détecteur duplicates " +
      "rapproche deux factures de 8 920 € à ± 0,01 € émises à 31 h d'écart, avec le même numéro de bon " +
      "de livraison. Risque de double paiement de la même prestation — score 64/100 (MEDIUM).",
    narrative: {
      pitch:
        "La même prestation de conseil est facturée deux fois via deux fiches fournisseurs quasi " +
        "identiques partageant le même IBAN — un classique du double règlement.",
      fraud_story: [
        { text: "Deux fiches (V01188, V01207) avec un SIREN identique (443 109 887) et des raisons sociales à distance fuzzy faible.", source_ids: ["DUP-FUZZY-12"] },
        { text: "IBAN FR76…6741 partagé entre les deux fiches — indice fort de doublon plutôt que d'entités distinctes.", source_ids: ["IBAN-SHARED"] },
        { text: "Deux factures de 8 920 € à ± 0,01 € émises à 31 h d'intervalle.", source_ids: ["INV-8920-A", "INV-8920-B"] },
        { text: "Même numéro de bon de livraison BL-CA-2841 référencé sur les deux pièces.", source_ids: ["BL-CA-2841"] },
      ],
      expected_detectors: ["duplicates", "master_data_changes"],
      false_positive_traps: [
        "Un acompte puis un solde peuvent légitimement porter des montants proches — vérifier les mentions « acompte »/« solde ».",
        "Deux établissements d'un même groupe peuvent partager un compte de trésorerie centralisé.",
      ],
      human_review_required: true,
    },
  },

  // ── 4 · Anneau de fraude (IBAN partagés) — industrie manufacturière ───────
  {
    name: "fraud_ring_iban",
    title: "Anneau de fraude — IBAN partagés",
    pillar: "Anneau de fraude",
    severity: "CRITICAL",
    short: "5 fournisseurs distincts partagent 3 IBAN par paires — graphe cyclique.",
    target_vendor: null,
    detectors: ["network_rings", "shell_companies"],
    storyline:
      "Cinq fournisseurs de pièces industrielles apparemment indépendants (V05112, V05119, V05123, " +
      "V05130, V05144) partagent trois IBAN par paires, formant un graphe cyclique détecté par " +
      "network_rings (cluster_risk 0,91). Trois d'entre eux ont été créés à moins de 30 jours " +
      "d'intervalle, sans site web ni effectif déclaré (signal shell_companies). L'exposition cumulée " +
      "atteint 1,24 M€ sur le trimestre. La topologie en anneau — bénéficiaires qui se reversent " +
      "entre eux — est caractéristique d'un réseau de mules, score 95/100 (CRITIQUE).",
    narrative: {
      pitch:
        "Cinq « fournisseurs » qui se partagent trois comptes en cercle : un anneau de sociétés écrans " +
        "qui recyclent 1,24 M€ de règlements entre eux.",
      fraud_story: [
        { text: "5 fournisseurs distincts mais reliés par 3 IBAN partagés deux à deux — le graphe forme un cycle.", source_ids: ["RING-CL-07", "GRAPH-CYCLE"] },
        { text: "Score de risque du cluster 0,91 calculé par network_rings sur la composante connexe.", source_ids: ["NET-091"] },
        { text: "3 des 5 entités créées à < 30 jours d'écart, sans site web ni effectif (sociétés écrans).", source_ids: ["SHELL-3", "AGE-30J"] },
        { text: "Exposition cumulée de 1,24 M€ sur le trimestre concentrée sur ces comptes.", source_ids: ["EXP-124M"] },
      ],
      expected_detectors: ["network_rings", "shell_companies"],
      false_positive_traps: [
        "Des filiales d'un même groupe peuvent légitimement partager une centrale de paiement — vérifier le RBE.",
        "Un IBAN partagé peut refléter un mandataire de facturation commun (affacturage) plutôt qu'une collusion.",
      ],
      human_review_required: true,
    },
  },

  // ── 5 · Sanctions / PEP — services professionnels ─────────────────────────
  {
    name: "sanctions_pep",
    title: "Fournisseur sous sanctions / PEP",
    pillar: "Sanctions & PEP",
    severity: "CRITICAL",
    short: "Raison sociale matchant une liste de sanctions, IBAN hors juridiction.",
    target_vendor: "V02041",
    detectors: ["sanctions", "pep"],
    storyline:
      "Le prestataire d'intermédiation Global Intermediary Ltd (V02041), sans SIREN français, " +
      "présente un IBAN chypriote CY17…0276 et un bénéficiaire effectif matchant à 97 % la liste " +
      "OFAC SDN (fuzzy match « Ratchenko I. »). Le détecteur sanctions lève un hit OFAC, pep confirme " +
      "une exposition politiquement exposée secondaire (liste Trésor FR 2025-Q4). Première facture, " +
      "paiement immédiat demandé. Score 96/100 (CRITIQUE) : blocage recommandé avant tout virement, " +
      "obligation LCB-FT de déclaration.",
    narrative: {
      pitch:
        "Un intermédiaire offshore dont le bénéficiaire effectif figure sur la liste OFAC SDN demande " +
        "un premier paiement immédiat vers un compte chypriote — risque LCB-FT majeur.",
      fraud_story: [
        { text: "Match fuzzy 97 % du bénéficiaire effectif avec une entrée OFAC SDN (« Ratchenko I. »).", source_ids: ["OFAC-SDN-97"] },
        { text: "Exposition PEP secondaire confirmée sur la liste Trésor FR 2025-Q4.", source_ids: ["PEP-TRESOR-Q4"] },
        { text: "Aucun identifiant français (SIREN absent), juridiction CY hors zone habituelle.", source_ids: ["SIREN-ABSENT", "IBAN-CY-0276"] },
        { text: "Première facture avec paiement immédiat (Net 0) demandé — pression opérationnelle inhabituelle.", source_ids: ["NET-0"] },
      ],
      expected_detectors: ["sanctions", "pep"],
      false_positive_traps: [
        "Un homonyme peut générer un faux match — exiger une vérification de la date de naissance / pays avant blocage définitif.",
        "Une PEP n'est pas interdite de transaction : c'est le défaut de vigilance renforcée qui constitue le risque.",
      ],
      human_review_required: true,
    },
  },

  // ── 6 · Faux fournisseur (SIREN absent) — collectivités publiques ─────────
  {
    name: "shell_supplier",
    title: "Faux fournisseur — SIREN absent",
    pillar: "Société écran",
    severity: "HIGH",
    short: "Fournisseur sans identifiant FR vérifiable, créé juste avant la 1re facture.",
    target_vendor: "V03110",
    detectors: ["shell_companies", "ghost_vendor", "score_explorer"],
    storyline:
      "Pour un marché de fournitures, la collectivité référence Eurotech Supplies Ltd (V03110), dont le " +
      "SIREN déclaré est introuvable au répertoire Sirene et dont l'adresse renvoie à une boîte postale " +
      "lituanienne (IBAN LT12…1000). Le détecteur shell_companies relève une entité créée 9 jours avant " +
      "la première facture, sans effectif, site web parqué. Le cross-check Sirene échoue (coverage 0). " +
      "Montant 63 400 €, score 84/100 (HIGH) : suspicion de société écran montée pour capter un paiement.",
    narrative: {
      pitch:
        "Une « société » sans existence vérifiable au registre, créée neuf jours avant d'émettre une " +
        "facture de 63 400 € vers un compte balte : le profil type de la société écran.",
      fraud_story: [
        { text: "SIREN déclaré introuvable au répertoire Sirene (cross-check Sirene en échec, coverage 0).", source_ids: ["SIRENE-MISS"] },
        { text: "Entité créée 9 jours avant la première facture, sans effectif ni site web actif.", source_ids: ["AGE-9J", "SHELL-WEB"] },
        { text: "Adresse en boîte postale et IBAN LT12…1000 hors juridiction de la collectivité.", source_ids: ["IBAN-LT-1000"] },
        { text: "Première facture de 63 400 €, sans antériorité commerciale.", source_ids: ["INV-63400"] },
      ],
      expected_detectors: ["shell_companies", "ghost_vendor", "score_explorer"],
      false_positive_traps: [
        "Une entreprise étrangère légitime peut ne pas avoir de SIREN — vérifier un identifiant équivalent (VAT intra-UE).",
        "Une jeune société n'est pas frauduleuse en soi : corroborer avec des références client et un site actif.",
      ],
      human_review_required: true,
    },
  },

  // ── 7 · Première facture à paiement immédiat — industrie manufacturière ───
  {
    name: "first_invoice_instant",
    title: "1re facture · paiement immédiat",
    pillar: "Comportement inhabituel",
    severity: "MEDIUM",
    short: "Premier règlement d'un nouveau bénéficiaire en virement instantané, Net 0.",
    target_vendor: "V03377",
    detectors: ["score_explorer", "master_data_changes"],
    storyline:
      "Composants Précision SARL (V03377, SIREN 522 740 118) est un nouveau fournisseur dont la toute " +
      "première facture, de 21 300 €, est demandée en virement instantané à échéance Net 0 — alors que " +
      "les conditions standard du portefeuille sont à 30 jours. Le bénéficiaire a été ajouté la veille. " +
      "score_explorer relève une déviation du profil de paiement (montant + immédiateté), " +
      "master_data_changes confirme un bénéficiaire ajouté < 24 h. Score 58/100 (MEDIUM) : à vérifier, " +
      "signal faible mais combinaison inhabituelle (nouveau tiers + instantané).",
    narrative: {
      pitch:
        "Un fournisseur tout neuf réclame son premier paiement en instantané, échéance immédiate : " +
        "ni frauduleux ni anodin, c'est la combinaison qui mérite une vérification.",
      fraud_story: [
        { text: "Première facture du tiers (21 300 €) demandée en virement instantané, échéance Net 0.", source_ids: ["INV-21300", "NET-0"] },
        { text: "Bénéficiaire ajouté < 24 h avant l'ordre de paiement.", source_ids: ["BEN-24H"] },
        { text: "Conditions standard du portefeuille à 30 jours — l'immédiateté demandée s'écarte du profil.", source_ids: ["TERMS-30J"] },
        { text: "Déviation de score modérée : signal faible mais combinaison atypique (nouveau tiers + instantané + Net 0).", source_ids: ["SCORE-58"] },
      ],
      expected_detectors: ["score_explorer", "master_data_changes"],
      false_positive_traps: [
        "Un escompte pour paiement comptant peut légitimement motiver un Net 0 — vérifier la mention sur la facture.",
        "Un nouveau fournisseur stratégique peut négocier des conditions dérogatoires validées par les achats.",
      ],
      human_review_required: true,
    },
  },

  // ── 8 · Modification RIB non contre-signée — collectivités publiques ──────
  {
    name: "rib_change_unsigned",
    title: "Modification de RIB non contre-signée",
    pillar: "Master data",
    severity: "HIGH",
    short: "Changement d'IBAN fournisseur sans validateur (4-eyes absent).",
    target_vendor: "V01902",
    detectors: ["master_data_changes"],
    storyline:
      "Sur le fournisseur d'exploitation Gestion Eau Métropole (V01902, SIREN 379 201 446), un agent " +
      "modifie l'IBAN dans la base tiers sans le workflow de double validation requis au-delà de " +
      "10 000 € d'exposition. Le détecteur master_data_changes enregistre un diff IBAN non précédé " +
      "d'une contre-signature (4-eyes breach), horodaté hors heures ouvrées. Aucun règlement n'a encore " +
      "été émis vers le nouveau compte. Score 79/100 (HIGH) : violation de contrôle interne à corriger " +
      "avant le prochain cycle de paiement, indépendamment de toute intention frauduleuse.",
    narrative: {
      pitch:
        "Un IBAN fournisseur est changé en base sans la double validation obligatoire : même sans " +
        "fraude avérée, c'est une brèche de contrôle interne à refermer avant le prochain paiement.",
      fraud_story: [
        { text: "Diff IBAN enregistré sur V01902 sans contre-signature 4-eyes requise au-delà de 10 000 €.", source_ids: ["MDM-1902", "POL-4EYES"] },
        { text: "Modification horodatée hors heures ouvrées (02 h 14), profil d'accès atypique.", source_ids: ["TS-0214"] },
        { text: "Aucun règlement encore émis vers le nouveau compte — fenêtre d'interception ouverte.", source_ids: ["RGL-NONE"] },
        { text: "Le contrôle interne ISA 240 impose la séparation des tâches sur la donnée bancaire de référence.", source_ids: ["ISA-240"] },
      ],
      expected_detectors: ["master_data_changes"],
      false_positive_traps: [
        "Une correction d'erreur de saisie peut expliquer le diff — exiger la pièce justificative bancaire.",
        "Un horodatage nocturne peut venir d'un batch d'import automatisé légitime.",
      ],
      human_review_required: true,
    },
  },

  // ── 9 · Anomalie ML (déviation comportementale) — industrie manufacturière ─
  {
    name: "ml_behaviour_drift",
    title: "Anomalie ML — déviation comportementale",
    pillar: "Anomalie ML",
    severity: "MEDIUM",
    short: "Score d'isolation élevé : profil de règlement hors distribution habituelle.",
    target_vendor: "V04120",
    detectors: ["score_explorer", "benford"],
    storyline:
      "Le transporteur Logistique Transeuro SAS (V04120, SIREN 451 882 330) présente sur le mois un " +
      "profil de règlements s'écartant fortement de sa distribution historique : fréquence, montants " +
      "ronds et jours d'émission atypiques. Le pipeline Isolation Forest renvoie un score d'anomalie " +
      "élevé (0,86) et l'analyse de Benford signale une sur-représentation des premiers chiffres 4 et 7 " +
      "sur les montants. Aucune règle déterministe unique n'est violée, mais le faisceau ML justifie une " +
      "revue. Score 61/100 (MEDIUM) : anomalie statistique à corroborer.",
    narrative: {
      pitch:
        "Aucune règle franche n'est cassée, mais le comportement de facturation du transporteur sort de " +
        "sa propre distribution : c'est le modèle ML qui lève la main.",
      fraud_story: [
        { text: "Score d'anomalie Isolation Forest de 0,86 sur le profil mensuel de règlements du tiers.", source_ids: ["IFOREST-086"] },
        { text: "Distribution de Benford anormale : sur-représentation des premiers chiffres 4 et 7.", source_ids: ["BENFORD-47"] },
        { text: "Montants ronds et jours d'émission atypiques vs la ligne de base historique du fournisseur.", source_ids: ["DRIFT-BASE"] },
        { text: "Aucune règle déterministe isolée n'est violée — le signal est la combinaison statistique.", source_ids: ["RULE-NONE"] },
      ],
      expected_detectors: ["score_explorer", "benford"],
      false_positive_traps: [
        "Un changement légitime d'activité (nouveau contrat) déplace naturellement la distribution.",
        "Benford est peu fiable sur de faibles volumes — vérifier la taille d'échantillon avant de conclure.",
      ],
      human_review_required: true,
    },
  },

  // ── 10 · Collusion interne — services professionnels ──────────────────────
  {
    name: "internal_collusion",
    title: "Collusion interne — approbateur lié au bénéficiaire",
    pillar: "Collusion interne",
    severity: "CRITICAL",
    short: "L'approbateur du paiement est relié au bénéficiaire dans le graphe.",
    target_vendor: "V02890",
    detectors: ["network_rings", "conflicts_of_interest", "master_data_changes"],
    storyline:
      "Le cabinet Prestaconseil RH (V02890, SIREN 489 330 715) est créé puis référencé, et ses factures " +
      "sont systématiquement validées par le même approbateur interne (USER-VAL-204). Le détecteur " +
      "network_rings établit un lien entre cet approbateur et le bénéficiaire effectif (adresse et " +
      "compte communs), tandis que master_data_changes montre que l'approbateur a lui-même créé la " +
      "fiche fournisseur — rompant la séparation des tâches. 14 règlements pour 92 700 € sur 6 mois. " +
      "Score 93/100 (CRITIQUE) : faisceau de collusion interne, escalade compliance immédiate.",
    narrative: {
      pitch:
        "L'agent qui valide les paiements a créé le fournisseur et partage une adresse avec son " +
        "bénéficiaire : séparation des tâches rompue, faisceau de conflit d'intérêts.",
      fraud_story: [
        { text: "L'approbateur USER-VAL-204 a lui-même créé la fiche fournisseur V02890 (séparation des tâches rompue).", source_ids: ["MDM-2890", "SOD-BREAK"] },
        { text: "network_rings relie l'approbateur et le bénéficiaire effectif via une adresse et un compte communs.", source_ids: ["RING-INT-04"] },
        { text: "100 % des 14 règlements (92 700 €) validés par ce même approbateur sur 6 mois.", source_ids: ["APPR-204-14"] },
        { text: "Absence de mise en concurrence et de pièces de réception pour des prestations immatérielles.", source_ids: ["RECEPT-NONE"] },
      ],
      expected_detectors: ["network_rings", "conflicts_of_interest", "master_data_changes"],
      false_positive_traps: [
        "Une homonymie d'adresse (immeuble de bureaux partagé) peut créer un faux lien de graphe.",
        "Dans une petite structure, un même valideur peut légitimement couvrir un périmètre — vérifier la délégation formelle.",
      ],
      human_review_required: true,
    },
  },
];

/** Narratif statique d'un scénario pré-chargé (sinon `undefined` → fallback IA). */
export function getSandboxNarrative(name: string): ScenarioNarrative | undefined {
  return SANDBOX_SCENARIOS.find((s) => s.name === name)?.narrative;
}

/**
 * Fusionne le catalogue local (toujours présent) avec les scénarios renvoyés par
 * le backend, dé-dupés par `name` (le local est prioritaire). Garantit que la
 * sandbox affiche les 10 typologies même hors-ligne, tout en exposant d'éventuels
 * scénarios backend supplémentaires lorsqu'il répond.
 */
export function mergeSandboxScenarios(api?: ScenarioMeta[] | null): ScenarioMeta[] {
  const local: ScenarioMeta[] = SANDBOX_SCENARIOS;
  if (!api || api.length === 0) return local;
  const localNames = new Set(SANDBOX_SCENARIOS.map((s) => s.name));
  const extras = api.filter((s) => !localNames.has(s.name));
  return [...local, ...extras];
}
