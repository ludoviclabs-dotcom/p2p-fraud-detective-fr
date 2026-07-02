// Forensic home ("Salle d'enquête") — synthetic but realistic data.

export interface Finding {
  mark: string;
  level: "risk" | "warn" | "info";
  title: string;
  det: string;
  conf: string;
}

export type ScenarioGraph = "central-iban" | "duplicate" | "structuring" | "sanction";

export interface Scenario {
  id: string;
  code: string;
  title: string;
  vendor: string;
  siren: string;
  score: number;
  severity: "CRITICAL" | "HIGH";
  iban: { current: string; changedSeg: string; previous: string };
  exposure: string;
  cases: number;
  sla: number;
  confidence: number;
  findings: Finding[];
  graph: ScenarioGraph;
}

export const SCENARIOS: Scenario[] = [
  {
    id: "iban-swap",
    code: "IBAN-SWAP",
    title: "Changement IBAN frauduleux",
    vendor: "ALPHACOM SERVICES SAS",
    siren: "812 446 901",
    score: 92,
    severity: "CRITICAL",
    iban: {
      current: "FR76 3000 4015 8800 0212 5847 9",
      changedSeg: "8800 0212 5847 9",
      previous: "FR76 1027 8073 3000 0145 2233 0",
    },
    exposure: "847 200 €",
    cases: 3,
    sla: 1,
    confidence: 0.94,
    findings: [
      { mark: "R", level: "risk", title: "IBAN modifié <24h avant règlement", det: "Δt = −18h · 4-eyes breach", conf: "p=0.94" },
      { mark: "R", level: "risk", title: "Nouveau RIB hors zone SEPA habituelle", det: "FR → DE · jamais vu", conf: "p=0.88" },
      { mark: "W", level: "warn", title: "Demande par email externe", det: "Domaine alphacom-fr.co", conf: "p=0.71" },
      { mark: "I", level: "info", title: "Approbateur unique (rôle dual requis)", det: "ISA 240 · contrôle interne", conf: "p=0.62" },
    ],
    graph: "central-iban",
  },
  {
    id: "duplicate",
    code: "DOUBLON",
    title: "Doublon de facture rapproché",
    vendor: "OMÉGA LOGISTIQUE",
    siren: "443 109 887",
    score: 87,
    severity: "CRITICAL",
    iban: {
      current: "FR76 3000 1007 4100 0067 4112 6",
      changedSeg: "0067 4112 6",
      previous: "FR76 3000 1007 4100 0067 4112 6",
    },
    exposure: "412 880 €",
    cases: 2,
    sla: 0,
    confidence: 0.91,
    findings: [
      { mark: "R", level: "risk", title: "2 factures · même montant ± 0.01€", det: "F-2026-04419 ↔ F-2026-04428", conf: "p=0.97" },
      { mark: "R", level: "risk", title: "Émission < 48h d'écart", det: "Δt = 31h", conf: "p=0.93" },
      { mark: "W", level: "warn", title: "Numéros BON-LIVRAISON identiques", det: "BL-OM-22841 (×2)", conf: "p=0.84" },
      { mark: "I", level: "info", title: "PO distinct (split intentionnel)", det: "PO-22841-A / PO-22841-B", conf: "p=0.58" },
    ],
    graph: "duplicate",
  },
  {
    id: "structuring",
    code: "SOUS-SEUIL",
    title: "Fractionnement sous délégation",
    vendor: "BÂTIPRO TRAVAUX",
    siren: "311 998 220",
    score: 81,
    severity: "HIGH",
    iban: {
      current: "FR76 1820 6000 4700 0091 1244 0",
      changedSeg: "",
      previous: "FR76 1820 6000 4700 0091 1244 0",
    },
    exposure: "324 500 €",
    cases: 14,
    sla: 4,
    confidence: 0.86,
    findings: [
      { mark: "R", level: "risk", title: "14 factures dans [4 800 € — 4 999 €]", det: "Seuil délégation = 5 000 €", conf: "p=0.92" },
      { mark: "R", level: "risk", title: "Pic anormal sur 14 jours", det: "+820% vs baseline", conf: "p=0.89" },
      { mark: "W", level: "warn", title: "Même approbateur sur 12/14", det: "USER-LDU221 · 86%", conf: "p=0.79" },
      { mark: "I", level: "info", title: "Aucun appel d'offres associé", det: "Marché < 25k€ direct", conf: "p=0.54" },
    ],
    graph: "structuring",
  },
  {
    id: "sanction",
    code: "SANCTION",
    title: "Match liste de sanctions",
    vendor: "INTERNATIONAL TRADE PARTNERS",
    siren: "—",
    score: 96,
    severity: "CRITICAL",
    iban: {
      current: "CY17 0020 0128 0000 0012 0052 76",
      changedSeg: "CY17",
      previous: "—",
    },
    exposure: "1 240 000 €",
    cases: 1,
    sla: 0,
    confidence: 0.98,
    findings: [
      { mark: "R", level: "risk", title: "Bénéficiaire effectif sur OFAC SDN", det: "Match fuzzy 97% · Ratchenko I.", conf: "p=0.98" },
      { mark: "R", level: "risk", title: "Pas d'identifiant FR (hors Sirene)", det: "SIREN absent · juridiction CY", conf: "p=0.96" },
      { mark: "W", level: "warn", title: "OpenSanctions · PEP secondaire", det: "Liste Trésor FR 2025-Q4", conf: "p=0.81" },
      { mark: "I", level: "info", title: "1ère facture · paiement immédiat", det: "Net 0 · inhabituel", conf: "p=0.67" },
    ],
    graph: "sanction",
  },
];

