type DemoCase = {
  case_id: string;
  title: string;
  severity: "critical" | "high" | "medium" | "low";
  status: string;
  vendor_id: string;
  invoice_id: string | null;
  exposure_eur: number;
  assignee: string | null;
  created_at: string;
  closed_at: string | null;
  closure_reason: string | null;
  rule_id: string;
  signal: string;
  detector: string;
};

export const demoModeMeta = {
  mode: "demo",
  data_origin: "synthetic",
  live_sources_enabled: false,
  public_sources: ["Sirene", "DECP", "OpenSanctions"],
  notice:
    "Mode demo Vercel: donnees synthetiques, aucun appel live Sirene/DECP/RBE/OpenSanctions.",
};

export const demoCases: DemoCase[] = [
  {
    case_id: "CASE-bec-iban-001",
    title: "BEC suspecte - Acme Industries",
    severity: "critical",
    status: "new",
    vendor_id: "V-FOURNISSEUR-789",
    invoice_id: "INV-2026-0142",
    exposure_eur: 184500,
    assignee: null,
    created_at: "2026-05-14T09:12:00.000Z",
    closed_at: null,
    closure_reason: null,
    rule_id: "MD_IBAN_NO_4EYES",
    signal: "Changement IBAN sans approbation 4-eyes",
    detector: "master_data_changes",
  },
  {
    case_id: "CASE-dup-002",
    title: "Doublon Prestation Conseil",
    severity: "high",
    status: "triaged",
    vendor_id: "V-PRESTA-456",
    invoice_id: "INV-2026-0234",
    exposure_eur: 12580,
    assignee: "alice.controleur",
    created_at: "2026-05-13T14:35:00.000Z",
    closed_at: null,
    closure_reason: null,
    rule_id: "DUP_FUZZY_NAME_AMOUNT",
    signal: "Doublon flou nom + montant",
    detector: "duplicates",
  },
  {
    case_id: "CASE-threshold-003",
    title: "Fragmentation suspectee - Maintenance Express",
    severity: "high",
    status: "investigating",
    vendor_id: "V-SOUS-SEUIL-321",
    invoice_id: "INV-2026-0301",
    exposure_eur: 14650,
    assignee: "bob.audit",
    created_at: "2026-05-12T10:05:00.000Z",
    closed_at: null,
    closure_reason: null,
    rule_id: "THRESHOLD_CLUSTER",
    signal: "3 factures de 4.8-4.9 kEUR sur 30 jours",
    detector: "under_thresholds",
  },
  {
    case_id: "CASE-sanctions-004",
    title: "Sanctions OFAC - Volkov Trading",
    severity: "critical",
    status: "escalated",
    vendor_id: "V-SANC-007",
    invoice_id: null,
    exposure_eur: 73200,
    assignee: "claire.compliance",
    created_at: "2026-05-11T16:20:00.000Z",
    closed_at: null,
    closure_reason: null,
    rule_id: "SANCTIONS_VENDOR",
    signal: "Match snapshot sanctions demo score 0.96",
    detector: "sanctions",
  },
  {
    case_id: "CASE-false-positive-005",
    title: "Doublon Societe Generale Services",
    severity: "medium",
    status: "closed_false_positive",
    vendor_id: "V-LEGITIME-100",
    invoice_id: "INV-2026-0089",
    exposure_eur: 4200,
    assignee: "auditeur.demo",
    created_at: "2026-05-10T08:42:00.000Z",
    closed_at: "2026-05-15T11:03:00.000Z",
    closure_reason: "Factures distinctes, BC differents.",
    rule_id: "DUP_FUZZY_NAME_AMOUNT",
    signal: "Doublon flou nom score 0.88",
    detector: "duplicates",
  },
];

