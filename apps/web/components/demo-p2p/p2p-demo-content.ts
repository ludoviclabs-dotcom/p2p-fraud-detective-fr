// Contenu bilingue de la demo guidee P2P.
//
// Recit forensic fictif. Le vocabulaire reste prudent : signal, indice,
// anomalie, a qualifier, a instruire, revue humaine.

import type { Locale } from "@/components/locale-provider";
import type { P2PCalloutId, P2PConsoleEventId, P2PDemoScene } from "./p2p-demo-data";

type SceneCopy = {
  label: string;
  title: string;
  body: string;
};

type CalloutCopy = {
  title: string;
  body: string;
};

type AlertCopy = {
  title: string;
  text: string;
  observation: string;
  why: string;
  proof: string;
  action: string;
  badges: string[];
  cta: string;
};

export interface DemoContent {
  launch: { topbar: string; sidebar: string; home: string };
  controls: {
    skip: string;
    skipAria: string;
    replay: string;
    exploreCockpit: string;
    viewScenarios: string;
    exportAnalysis: string;
    demoBadge: string;
  };
  demoNotice: string;
  brief: {
    kicker: string;
    objectiveLabel: string;
    objective: string;
    signalsLabel: string;
    signals: string;
    outputLabel: string;
    output: string;
  };
  cockpit: {
    eyebrow: string;
    title: string;
    subtitle: string;
    searchPlaceholder: string;
    searchHint: string;
    loadingStatus: string;
    kpiTotal: string;
    kpiCritical: string;
    kpiOpen: string;
    kpiSla: string;
    tableTitle: string;
    tableSub: string;
    colVendor: string;
    colExposure: string;
    colFindings: string;
    colSeverity: string;
    colAction: string;
    open360: string;
    priorityEyebrow: string;
    priorityTitle: string;
    priorityBody: string;
    suggestionsTitle: string;
    suggestions: string[];
  };
  case360: {
    eyebrow: string;
    header: string;
    subheader: string;
    gaugeLabel: string;
    reasonCodesTitle: string;
    signalsTitle: string;
    prepareReview: string;
  };
  reasonCodes: Record<string, { label: string; description: string }>;
  evidence: {
    drawerTitle: string;
    drawerSub: string;
    sealed: string;
    typeLabel: string;
    statusLabel: string;
    items: Record<
      string,
      { title: string; type: string; status: string; detail: string }
    >;
  };
  alerts: Record<string, AlertCopy>;
  recommendations: {
    eyebrow: string;
    title: string;
    sub: string;
    actions: string[];
    note: string;
  };
  final: {
    title: string;
    stats: string;
    tagline: string;
    disclaimer: string;
  };
  rail: Record<string, string>;
  sceneLabels: Record<P2PDemoScene, string>;
  sceneCaptions: Record<P2PDemoScene, SceneCopy>;
  consoleEvents: Record<P2PConsoleEventId, string>;
  callouts: Record<P2PCalloutId, CalloutCopy>;
  labels: {
    scene: string;
    sources: string;
    findings: string;
    observation: string;
    why: string;
    proof: string;
    action: string;
    console: string;
  };
  dataLineage: {
    title: string;
    subtitle: string;
    sources: string[];
    output: string;
  };
  scoreBreakdown: {
    title: string;
    subtitle: string;
    illustrative: string;
  };
  microVisuals: {
    ibanTitle: string;
    ibanLabel: string;
    thresholdTitle: string;
    thresholdLabel: string;
    rbeTitle: string;
    rbeInternal: string;
    rbeOfficial: string;
    rbeMismatch: string;
    fourEyesTitle: string;
    fourEyesSteps: string[];
    fourEyesLabel: string;
  };
  investigationMap: {
    title: string;
    steps: string[];
  };
  casePacket: {
    title: string;
    subtitle: string;
    idLabel: string;
    supplierLabel: string;
    scoreLabel: string;
    exposureLabel: string;
    signalsLabel: string;
    evidenceLabel: string;
    statusLabel: string;
    statusValue: string;
    fingerprintLabel: string;
    sealPrimary: string;
    sealSecondary: string;
    exportTitle: string;
    exportSubtitle: string;
    exportMeta: string;
    exportFeatures: string[];
  };
}