export interface Detector {
  num: string;
  name: string;
  meta: string;
  f1: string;
  w: number;
  ref: string;
}

export const DETECTORS: Detector[] = [
  { num: "01", name: "Master Data History", meta: "Diff IBAN · nom · SIREN · 4-eyes breach", f1: "F1 = 0.94", w: 94, ref: "ISA 240 · AFP 2026" },
  { num: "02", name: "Doublons Fuzzy", meta: "Bucket montant ±0.01 € · date ±2j", f1: "F1 = 0.47 (R=1.00)", w: 100, ref: "AICPA ADS" },
  { num: "03", name: "Sous-Seuils", meta: "Fenêtre [seuil−ε, seuil[", f1: "F1 = 0.63 (R=1.00)", w: 100, ref: "Contrôle interne" },
  { num: "04", name: "Cross-check Sirene", meta: "API v3 · statut · date · code APE", f1: "Coverage 99.8%", w: 99, ref: "INSEE" },
  { num: "05", name: "Sanctions & PEP", meta: "OpenSanctions · OFAC · Trésor FR", f1: "Recall 0.96", w: 96, ref: "LCB-FT · Sapin 2" },
  { num: "06", name: "Isolation Forest", meta: "Pipeline scikit-learn · features", f1: "F1 = 0.62", w: 62, ref: "ML anomaly" },
  { num: "07", name: "Anneaux de fraude", meta: "Graphe NetworkX · employés ⟷ vendors", f1: "Précision élevée", w: 88, ref: "Forensic accounting" },
  { num: "08", name: "Risk Score consolidé", meta: "Pondération YAML · reason codes FR", f1: "F1 = 0.91", w: 91, ref: "Continuous auditing" },
];

export interface TickerItem {
  t: string;
  sev: "crit" | "high" | "med";
  txt: string;
}

export const TICKER_ITEMS: TickerItem[] = [
  { t: "12:47:08", sev: "crit", txt: "ALPHACOM SERVICES — IBAN modifié <24h, exposition 847k€" },
  { t: "12:45:22", sev: "high", txt: "OMÉGA LOGISTIQUE — doublon F-2026-04419 ↔ 04428" },
  { t: "12:42:11", sev: "med", txt: "Sirene · vérification 1 247 fournisseurs · OK" },
  { t: "12:39:54", sev: "crit", txt: "INTL TRADE PARTNERS — match OFAC SDN 97%" },
  { t: "12:35:08", sev: "high", txt: "BÂTIPRO TRAVAUX — 14 factures sous seuil 5k€ en 14j" },
  { t: "12:30:41", sev: "med", txt: "DECP · ingestion 3 412 marchés · 7 nouveaux fournisseurs" },
  { t: "12:27:19", sev: "crit", txt: "DELTA SERVICES — IBAN partagé avec 4 entités distinctes" },
  { t: "12:22:03", sev: "high", txt: "Audit log · 8 412 entrées signées Ed25519 · hash OK" },
];

