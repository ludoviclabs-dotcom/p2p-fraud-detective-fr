// Contenu bilingue (FR/EN) de la démo guidée P2P.
//
// Récit forensic fictif. Vocabulaire volontairement prudent : « signal »,
// « indice », « anomalie », « à qualifier », « à instruire » — jamais « fraude
// confirmée » ni notification réglementaire automatique. Fusionné avec les
// données structurelles de `p2p-demo-data.ts` par `code`/`id`.

import type { Locale } from "@/components/locale-provider";

export interface DemoContent {
  launch: { topbar: string; sidebar: string; home: string };
  controls: {
    skip: string;
    skipAria: string;
    replay: string;
    exploreCockpit: string;
    viewScenarios: string;
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
  alerts: Record<string, { title: string; text: string; badges: string[]; cta: string }>;
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
    replay: "↺ Rejouer la démo",
    exploreCockpit: "Explorer le cockpit →",
    viewScenarios: "Voir les scénarios P2P →",
    demoBadge: "Données de démonstration fictives",
  },
  demoNotice: "Données de démonstration fictives",
  brief: {
    kicker: "Mission démo · 60 secondes",
    objectiveLabel: "Objectif",
    objective:
      "Identifier pourquoi ALPHACOM SERVICES déclenche un risque prioritaire 92/100.",
    signalsLabel: "Signaux attendus",
    signals:
      "IBAN partagé · fractionnement sous seuil · rupture 4-eyes · incohérence RBE.",
    outputLabel: "Sortie attendue",
    output: "Dossier fournisseur 360 + piste d'audit + parcours recommandé.",
  },
  cockpit: {
    eyebrow: "Cockpit P2P · vue consolidée",
    title: "Cockpit risque P2P",
    subtitle:
      "Vue consolidée des risques fournisseurs, triée par exposition financière et prête pour la décision audit.",
    searchPlaceholder: "Rechercher un SIREN, fournisseur, IBAN, case ou alerte…",
    searchHint: "Recherche fournisseur · référentiel P2P · signaux audit",
    loadingStatus:
      "Interrogation référentiel fournisseur · écritures P2P · audit log · RBE · signaux internes…",
    kpiTotal: "Exposition totale",
    kpiCritical: "Exposition critique",
    kpiOpen: "Cases ouverts",
    kpiSla: "Retards SLA",
    tableTitle: "Top fournisseurs par exposition",
    tableSub: "Le tri favorise l'impact financier, pas seulement le score brut.",
    colVendor: "Fournisseur",
    colExposure: "Exposition",
    colFindings: "Findings",
    colSeverity: "Sévérité",
    colAction: "Action",
    open360: "Ouvrir 360",
    priorityEyebrow: "Priorité du jour",
    priorityTitle: "Réduire l'exposition critique",
    priorityBody:
      "Traiter d'abord les fournisseurs à criticité maximale avec retard SLA ou absence d'assignation. Chaque case doit produire une preuve exploitable.",
  },
  case360: {
    eyebrow: "Fraud Case 360 · données de démonstration",
    header: "V00474 · ALPHACOM SERVICES",
    subheader: "Dossier fournisseur 360 · faisceau d'indices à instruire",
    gaugeLabel: "Score de risque",
    reasonCodesTitle: "Reason codes",
    signalsTitle: "Signaux détectés",
    prepareReview: "Préparer revue",
  },
  reasonCodes: {
    IBAN_RING: {
      label: "Anneau IBAN partagé",
      description:
        "Même IBAN détecté sur plusieurs fournisseurs liés au référentiel P2P.",
    },
    THRESHOLD_SPLIT: {
      label: "Fractionnement sous seuil",
      description:
        "Série de factures rapprochées sous le seuil de validation interne.",
    },
    FOUR_EYES_BREAK: {
      label: "Rupture 4-eyes",
      description:
        "Validation et création fournisseur rapprochées sur un même périmètre opérationnel.",
    },
    RBE_MISMATCH: {
      label: "Écart RBE / référentiel",
      description:
        "Écart entre les informations bénéficiaires effectifs et le référentiel fournisseur.",
    },
  },
  evidence: {
    drawerTitle: "Evidence drawer",
    drawerSub: "Pièces associées au scénario ALPHACOM",
    sealed: "Preuve scellée",
    typeLabel: "Type",
    statusLabel: "Statut",
    items: {
      "ev-iban": {
        title: "IBAN partagé",
        type: "Signal bancaire",
        status: "À qualifier",
        detail: "IBAN commun observé entre V00474, V00231 et V00118.",
      },
      "ev-invoice": {
        title: "Factures sous seuil",
        type: "Contrôle interne",
        status: "À instruire",
        detail: "14 factures entre 4 200 € et 4 950 € sur 30 jours.",
      },
      "ev-four-eyes": {
        title: "Rupture 4-eyes",
        type: "Gouvernance P2P",
        status: "Revue requise",
        detail:
          "Création fournisseur et validation rapprochées dans le même périmètre.",
      },
      "ev-rbe": {
        title: "Écart RBE / référentiel",
        type: "KYS fournisseur",
        status: "Mise à jour requise",
        detail: "Bénéficiaire effectif non aligné avec le référentiel interne.",
      },
    },
  },
  alerts: {
    "iban-ring": {
      title: "Anneau IBAN partagé détecté",
      text:
        "Trois fournisseurs de démonstration partagent un même IBAN de domiciliation. Signal caractéristique d'un schéma fournisseur à qualifier dans le cadre des contrôles anticorruption et du dispositif de contrôle interne.",
      badges: ["Signal critique", "Sapin II", "Contrôle interne"],
      cta: "Documenter le signal",
    },
    threshold: {
      title: "Fractionnement sous seuil à instruire",
      text:
        "Série de 14 factures entre 4 200 € et 4 950 € sur 30 jours. Le schéma suggère un possible contournement du seuil interne de validation à 5 000 €, à qualifier avant toute conclusion.",
      badges: ["Threshold split", "4-eyes", "Revue P2P"],
      cta: "Ouvrir les écritures",
    },
    rbe: {
      title: "Écart RBE / référentiel fournisseur",
      text:
        "Les informations bénéficiaires effectifs ne sont pas alignées avec le référentiel fournisseur interne. Une mise à jour KYS et une revue documentaire sont recommandées.",
      badges: ["RBE", "KYS", "Référentiel"],
      cta: "Demander mise à jour",
    },
    concentration: {
      title: "Concentration fournisseur critique",
      text:
        "V00474 concentre une part significative de l'exposition critique du scénario. Si le fournisseur est qualifié de prestataire critique ou TIC, une revue risque tiers renforcée doit être envisagée.",
      badges: ["Risque tiers", "Concentration", "DORA si applicable"],
      cta: "Préparer revue tiers",
    },
  },
  recommendations: {
    eyebrow: "Parcours recommandé",
    title: "Dossier prêt pour revue",
    sub: "Preuves scellées · piste d'audit générée",
    actions: [
      "Assigner reviewer",
      "Générer audit trail",
      "Préparer note d'escalade conformité",
    ],
    note: "Aucune déclaration automatique. Le dossier prépare les éléments pour revue humaine.",
  },
  final: {
    title: "Investigation documentée en 60 secondes",
    stats: "383 cases · 6 579 354 € d'exposition · 4 signaux explicables",
    tagline:
      "Le cockpit ne conclut pas à la fraude : il priorise, documente et prépare la revue humaine.",
    disclaimer:
      "Démonstration fictive. Le cockpit priorise les signaux, documente les preuves et prépare la revue humaine. Il ne conclut pas juridiquement à une fraude.",
  },
  rail: {
    brief: "Brief",
    search: "Recherche",
    cascade: "Cascade",
    case360: "Dossier 360",
    evidence: "Preuves",
    recommendations: "Recommandations",
  },
};