const FR: DemoContent = {
  launch: {
    topbar: "Démo guidée 60 s",
    sidebar: "Scénario ALPHACOM",
    home: "Démo guidée",
  },
  controls: {
    skip: "Passer",
    skipAria: "Passer la démonstration",
    replay: "Rejouer la démo",
    exploreCockpit: "Explorer le cockpit",
    viewScenarios: "Voir les scénarios P2P",
    exportAnalysis: "Exporter pour analyse",
    demoBadge: "Données de démonstration fictives",
  },
  demoNotice: "Données de démonstration fictives",
  brief: {
    kicker: "Mission démo - 60 secondes",
    objectiveLabel: "Objectif",
    objective:
      "Identifier pourquoi ALPHACOM SERVICES declenche un risque prioritaire 92/100.",
    signalsLabel: "Signaux attendus",
    signals:
      "IBAN partage - fractionnement sous seuil - rupture 4-eyes - incoherence RBE.",
    outputLabel: "Sortie attendue",
    output: "Dossier fournisseur 360 + piste d'audit + parcours recommande.",
  },
  cockpit: {
    eyebrow: "Cockpit P2P - vue consolidee",
    title: "Cockpit risque P2P",
    subtitle:
      "Vue consolidee des risques fournisseurs, triee par exposition financiere et prete pour la decision audit.",
    searchPlaceholder: "Rechercher un SIREN, fournisseur, IBAN, case ou alerte...",
    searchHint: "Recherche fournisseur - referentiel P2P - signaux audit",
    loadingStatus:
      "Interrogation referentiel fournisseur - ecritures P2P - audit log - RBE - signaux internes...",
    kpiTotal: "Exposition totale",
    kpiCritical: "Exposition critique",
    kpiOpen: "Cases ouverts",
    kpiSla: "Retards SLA",
    tableTitle: "Top fournisseurs par exposition",
    tableSub: "Le tri favorise l'impact financier, pas seulement le score brut.",
    colVendor: "Fournisseur",
    colExposure: "Exposition",
    colFindings: "Findings",
    colSeverity: "Severite",
    colAction: "Action",
    open360: "Ouvrir 360",
    priorityEyebrow: "Priorite du jour",
    priorityTitle: "Reduire l'exposition critique",
    priorityBody:
      "Traiter d'abord les fournisseurs a criticite maximale avec retard SLA ou absence d'assignation. Chaque case doit produire une preuve exploitable.",
    suggestionsTitle: "Suggestions",
    suggestions: [
      "V00474 - ALPHACOM SERVICES - fournisseur prioritaire",
      "V00444 - fournisseur surveille",
      "V00343 - exposition elevee",
    ],
  },
  case360: {
    eyebrow: "Fraud Case 360 - donnees de demonstration",
    header: "V00474 - ALPHACOM SERVICES",
    subheader: "Dossier fournisseur 360 - faisceau d'indices a instruire",
    gaugeLabel: "Score de risque",
    reasonCodesTitle: "Reason codes",
    signalsTitle: "Signaux detectes",
    prepareReview: "Preparer revue",
  },
  reasonCodes: {
    IBAN_RING: {
      label: "Anneau IBAN partage",
      description:
        "Meme IBAN detecte sur plusieurs fournisseurs lies au referentiel P2P.",
    },
    THRESHOLD_SPLIT: {
      label: "Fractionnement sous seuil",
      description:
        "Serie de factures rapprochees sous le seuil de validation interne.",
    },
    FOUR_EYES_BREAK: {
      label: "Rupture 4-eyes",
      description:
        "Validation et creation fournisseur rapprochees sur un meme perimetre operationnel.",
    },
    RBE_MISMATCH: {
      label: "Ecart RBE / referentiel",
      description:
        "Ecart entre les informations beneficiaires effectifs et le referentiel fournisseur.",
    },
    SLA_UNASSIGNED: {
      label: "Retard SLA / absence d'assignation",
      description:
        "Case prioritaire sans reviewer assigne dans la fenetre de demonstration.",
    },
  },
  evidence: {
    drawerTitle: "Evidence drawer",
    drawerSub: "Pieces associees au scenario ALPHACOM",
    sealed: "Preuve scellee",
    typeLabel: "Type",
    statusLabel: "Statut",
    items: {
      "ev-iban": {
        title: "IBAN partage",
        type: "Signal bancaire",
        status: "A qualifier",
        detail: "IBAN commun observe entre V00474, V00231 et V00118.",
      },
      "ev-invoice": {
        title: "Factures sous seuil",
        type: "Controle interne",
        status: "A instruire",
        detail: "14 factures entre 4 200 EUR et 4 950 EUR sur 30 jours.",
      },
      "ev-four-eyes": {
        title: "Rupture 4-eyes",
        type: "Gouvernance P2P",
        status: "Revue requise",
        detail:
          "Creation fournisseur et validation rapprochees dans le meme perimetre.",
      },
      "ev-rbe": {
        title: "Ecart RBE / referentiel",
        type: "KYS fournisseur",
        status: "Mise a jour requise",
        detail: "Beneficiaire effectif non aligne avec le referentiel interne.",
      },
      "ev-sla": {
        title: "Absence d'assignation",
        type: "Workflow audit",
        status: "Reviewer requis",
        detail: "Case prioritaire sans assignation dans le parcours de revue.",
      },
    },
  },
  alerts: {
    "iban-ring": {
      title: "Anneau IBAN partage",
      text:
        "Trois fournisseurs de demonstration partagent un meme IBAN de domiciliation. Signal a qualifier dans le cadre des controles anticorruption et du controle interne.",
      observation: "3 fournisseurs de demonstration partagent le meme IBAN.",
      why:
        "Un IBAN reutilise peut indiquer une anomalie fournisseur ou un schema a qualifier.",
      proof: "ev-iban - ed25519:7f3a...91c2",
      action: "Documenter le signal bancaire.",
      badges: ["Signal critique", "Sapin II", "Controle interne"],
      cta: "Documenter le signal",
    },
    threshold: {
      title: "Fractionnement sous seuil",
      text:
        "Serie de 14 factures entre 4 200 EUR et 4 950 EUR sur 30 jours. Le pattern suggere un possible contournement du seuil interne de validation a qualifier avant toute conclusion.",
      observation: "14 factures concentrees sous le seuil interne de 5 000 EUR.",
      why:
        "La repetition sous seuil peut masquer une rupture de controle a instruire.",
      proof: "ev-invoice - ed25519:93ab...4d20",
      action: "Ouvrir les ecritures et assigner une revue.",
      badges: ["Threshold split", "4-eyes", "Revue P2P"],
      cta: "Ouvrir les ecritures",
    },
    rbe: {
      title: "Ecart RBE / referentiel fournisseur",
      text:
        "Les informations beneficiaires effectifs ne sont pas alignees avec le referentiel fournisseur interne. Une mise a jour KYS et une revue documentaire sont recommandees.",
      observation: "Beneficiaire effectif externe different du referentiel interne.",
      why: "Un ecart documentaire doit etre explique avant poursuite du parcours.",
      proof: "ev-rbe - ed25519:b9aa...31e7",
      action: "Demander une mise a jour KYS.",
      badges: ["RBE", "KYS", "Referentiel"],
      cta: "Demander mise a jour",
    },
    concentration: {
      title: "Concentration fournisseur critique",
      text:
        "V00474 concentre une part significative de l'exposition critique du scenario. Si le fournisseur est critique ou TIC, une revue risque tiers renforcee doit etre envisagee.",
      observation: "ALPHACOM porte 4 706 422 EUR d'exposition dans la demo.",
      why:
        "La priorisation combine exposition, signaux et retard de traitement.",
      proof: "ev-sla - ed25519:41f0...72ad",
      action: "Preparer la revue humaine et le parcours d'escalade.",
      badges: ["Risque tiers", "Concentration", "DORA si applicable"],
      cta: "Preparer revue tiers",
    },
  },
  recommendations: {
    eyebrow: "Parcours recommande",
    title: "Dossier prêt pour revue",
    sub: "Preuves scellées - piste d'audit générée",
    actions: [
      "Assigner reviewer",
      "Generer audit trail",
      "Preparer note d'escalade conformite",
    ],
    note: "Aucune declaration automatique. Le dossier prepare les elements pour revue humaine.",
  },
  final: {
    title: "Dossier ALPHACOM prêt pour revue",
    stats: "Signaux priorisés - preuves scellées - piste d'audit générée",
    tagline:
      "Le cockpit ne conclut pas a la fraude : il priorise, documente et prepare la revue humaine.",
    disclaimer:
      "Demonstration fictive. Le cockpit priorise les signaux, documente les preuves et prepare la revue humaine. Il ne conclut pas juridiquement a une fraude.",
  },
  rail: {
    brief: "Brief",
    search: "Recherche",
    cascade: "Cascade",
    case360: "Dossier 360",
    evidence: "Preuves",
    recommendations: "Recommandations",
  },
  sceneLabels: {
    "cold-open": "Alerte prioritaire",
    "command-launch": "Mission",
    "cockpit-wide": "Cockpit",
    "search-zoom": "Recherche fournisseur",
    "data-cascade": "Cascade de signaux",
    "supplier-row": "Priorisation",
    "case-file-open": "Dossier 360",
    "score-breakdown": "Score explicable",
    "evidence-build": "Preuves",
    "alert-sequence": "Findings",
    "review-path": "Revue humaine",
    "export-ready": "Export analyse",
    "final-summary": "Case packet",
  },
  sceneCaptions: {
    "cold-open": {
      label: "Brief",
      title: "Un fournisseur sort du bruit.",
      body: "ALPHACOM remonte en tête : 92/100, 4,7 M EUR exposés et plusieurs signaux à qualifier.",
    },
    "command-launch": {
      label: "Mission",
      title: "On rejoue le raisonnement, pas seulement l'écran.",
      body: "La démo montre comment passer d'une alerte brute à un dossier clair, relisible et assignable.",
    },
    "cockpit-wide": {
      label: "Cockpit",
      title: "Le cockpit donne l'ordre de bataille.",
      body: "Montants, retards et criticité indiquent où l'auditeur doit commencer sa revue.",
    },
    "search-zoom": {
      label: "Recherche",
      title: "Un identifiant suffit pour isoler le sujet.",
      body: "V00474 ouvre le contexte fournisseur, les alertes liées et les preuves déjà disponibles.",
    },
    "data-cascade": {
      label: "Cascade",
      title: "Les sources parlent ensemble.",
      body: "Référentiel, écritures P2P, IBAN, RBE et audit log sont rapprochés avant toute conclusion.",
    },
    "supplier-row": {
      label: "Priorisation",
      title: "La ligne ALPHACOM devient actionnable.",
      body: "Le tri explique pourquoi ce fournisseur passe avant les autres, sans masquer les raisons.",
    },
    "case-file-open": {
      label: "Dossier 360",
      title: "Le dossier 360 donne les pièces du puzzle.",
      body: "Le score n'est utile que s'il montre les signaux, les dates et les preuves associées.",
    },
    "score-breakdown": {
      label: "Score",
      title: "Le 92/100 devient compréhensible.",
      body: "Chaque point fort du score renvoie à une raison lisible et à une pièce de dossier.",
    },
    "evidence-build": {
      label: "Preuves",
      title: "Les indices deviennent des preuves de travail.",
      body: "IBAN, seuil, 4-eyes et RBE sont horodatés, hashés et prêts à être relus.",
    },
    "alert-sequence": {
      label: "Findings",
      title: "Chaque alerte répond à quatre questions.",
      body: "Qu'a-t-on vu ? Pourquoi c'est important ? Quelle preuve ? Quelle action maintenant ?",
    },
    "review-path": {
      label: "Recommandations",
      title: "La suite est simple : assigner, tracer, décider.",
      body: "Le cockpit prépare la revue humaine avec un parcours d'escalade clair et prudent.",
    },
    "export-ready": {
      label: "Export analyse",
      title: "Le dossier est prêt à sortir du cockpit.",
      body: "Un paquet d'analyse est généré : synthèse, preuves, empreintes et prochaine action.",
    },
    "final-summary": {
      label: "Case packet",
      title: "Le dossier ALPHACOM est prêt pour revue.",
      body: "Le document est prêt à être exporté, partagé et relu par un reviewer humain.",
    },
  },
  consoleEvents: {
    init: "[00:01.120] init cockpit_context",
    "load-case": "[00:02.040] load priority_case supplier=V00474",
    "query-supplier": "[00:03.018] query supplier_index id=V00474",
    "fetch-ledger": "[00:06.211] fetch p2p_ledger window=30d",
    "scan-iban": "[00:07.004] scan iban_reuse graph_depth=2",
    "detect-threshold": "[00:08.440] detect threshold_split count=14 limit=5000",
    "compare-rbe": "[00:09.205] compare rbe_snapshot supplier_ref",
    "compute-score": "[00:10.880] compute risk_score -> 92",
    "open-case": "[00:13.012] open vendor_360 case=CASE-P2P-V00474",
    "seal-evidence": "[00:18.416] seal evidence_packet ed25519:7f3a...91c2",
    "prepare-review": "[00:23.100] prepare review_path reviewer_required=true",
    "build-export": "[00:26.420] build analysis_export format=case_packet",
    "packet-ready": "[00:27.000] packet status=ready_for_human_review",
  },
  callouts: {
    "priority-score": {
      title: "Score prioritaire 92/100",
      body: "Ce score dit ou regarder en premier, pas quoi conclure.",
    },
    "global-search": {
      title: "Recherche sans détour",
      body: "Tapez un fournisseur ou un identifiant : le cockpit remonte le dossier utile.",
    },
    "critical-kpi": {
      title: "Exposition critique",
      body: "Le risque financier donne le tempo de revue.",
    },
    "supplier-row": {
      title: "Fournisseur prioritaire",
      body: "ALPHACOM combine montant élevé, signaux multiples et retard de traitement.",
    },
    "data-lineage": {
      title: "Cascade de rapprochement",
      body: "Les données sont rapprochées avant d'être résumées.",
    },
    "case-score": {
      title: "Score explicable",
      body: "Chaque raison doit pouvoir être relue par un auditeur.",
    },
    "iban-ring": {
      title: "Signal bancaire critique",
      body: "Un meme IBAN apparait sur plusieurs fournisseurs de demonstration.",
    },
    "threshold-strip": {
      title: "Pattern de fractionnement",
      body: "14 factures proches du seuil interne de 5 000 EUR.",
    },
    "rbe-mismatch": {
      title: "Revue documentaire requise",
      body: "Le beneficiaire effectif externe ne matche pas le referentiel interne.",
    },
    "four-eyes": {
      title: "Controle 4-eyes a revoir",
      body: "Creation fournisseur et validation restent trop rapprochees.",
    },
    "evidence-seal": {
      title: "Piste d'audit",
      body: "Les pièces sont horodatées, hashées et prêtes à être partagées.",
    },
    "review-human": {
      title: "Decision controlee",
      body: "Le système prépare la revue ; la décision reste humaine.",
    },
    "export-ready": {
      title: "Document prêt",
      body: "Le paquet d'analyse rassemble synthèse, preuves et actions recommandées.",
    },
  },
  labels: {
    scene: "Scene",
    sources: "Sources",
    findings: "Findings d'investigation",
    observation: "Observation",
    why: "Pourquoi c'est important",
    proof: "Preuve associee",
    action: "Action recommandee",
    console: "Console d'analyse",
  },
  dataLineage: {
    title: "Cascade de rapprochement",
    subtitle: "5 sources rapprochees - 4 signaux priorises - 1 dossier fournisseur",
    sources: [
      "Referentiel fournisseur",
      "Ecritures P2P",
      "IBAN / coordonnees bancaires",
      "RBE / beneficiaires effectifs",
      "Audit log",
    ],
    output: "Score explicable 92/100",
  },
  scoreBreakdown: {
    title: "Score 92/100",
    subtitle: "Contribution illustrative des reason codes",
    illustrative: "Score de demonstration - ponderation illustrative",
  },
  microVisuals: {
    ibanTitle: "Anneau IBAN",
    ibanLabel: "IBAN partage",
    thresholdTitle: "Seuil 5 000 EUR",
    thresholdLabel: "14 factures / 30 jours",
    rbeTitle: "Comparatif RBE",
    rbeInternal: "Referentiel interne: A. Martin",
    rbeOfficial: "RBE INPI: L. Bernard",
    rbeMismatch: "Ecart detecte",
    fourEyesTitle: "Rupture 4-eyes",
    fourEyesSteps: ["Creation fournisseur", "Validation facture", "Paiement"],
    fourEyesLabel: "Meme perimetre / delai rapproche",
  },
  investigationMap: {
    title: "Carte d'investigation",
    steps: [
      "Alerte prioritaire",
      "Recherche fournisseur",
      "Rapprochement signaux",
      "Dossier 360",
      "Preuves scellees",
      "Revue humaine",
    ],
  },
  casePacket: {
    title: "Case packet",
    subtitle: "Dossier ALPHACOM prêt pour revue",
    idLabel: "ID",
    supplierLabel: "Fournisseur",
    scoreLabel: "Score",
    exposureLabel: "Exposition",
    signalsLabel: "Signaux",
    evidenceLabel: "Preuves",
    statusLabel: "Statut",
    statusValue: "Revue humaine requise",
    fingerprintLabel: "Empreinte",
    sealPrimary: "PREUVE SCELLÉE",
    sealSecondary: "AUDIT TRAIL READY",
    exportTitle: "Export d'analyse prêt",
    exportSubtitle: "Document structuré pour revue humaine",
    exportMeta: "PDF + JSON audit · 5 preuves · 4 findings",
    exportFeatures: [
      "Synthèse décisionnelle",
      "Preuves horodatées",
      "Reason codes explicables",
      "Actions de revue",
    ],
  },
};