export interface Referential {
  num: string;
  name: string;
  desc: string;
  tag: string;
}

export const REFERENTIALS: Referential[] = [
  { num: "I", name: "ISA 240", desc: "Responsabilités de l'auditeur concernant les fraudes. Tests JET, contrôles 4-eyes, Benford en outil de scoping.", tag: "Audit légal" },
  { num: "II", name: "AS 2401", desc: "Équivalent PCAOB · applicable à l'audit des entités cotées SEC (filiales US d'ETI françaises).", tag: "PCAOB · US" },
  { num: "III", name: "Sapin 2 · Art. 17", desc: "Cartographie des risques de corruption. Réutilise le risk engine du module P2P pour la conformité.", tag: "Anti-corruption" },
  { num: "IV", name: "DORA · Art. 28", desc: "Résilience opérationnelle numérique · registre des prestataires TIC alimenté par le client Sirene.", tag: "Résilience UE" },
  { num: "V", name: "LCB-FT", desc: "Lutte contre le blanchiment · matching fuzzy contre OpenSanctions, Trésor FR, OFAC SDN.", tag: "Conformité bancaire" },
  { num: "VI", name: "NIS2 · supply chain", desc: "Gestion du risque tiers (art. 21) · le registre fournisseurs scoré couvre le pilier chaîne d'approvisionnement.", tag: "Cyber · UE" },
  { num: "VII", name: "IPR 2024/886 · VoP", desc: "Verification of Payee obligatoire (oct. 2025) · pré-check nom ↔ IBAN dès la saisie du RIB, en amont du PSP.", tag: "Paiements UE" },
  { num: "VIII", name: "FNC-RF · BdF 2026", desc: "Fichier des IBAN frauduleux partagé entre PSP · connecteur réservé, complémentaire du contrôle interne pre-payment.", tag: "Banque de France" },
];

export const HASH_CHAIN: string[] = [
  "0x7a9f3b2c8e4d", "0xf28b1c9a45e7", "0x3d8e7f2a91bc", "0xbe19a07c4f3d",
  "0x29c4b8e1735a", "0x801f5d2a9bc8", "0x4a73e9c182bf", "0xd7b5210ac8f3",
  "0x916e3a4c8d2b", "0x5c2f87a1d49e", "0xab8c0e5f923d", "0x37e2b9c1a4f8",
];

export type EvPayloadValue = string | number | boolean | string[];

export interface EvEntry {
  when: string;
  glyph: string;
  what: string;
  who: string;
  level?: "crit" | "sealed";
  hash: string;
  payload: Record<string, EvPayloadValue>;
}

export const EV_DATA: EvEntry[] = [
  { when: "T−18h00", glyph: "△", what: "USER-LDU221 modifie l'IBAN + banque · pas de contre-signature", who: "vendor-master", level: "crit", hash: "7a9f3b2c", payload: { actor: "USER-LDU221", action: "iban_change", before: "FR76 1027…2233 0", after: "FR76 3000…5847 9" } },
  { when: "T−17h42", glyph: "▣", what: "Émission F-2026-04419 · 412 880 € · règlement immédiat", who: "RBKP · AP", level: "crit", hash: "f28b1c9a", payload: { invoice: "F-2026-04419", amount: 412880, currency: "EUR", terms: "net_0" } },
  { when: "T+00h00", glyph: "·", what: "Scheduler nocturne · pipeline P2P", who: "scheduler", hash: "3d8e7f2a", payload: { job: "nightly_p2p", trigger: "cron", detectors: 8 } },
  { when: "T+00h02", glyph: "✦", what: "Détecteur 01 master data history · score brut 0.94", who: "det · 01", hash: "be19a07c", payload: { detector: "master_data_history", score: 0.94, reason_codes: ["MD_IBAN_CHANGE", "MD_4EYES_VIOLATION"] } },
  { when: "T+00h02", glyph: "✦", what: "Détecteur 04 Sirene · OK · entreprise active", who: "det · 04", hash: "29c4b8e1", payload: { detector: "sirene_crosscheck", siren: "812446901", status: "active" } },
  { when: "T+00h02", glyph: "✦", what: "Détecteur 05 sanctions · pas de match", who: "det · 05", hash: "801f5d2a", payload: { detector: "sanctions", match: false, sources: ["OFAC", "OpenSanctions", "TresorFR"] } },
  { when: "T+00h03", glyph: "Σ", what: "Risk Score consolidé · 92 · CRITIQUE · alerte CAC", who: "risk-engine", level: "crit", hash: "4a73e9c1", payload: { final_score: 92, severity: "CRITICAL", channel: "cac_alert" } },
  { when: "T+00h03", glyph: "✓", what: "Audit log entry · hash chaîné · signature Ed25519", who: "audit", level: "sealed", hash: "d7b5210a", payload: { entries: 8412, signature_algo: "Ed25519", chain_intact: true } },
  { when: "T+01h12", glyph: "⌘", what: "Reviewer assigné · USER-VAL-088 · 4-eyes restauré", who: "case · CASE-2041", hash: "916e3a4c", payload: { case_id: "CASE-2041", reviewer: "USER-VAL-088", four_eyes: "restored" } },
  { when: "T+24h00", glyph: "★", what: "Dossier clôturé · règlement bloqué · CAC informé", who: "case · CASE-2041", level: "sealed", hash: "5c2f87a1", payload: { case_id: "CASE-2041", status: "closed", payment_blocked: true, cac_notified: true } },
];