const EN: DemoContent = {
  launch: {
    topbar: "Guided demo · 60s",
    sidebar: "ALPHACOM scenario",
    home: "Guided demo",
  },
  controls: {
    skip: "Skip",
    skipAria: "Skip the demonstration",
    replay: "↺ Replay demo",
    exploreCockpit: "Explore the cockpit →",
    viewScenarios: "View P2P scenarios →",
    demoBadge: "Fictional demonstration data",
  },
  demoNotice: "Fictional demonstration data",
  brief: {
    kicker: "Demo mission · 60 seconds",
    objectiveLabel: "Objective",
    objective: "Identify why ALPHACOM SERVICES triggers a priority risk of 92/100.",
    signalsLabel: "Expected signals",
    signals: "Shared IBAN · sub-threshold structuring · 4-eyes breach · UBO mismatch.",
    outputLabel: "Expected output",
    output: "Vendor 360 case file + audit trail + recommended path.",
  },
  cockpit: {
    eyebrow: "P2P cockpit · consolidated view",
    title: "P2P risk cockpit",
    subtitle:
      "Consolidated view of vendor risks, sorted by financial exposure and ready for the audit decision.",
    searchPlaceholder: "Search a SIREN, vendor, IBAN, case or alert…",
    searchHint: "Vendor search · P2P master data · audit signals",
    loadingStatus:
      "Querying vendor master data · P2P entries · audit log · UBO · internal signals…",
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
  },
  case360: {
    eyebrow: "Fraud Case 360 · demonstration data",
    header: "V00474 · ALPHACOM SERVICES",
    subheader: "Vendor 360 case file · body of indicators to investigate",
    gaugeLabel: "Risk score",
    reasonCodesTitle: "Reason codes",
    signalsTitle: "Detected signals",
    prepareReview: "Prepare review",
  },
  reasonCodes: {
    IBAN_RING: {
      label: "Shared IBAN ring",
      description: "Same IBAN detected across several vendors linked in the P2P master data.",
    },
    THRESHOLD_SPLIT: {
      label: "Sub-threshold structuring",
      description: "Series of clustered invoices just below the internal approval threshold.",
    },
    FOUR_EYES_BREAK: {
      label: "4-eyes breach",
      description:
        "Vendor creation and approval clustered within the same operational perimeter.",
    },
    RBE_MISMATCH: {
      label: "UBO / master-data mismatch",
      description:
        "Discrepancy between ultimate beneficial owner data and the vendor master record.",
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
        detail: "14 invoices between €4,200 and €4,950 over 30 days.",
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
    },
  },
  alerts: {
    "iban-ring": {
      title: "Shared IBAN ring detected",
      text:
        "Three demonstration vendors share the same domiciliation IBAN. A signal characteristic of a vendor scheme to qualify within anti-corruption controls and the internal control framework.",
      badges: ["Critical signal", "Sapin II", "Internal control"],
      cta: "Document the signal",
    },
    threshold: {
      title: "Sub-threshold structuring to investigate",
      text:
        "Series of 14 invoices between €4,200 and €4,950 over 30 days. The pattern suggests a possible circumvention of the €5,000 internal approval threshold, to qualify before any conclusion.",
      badges: ["Threshold split", "4-eyes", "P2P review"],
      cta: "Open the entries",
    },
    rbe: {
      title: "UBO / vendor master-data mismatch",
      text:
        "Ultimate beneficial owner data is not aligned with the internal vendor master record. A KYS update and a documentary review are recommended.",
      badges: ["UBO", "KYS", "Master data"],
      cta: "Request update",
    },
    concentration: {
      title: "Critical vendor concentration",
      text:
        "V00474 concentrates a significant share of the scenario's critical exposure. If the vendor qualifies as a critical or ICT provider, an enhanced third-party risk review should be considered.",
      badges: ["Third-party risk", "Concentration", "DORA if applicable"],
      cta: "Prepare third-party review",
    },
  },
  recommendations: {
    eyebrow: "Recommended path",
    title: "Case ready for review",
    sub: "Sealed evidence · audit trail generated",
    actions: ["Assign reviewer", "Generate audit trail", "Prepare compliance escalation note"],
    note: "No automatic filing. The case prepares the elements for human review.",
  },
  final: {
    title: "Investigation documented in 60 seconds",
    stats: "383 cases · €6,579,354 exposure · 4 explainable signals",
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
};

export function getDemoContent(locale: Locale): DemoContent {
  return locale === "en" ? EN : FR;
}