const EN: DemoContent = {
  launch: {
    topbar: "Guided demo 60s",
    sidebar: "ALPHACOM scenario",
    home: "Guided demo",
  },
  controls: {
    skip: "Skip",
    skipAria: "Skip the demonstration",
    replay: "Replay demo",
    exploreCockpit: "Explore cockpit",
    viewScenarios: "View P2P scenarios",
    exportAnalysis: "Export for analysis",
    demoBadge: "Fictional demonstration data",
  },
  demoNotice: "Fictional demonstration data",
  brief: {
    kicker: "Demo mission - 60 seconds",
    objectiveLabel: "Objective",
    objective: "Identify why ALPHACOM SERVICES triggers a priority risk of 92/100.",
    signalsLabel: "Expected signals",
    signals: "Shared IBAN - sub-threshold structuring - 4-eyes breach - UBO mismatch.",
    outputLabel: "Expected output",
    output: "Vendor 360 case file + audit trail + recommended path.",
  },
  cockpit: {
    eyebrow: "P2P cockpit - consolidated view",
    title: "P2P risk cockpit",
    subtitle:
      "Consolidated view of vendor risks, sorted by financial exposure and ready for the audit decision.",
    searchPlaceholder: "Search a SIREN, vendor, IBAN, case or alert...",
    searchHint: "Vendor search - P2P master data - audit signals",
    loadingStatus:
      "Querying vendor master data - P2P entries - audit log - UBO - internal signals...",
    kpiTotal: "Total exposure",
    kpiCritical: "Critical exposure",
    kpiOpen: "Open cases",
    kpiSla: "SLA overruns",
    tableTitle: "Top vendors by exposure",
    tableSub: "Sorting favours financial impact, not just the raw score.",
    colVendor: "Vendor",
    colExposure: "Exposure",
    colFindings: "Findings",
    colSeverity: "Severity",
    colAction: "Action",
    open360: "Open 360",
    priorityEyebrow: "Priority of the day",
    priorityTitle: "Reduce critical exposure",
    priorityBody:
      "Handle first the highest-criticality vendors with SLA overruns or no assignment. Each case must produce actionable evidence.",
    suggestionsTitle: "Suggestions",
    suggestions: [
      "V00474 - ALPHACOM SERVICES - priority vendor",
      "V00444 - monitored vendor",
      "V00343 - high exposure",
    ],
  },
  case360: {
    eyebrow: "Fraud Case 360 - demonstration data",
    header: "V00474 - ALPHACOM SERVICES",
    subheader: "Vendor 360 case file - body of indicators to investigate",
    gaugeLabel: "Risk score",
    reasonCodesTitle: "Reason codes",
    signalsTitle: "Detected signals",
    prepareReview: "Prepare review",
  },
  reasonCodes: {
    IBAN_RING: {
      label: "Shared IBAN ring",
      description: "Same IBAN detected across several vendors linked in P2P master data.",
    },
    THRESHOLD_SPLIT: {
      label: "Sub-threshold structuring",
      description: "Series of clustered invoices just below the internal approval threshold.",
    },
    FOUR_EYES_BREAK: {
      label: "4-eyes breach",
      description: "Vendor creation and approval clustered within the same perimeter.",
    },
    RBE_MISMATCH: {
      label: "UBO / master-data mismatch",
      description: "Discrepancy between UBO data and the internal vendor master record.",
    },
    SLA_UNASSIGNED: {
      label: "SLA overrun / no assignment",
      description: "Priority case still waiting for a reviewer in the demo window.",
    },
  },
  evidence: {
    drawerTitle: "Evidence drawer",
    drawerSub: "Exhibits attached to the ALPHACOM scenario",
    sealed: "Sealed evidence",
    typeLabel: "Type",
    statusLabel: "Status",
    items: {
      "ev-iban": {
        title: "Shared IBAN",
        type: "Banking signal",
        status: "To qualify",
        detail: "Common IBAN observed across V00474, V00231 and V00118.",
      },
      "ev-invoice": {
        title: "Sub-threshold invoices",
        type: "Internal control",
        status: "To investigate",
        detail: "14 invoices between EUR 4,200 and EUR 4,950 over 30 days.",
      },
      "ev-four-eyes": {
        title: "4-eyes breach",
        type: "P2P governance",
        status: "Review required",
        detail: "Vendor creation and approval clustered within the same perimeter.",
      },
      "ev-rbe": {
        title: "UBO / master-data mismatch",
        type: "Vendor KYS",
        status: "Update required",
        detail: "Ultimate beneficial owner not aligned with the internal master data.",
      },
      "ev-sla": {
        title: "No assignment",
        type: "Audit workflow",
        status: "Reviewer required",
        detail: "Priority case has no assigned reviewer in the review path.",
      },
    },
  },
  alerts: {
    "iban-ring": {
      title: "Shared IBAN ring",
      text:
        "Three demonstration vendors share the same domiciliation IBAN. This signal should be qualified within anti-corruption controls and the internal control framework.",
      observation: "3 demonstration vendors share the same IBAN.",
      why: "A reused IBAN may indicate a vendor anomaly or a pattern to qualify.",
      proof: "ev-iban - ed25519:7f3a...91c2",
      action: "Document the banking signal.",
      badges: ["Critical signal", "Sapin II", "Internal control"],
      cta: "Document the signal",
    },
    threshold: {
      title: "Sub-threshold structuring",
      text:
        "Series of 14 invoices between EUR 4,200 and EUR 4,950 over 30 days. The pattern suggests a possible bypass of the EUR 5,000 approval threshold, to qualify before any conclusion.",
      observation: "14 invoices are clustered below the EUR 5,000 internal threshold.",
      why: "Repeated sub-threshold amounts can hide a control break to investigate.",
      proof: "ev-invoice - ed25519:93ab...4d20",
      action: "Open the entries and assign a review.",
      badges: ["Threshold split", "4-eyes", "P2P review"],
      cta: "Open the entries",
    },
    rbe: {
      title: "UBO / vendor master-data mismatch",
      text:
        "Ultimate beneficial owner data is not aligned with the internal vendor master record. A KYS update and a documentary review are recommended.",
      observation: "External UBO data differs from the internal master record.",
      why: "A documentary discrepancy must be explained before continuing the path.",
      proof: "ev-rbe - ed25519:b9aa...31e7",
      action: "Request a KYS update.",
      badges: ["UBO", "KYS", "Master data"],
      cta: "Request update",
    },
    concentration: {
      title: "Critical vendor concentration",
      text:
        "V00474 concentrates a significant share of the scenario's critical exposure. If the vendor qualifies as critical or ICT, enhanced third-party review should be considered.",
      observation: "ALPHACOM carries EUR 4,706,422 exposure in the demo.",
      why: "Prioritisation combines exposure, signals and handling delay.",
      proof: "ev-sla - ed25519:41f0...72ad",
      action: "Prepare the human review and escalation path.",
      badges: ["Third-party risk", "Concentration", "DORA if applicable"],
      cta: "Prepare third-party review",
    },
  },
  recommendations: {
    eyebrow: "Recommended path",
    title: "Case ready for review",
    sub: "Sealed evidence - audit trail generated",
    actions: ["Assign reviewer", "Generate audit trail", "Prepare compliance escalation note"],
    note: "No automatic filing. The case prepares the elements for human review.",
  },
  final: {
    title: "ALPHACOM case ready for review",
    stats: "Prioritised signals - sealed evidence - audit trail generated",
    tagline:
      "The cockpit does not conclude on fraud: it prioritises, documents and prepares the human review.",
    disclaimer:
      "Fictional demonstration. The cockpit prioritises signals, documents evidence and prepares the human review. It does not legally conclude on fraud.",
  },
  rail: {
    brief: "Brief",
    search: "Search",
    cascade: "Cascade",
    case360: "Case 360",
    evidence: "Evidence",
    recommendations: "Recommendations",
  },
  sceneLabels: {
    "cold-open": "Priority alert",
    "command-launch": "Mission",
    "cockpit-wide": "Cockpit",
    "search-zoom": "Vendor search",
    "data-cascade": "Signal cascade",
    "supplier-row": "Prioritisation",
    "case-file-open": "Case 360",
    "score-breakdown": "Explainable score",
    "evidence-build": "Evidence",
    "alert-sequence": "Findings",
    "review-path": "Human review",
    "export-ready": "Analysis export",
    "final-summary": "Case packet",
  },
  sceneCaptions: {
    "cold-open": {
      label: "Brief",
      title: "One vendor rises above the noise.",
      body: "ALPHACOM reaches the top of the queue: 92/100, EUR 4.7M exposed and several signals to qualify.",
    },
    "command-launch": {
      label: "Mission",
      title: "We replay the reasoning, not just the screen.",
      body: "The demo shows how a raw alert becomes a clear, reviewable and assignable case file.",
    },
    "cockpit-wide": {
      label: "Cockpit",
      title: "The cockpit sets the order of work.",
      body: "Amounts, delays and criticality show where the auditor should start.",
    },
    "search-zoom": {
      label: "Search",
      title: "One identifier is enough to isolate the subject.",
      body: "V00474 opens the vendor context, linked alerts and evidence already available.",
    },
    "data-cascade": {
      label: "Cascade",
      title: "The sources start speaking together.",
      body: "Master data, P2P entries, IBAN, UBO and audit log are reconciled before any conclusion.",
    },
    "supplier-row": {
      label: "Prioritisation",
      title: "The ALPHACOM row becomes actionable.",
      body: "The ranking explains why this vendor goes first without hiding the reasons.",
    },
    "case-file-open": {
      label: "Case 360",
      title: "Case 360 gives the pieces of the puzzle.",
      body: "The score only helps if it exposes the signals, dates and linked evidence.",
    },
    "score-breakdown": {
      label: "Score",
      title: "The 92/100 becomes understandable.",
      body: "Each strong score driver maps to a readable reason and a case exhibit.",
    },
    "evidence-build": {
      label: "Evidence",
      title: "Indicators become working evidence.",
      body: "IBAN, threshold, 4-eyes and UBO are timestamped, hashed and ready to review.",
    },
    "alert-sequence": {
      label: "Findings",
      title: "Each alert answers four questions.",
      body: "What did we see? Why does it matter? What evidence supports it? What action comes next?",
    },
    "review-path": {
      label: "Recommendations",
      title: "The next step is simple: assign, trace, decide.",
      body: "The cockpit prepares human review with a clear and prudent escalation path.",
    },
    "export-ready": {
      label: "Analysis export",
      title: "The case is ready to leave the cockpit.",
      body: "An analysis packet is generated: summary, evidence, fingerprints and next action.",
    },
    "final-summary": {
      label: "Case packet",
      title: "The ALPHACOM case is ready for review.",
      body: "The document is ready to export, share and review by a human reviewer.",
    },
  },
  consoleEvents: {
    init: "[00:01.120] init cockpit_context",
    "load-case": "[00:02.040] load priority_case supplier=V00474",
    "query-supplier": "[00:03.018] query supplier_index id=V00474",
    "fetch-ledger": "[00:06.211] fetch p2p_ledger window=30d",
    "scan-iban": "[00:07.004] scan iban_reuse graph_depth=2",
    "detect-threshold": "[00:08.440] detect threshold_split count=14 limit=5000",
    "compare-rbe": "[00:09.205] compare ubo_snapshot supplier_ref",
    "compute-score": "[00:10.880] compute risk_score -> 92",
    "open-case": "[00:13.012] open vendor_360 case=CASE-P2P-V00474",
    "seal-evidence": "[00:18.416] seal evidence_packet ed25519:7f3a...91c2",
    "prepare-review": "[00:23.100] prepare review_path reviewer_required=true",
    "build-export": "[00:26.420] build analysis_export format=case_packet",
    "packet-ready": "[00:27.000] packet status=ready_for_human_review",
  },
  callouts: {
    "priority-score": {
      title: "Priority score 92/100",
      body: "This score says where to look first, not what to conclude.",
    },
    "global-search": {
      title: "Search without detours",
      body: "Enter a vendor or identifier: the cockpit brings up the useful case.",
    },
    "critical-kpi": {
      title: "Critical exposure",
      body: "Financial exposure sets the review tempo.",
    },
    "supplier-row": {
      title: "Priority vendor",
      body: "ALPHACOM combines high exposure, multiple signals and handling delay.",
    },
    "data-lineage": {
      title: "Reconciliation cascade",
      body: "Data is reconciled before it is summarised.",
    },
    "case-score": {
      title: "Explainable score",
      body: "Each reason must be readable by an auditor.",
    },
    "iban-ring": {
      title: "Critical banking signal",
      body: "The same IBAN appears across multiple demonstration vendors.",
    },
    "threshold-strip": {
      title: "Structuring pattern",
      body: "14 invoices clustered near the EUR 5,000 internal threshold.",
    },
    "rbe-mismatch": {
      title: "Documentary review required",
      body: "The external UBO does not match internal master data.",
    },
    "four-eyes": {
      title: "4-eyes control to review",
      body: "Vendor creation and approval are too closely clustered.",
    },
    "evidence-seal": {
      title: "Audit trail",
      body: "Exhibits are timestamped, hashed and ready to share.",
    },
    "review-human": {
      title: "Controlled decision",
      body: "The system prepares the review; the decision remains human.",
    },
    "export-ready": {
      title: "Document ready",
      body: "The analysis packet gathers summary, evidence and recommended actions.",
    },
  },
  labels: {
    scene: "Scene",
    sources: "Sources",
    findings: "Investigation findings",
    observation: "Observation",
    why: "Why it matters",
    proof: "Associated evidence",
    action: "Recommended action",
    console: "Analysis console",
  },
  dataLineage: {
    title: "Reconciliation cascade",
    subtitle: "5 sources reconciled - 4 prioritised signals - 1 vendor case",
    sources: [
      "Vendor master data",
      "P2P entries",
      "IBAN / bank details",
      "UBO registry",
      "Audit log",
    ],
    output: "Explainable score 92/100",
  },
  scoreBreakdown: {
    title: "Score 92/100",
    subtitle: "Illustrative reason-code contribution",
    illustrative: "Demonstration score - illustrative weighting",
  },
  microVisuals: {
    ibanTitle: "IBAN ring",
    ibanLabel: "Shared IBAN",
    thresholdTitle: "EUR 5,000 threshold",
    thresholdLabel: "14 invoices / 30 days",
    rbeTitle: "UBO comparison",
    rbeInternal: "Internal record: A. Martin",
    rbeOfficial: "UBO registry: L. Bernard",
    rbeMismatch: "Mismatch detected",
    fourEyesTitle: "4-eyes breach",
    fourEyesSteps: ["Vendor creation", "Invoice approval", "Payment"],
    fourEyesLabel: "Same perimeter / clustered delay",
  },
  investigationMap: {
    title: "Investigation map",
    steps: [
      "Priority alert",
      "Vendor search",
      "Signal reconciliation",
      "Case 360",
      "Sealed evidence",
      "Human review",
    ],
  },
  casePacket: {
    title: "Case packet",
    subtitle: "ALPHACOM case ready for review",
    idLabel: "ID",
    supplierLabel: "Supplier",
    scoreLabel: "Score",
    exposureLabel: "Exposure",
    signalsLabel: "Signals",
    evidenceLabel: "Evidence",
    statusLabel: "Status",
    statusValue: "Human review required",
    fingerprintLabel: "Fingerprint",
    sealPrimary: "SEALED EVIDENCE",
    sealSecondary: "AUDIT TRAIL READY",
    exportTitle: "Analysis export ready",
    exportSubtitle: "Structured document for human review",
    exportMeta: "PDF + audit JSON · 5 exhibits · 4 findings",
    exportFeatures: [
      "Decision summary",
      "Timestamped evidence",
      "Explainable reason codes",
      "Review actions",
    ],
  },
};

export function getDemoContent(locale: Locale): DemoContent {
  return locale === "en" ? EN : FR;
}