export interface ToolLink {
  ic: string;
  lab: string;
  href: string;
}

export interface ToolGroup {
  code: string;
  title: string;
  intent: string;
  tools: ToolLink[];
}

export const TOOL_GROUPS: ToolGroup[] = [
  {
    code: "A",
    title: "Investiguer",
    intent:
      "Vous avez une alerte. Vous voulez ouvrir un dossier, retracer les faits, désigner un responsable et signer la décision.",
    tools: [
      { ic: "▣", lab: "Dossiers en cours", href: "/cases" },
      { ic: "◎", lab: "Fraud Case 360", href: "/fraud-case-360/CASE-APP-BANK-001" },
      { ic: "◫", lab: "Fournisseur 360", href: "/vendors" },
      { ic: "!", lab: "Alertes (stream)", href: "/alerts" },
      { ic: "⌘", lab: "4-eyes & collab", href: "/collab" },
      { ic: "§", lab: "Méthodologie audit", href: "/methodology" },
    ],
  },
  {
    code: "B",
    title: "Contrôler",
    intent:
      "Vous voulez exécuter les 8 détecteurs sur votre extraction, les comparer, voir les reason codes.",
    tools: [
      { ic: "▶", lab: "Sandbox · démo", href: "/sandbox" },
      { ic: "✦", lab: "Detection Studio", href: "/detection-studio" },
      { ic: "⊟", lab: "Risk Test Lab (A/B)", href: "/risk-test-lab" },
      { ic: "△", lab: "Anomalies (IForest)", href: "/anomalies" },
      { ic: "□", lab: "Doublons fuzzy", href: "/duplicates" },
      { ic: "⌒", lab: "Sous-seuils", href: "/structuring" },
      { ic: "✕", lab: "Sanctions & PEP", href: "/sanctions" },
      { ic: "◇", lab: "Anneaux IBAN", href: "/rings" },
      { ic: "Σ", lab: "Risk Score", href: "/score" },
    ],
  },
  {
    code: "C",
    title: "Piloter & prouver",
    intent:
      "Vous présentez à votre Comex, votre CAC, votre régulateur. Vous voulez le cockpit, les exports et la preuve d'audit.",
    tools: [
      { ic: "▤", lab: "Cockpit P2P", href: "/dashboard" },
      { ic: "↥", lab: "Upload Excel · CSV", href: "/upload" },
      { ic: "✓", lab: "Sirene (live)", href: "/sirene" },
      { ic: "✓", lab: "DECP · RBE (live)", href: "/decp-rbe" },
      { ic: "↺", lab: "Master History diff", href: "/master-history" },
      { ic: "↓", lab: "Exports XLSX · Parquet", href: "/exports" },
      { ic: "✓", lab: "Audit log Ed25519", href: "/audit" },
      { ic: "★", lab: "Trust center", href: "/governance" },
    ],
  },
];

export type SidebarBadge = "new" | "risk" | "live";

export interface SidebarItem {
  href: string;
  ic: string;
  label: string;
  hint: string;
  badge?: SidebarBadge;
}

export interface SidebarSection {
  title: string;
  code: string;
  items: SidebarItem[];
}