export const demoScenarios = [
  {
    name: "bec_iban_swap",
    title: "BEC - changement IBAN fournisseur",
    pillar: "Master data",
    severity: "critical",
    short: "Un IBAN fournisseur change sans validation 4-eyes avant paiement.",
    detectors: ["master_data_changes", "score_explorer"],
    target_vendor: "V-FOURNISSEUR-789",
    storyline:
      "Le fournisseur Acme Industries change d'IBAN juste avant un paiement de 184 500 EUR. La validation 4-eyes est absente et l'utilisateur ERP est inhabituel.",
  },
  {
    name: "doublons_fournisseurs",
    title: "Doublon fournisseur / facture",
    pillar: "Controle facture",
    severity: "high",
    short: "Deux factures proches partagent un montant et un libelle similaires.",
    detectors: ["duplicates", "score_explorer"],
    target_vendor: "V-PRESTA-456",
    storyline:
      "Deux factures Prestation Conseil presentent un montant proche et un nom fuzzy-matche. La preuve attendue est le rapprochement facture, BC et reception.",
  },
  {
    name: "fractionnement",
    title: "Fractionnement sous seuil",
    pillar: "Controle interne",
    severity: "high",
    short: "Trois factures restent juste sous un seuil de validation.",
    detectors: ["under_thresholds", "score_explorer"],
    target_vendor: "V-SOUS-SEUIL-321",
    storyline:
      "Maintenance Express facture plusieurs prestations de 4.8-4.9 kEUR dans une fenetre courte. Le controle recherche un contournement de seuil.",
  },
  {
    name: "sanctions_ue",
    title: "Match sanctions / PEP",
    pillar: "Conformite",
    severity: "critical",
    short: "Un fournisseur de demonstration matche un snapshot sanctions.",
    detectors: ["sanctions", "pep", "score_explorer"],
    target_vendor: "V-SANC-007",
    storyline:
      "Volkov Trading apparait dans le snapshot sanctions de demonstration. En production, le match doit etre confirme avec la source officielle active.",
  },
  {
    name: "anneau_fraude",
    title: "Anneau IBAN partage",
    pillar: "Graphe",
    severity: "critical",
    short: "Plusieurs fournisseurs partagent un meme IBAN.",
    detectors: ["network_rings", "shell_companies"],
    target_vendor: null,
    storyline:
      "Trois fournisseurs synthetiques convergent vers un meme IBAN. Le graphe aide a prioriser le cluster et les beneficiaires possibles.",
  },
];

export function demoFindings() {
  return demoCases.map((c) => ({
    invoice_id: c.invoice_id ?? `VENDOR::${c.vendor_id}`,
    rule_id: c.rule_id,
    severity: c.severity,
    signal: c.signal,
    detector: c.detector,
    detected_at: c.created_at,
    evidence: {
      case_id: c.case_id,
      vendor_id: c.vendor_id,
      exposure_eur: c.exposure_eur,
      data_origin: "synthetic",
    },
  }));
}

export function demoAuditEntries() {
  return demoCases.flatMap((c, index) => {
    const seq = index * 2 + 1;
    return [
      {
        seq,
        at: c.created_at,
        actor: "auditeur.demo",
        kind: "case.created",
        payload: {
          case_id: c.case_id,
          severity: c.severity,
          rule_id: c.rule_id,
          signal: c.signal,
          data_origin: "synthetic",
        },
        prev_hash: seq === 1 ? "GENESIS" : `demo-prev-${seq}`,
        hash: `demo-hash-${seq}`,
        signature: "",
      },
      {
        seq: seq + 1,
        at: c.created_at,
        actor: c.assignee ?? "auditeur.demo",
        kind: c.assignee ? "case.assigned" : "case.triaged",
        payload: {
          case_id: c.case_id,
          assignee: c.assignee,
          data_origin: "synthetic",
        },
        prev_hash: `demo-hash-${seq}`,
        hash: `demo-hash-${seq + 1}`,
        signature: "",
      },
    ];
  });
}

export function demoDailySeries(key: "created" | "closed" | "critical" | "audit") {
  const today = new Date("2026-05-17T00:00:00.000Z");
  const points = [];
  for (let i = 29; i >= 0; i--) {
    const d = new Date(today);
    d.setUTCDate(today.getUTCDate() - i);
    const iso = d.toISOString().slice(0, 10);
    const value =
      key === "closed"
        ? iso === "2026-05-15"
          ? 1
          : 0
        : key === "critical"
          ? ["2026-05-11", "2026-05-14"].includes(iso)
            ? 1
            : 0
          : key === "audit"
            ? demoAuditEntries().filter((e) => e.at.slice(0, 10) === iso).length
            : demoCases.filter((c) => c.created_at.slice(0, 10) === iso).length;
    points.push({ date: iso, value });
  }
  return points;
}