export const SB_SECTIONS: SidebarSection[] = [
  {
    title: "Commande",
    code: "01",
    items: [
      { href: "#hero", ic: "◉", label: "Console live", hint: "Cockpit live" },
      { href: "#acte-i", ic: "I", label: "L'événement", hint: "Acte I · le déclencheur" },
      { href: "#pipeline", ic: "II", label: "La cascade", hint: "Acte II · les 8 détecteurs" },
      { href: "#anatomy", ic: "✚", label: "Planche n°I", hint: "Anatomie d'une fraude" },
      { href: "#evlog", ic: "III", label: "La signature", hint: "Acte III · journal scellé" },
      { href: "#toolmap", ic: "▦", label: "Tous les outils", hint: "Cartographie · 26 outils" },
    ],
  },
  {
    title: "Atelier",
    code: "02",
    items: [
      { href: "/dashboard", ic: "▤", label: "Cockpit P2P", hint: "KPIs & top fournisseurs" },
      { href: "/sandbox", ic: "▶", label: "Sandbox", hint: "Démo guidée", badge: "new" },
      { href: "/tour", ic: "→", label: "Tour produit", hint: "60s walkthrough" },
      { href: "/p2p-scenarios", ic: "⊞", label: "P2P Scenarios", hint: "Typologies prêtes", badge: "new" },
      { href: "/risk-test-lab", ic: "⊟", label: "Risk Test Lab", hint: "A/B sur weights", badge: "new" },
      { href: "/detection-studio", ic: "✦", label: "Detection Studio", hint: "Composer ses règles", badge: "new" },
      { href: "/fraud-case-360/CASE-APP-BANK-001", ic: "◎", label: "Fraud Case 360", hint: "Dossier complet", badge: "new" },
      { href: "/risk-docs", ic: "≡", label: "Risk Docs", hint: "Templates & exports", badge: "new" },
    ],
  },
  {
    title: "Investigation",
    code: "03",
    items: [
      { href: "/cases", ic: "▣", label: "Dossiers", hint: "Cases en cours", badge: "risk" },
      { href: "/vendors", ic: "◫", label: "Fournisseurs", hint: "Master data" },
      { href: "/alerts", ic: "!", label: "Alertes", hint: "Stream temps réel" },
      { href: "/collab", ic: "⌘", label: "Collaboration", hint: "4-eyes review" },
    ],
  },
  {
    title: "Contrôles",
    code: "04",
    items: [
      { href: "/anomalies", ic: "△", label: "Anomalies", hint: "Isolation Forest" },
      { href: "/duplicates", ic: "□", label: "Doublons", hint: "Fuzzy matching" },
      { href: "/structuring", ic: "⌒", label: "Sous-seuils", hint: "Fractionnement" },
      { href: "/sanctions", ic: "✕", label: "Sanctions", hint: "OFAC · OpenSanctions", badge: "risk" },
      { href: "/rings", ic: "◇", label: "Anneaux IBAN", hint: "Graphe NetworkX" },
      { href: "/score", ic: "Σ", label: "Risk Score", hint: "Pondération" },
    ],
  },
  {
    title: "Données",
    code: "05",
    items: [
      { href: "/upload", ic: "↥", label: "Upload", hint: "Excel · CSV · SAP" },
      { href: "/sirene", ic: "✓", label: "Sirene", hint: "API INSEE v3", badge: "live" },
      { href: "/decp-rbe", ic: "✓", label: "DECP · RBE", hint: "Marchés publics", badge: "live" },
      { href: "/master-history", ic: "↺", label: "Master History", hint: "Diff vendor master" },
    ],
  },
  {
    title: "Gouvernance",
    code: "06",
    items: [
      { href: "/methodology", ic: "§", label: "Méthodologie", hint: "ISA 240 · AS 2401" },
      { href: "/audit", ic: "✓", label: "Audit log", hint: "Ed25519 signé" },
      { href: "/exports", ic: "↓", label: "Exports", hint: "XLSX · Parquet" },
      { href: "/governance", ic: "★", label: "Trust center", hint: "RGPD · DORA" },
    ],
  },
];

export const HOME_ANCHORS = [
  "hero", "acte-i", "piece-1", "acte-ii", "pipeline",
  "anatomy", "score", "evlog", "toolmap", "refs", "trust",
];
