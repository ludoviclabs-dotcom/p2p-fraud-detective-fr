// Catalogue local des connecteurs (offline-first).
//
// Miroir du registre backend `p2p_fraud/connectors.py` avec les statuts par
// défaut de la démo publique (aucune variable d'environnement posée). Quand le
// backend répond, GET /api/v1/connectors fait foi : ses statuts reflètent
// l'environnement réel et remplacent les statuts locaux (merge par `id`).

import type { ConnectorOut } from "@/lib/api-client";

export const LOCAL_CONNECTORS: ConnectorOut[] = [
  // ── Registres d'entreprises ────────────────────────────────────────────────
  {
    id: "sirene",
    name: "INSEE Sirene v3",
    category: "registres",
    description:
      "Existence légale et état administratif des unités : cross-check SIREN à l'import et sur chaque fiche fournisseur.",
    status: "actif",
    mode: "demo",
    env_vars: ["SIRENE_API_TOKEN", "ENRICHMENT_MODE"],
    signals: ["shell_companies", "ghost_vendor", "/sirene"],
    docs_url: "https://api.insee.fr/catalogue/",
  },
  {
    id: "pappers_rbe",
    name: "Pappers · RBE (bénéficiaires effectifs)",
    category: "registres",
    description:
      "Bénéficiaires effectifs et dirigeants (RNE consolidé). Un changement de bénéficiaire effectif est un signal de risque master data.",
    status: "disponible",
    mode: "demo",
    env_vars: ["P2PFD_PAPPERS_API_KEY", "PAPPERS_BASE_URL"],
    signals: ["network_rings", "conflicts_of_interest", "/decp-rbe"],
    docs_url: "https://www.pappers.fr/api/documentation",
  },
  {
    id: "bodacc",
    name: "Bodacc (procédures collectives)",
    category: "registres",
    description:
      "Sauvegarde, redressement, liquidation : une procédure collective récente sur un fournisseur actif est un signal critique.",
    status: "actif",
    mode: "demo",
    env_vars: ["BODACC_BASE_URL", "ENRICHMENT_MODE"],
    signals: ["shell_companies", "score_explorer"],
    docs_url:
      "https://bodacc-datadila.opendatasoft.com/explore/dataset/annonces-commerciales/",
  },
  // ── Marchés publics ────────────────────────────────────────────────────────
  {
    id: "decp",
    name: "DECP (données essentielles de la commande publique)",
    category: "marches_publics",
    description:
      "Historique des marchés attribués : concentration anormale, fournisseur sans marché formalisé, croisement favoritisme.",
    status: "actif",
    mode: "demo",
    env_vars: ["DECP_LIVE_BASE_URL", "DECP_PARQUET_PATH", "ENRICHMENT_MODE"],
    signals: ["under_thresholds", "/decp-rbe", "/structuring"],
    docs_url: "https://data.economie.gouv.fr/explore/dataset/decp_augmente/",
  },
  {
    id: "chorus_pro",
    name: "Chorus Pro (facturation électronique publique)",
    category: "marches_publics",
    description:
      "Flux Factur-X structuré des entités publiques (AIFE) — ingestion directe des factures dans le pipeline de détection. Emplacement réservé.",
    status: "roadmap",
    mode: "slot",
    env_vars: ["CHORUS_PRO_API_URL", "CHORUS_PRO_API_KEY"],
    signals: ["ingestion secteur public", "/secteur-public"],
    docs_url: "https://developer.aife.economie.gouv.fr",
  },
  // ── Sanctions & conformité ─────────────────────────────────────────────────
  {
    id: "opensanctions",
    name: "OpenSanctions · Yente (OFAC, UE, Trésor FR)",
    category: "sanctions",
    description:
      "Matching fuzzy multi-listes (SDN, UE consolidée, gels Trésor FR) sur raisons sociales et bénéficiaires effectifs.",
    status: "actif",
    mode: "demo",
    env_vars: ["YENTE_BASE_URL", "ENRICHMENT_MODE"],
    signals: ["sanctions", "pep", "/sanctions"],
    docs_url: "https://www.opensanctions.org/docs/api/",
  },
  // ── Couche bancaire (complémentarité aval) ─────────────────────────────────
  {
    id: "fnc_rf",
    name: "FNC-RF · Banque de France (IBAN frauduleux)",
    category: "bancaire",
    description:
      "Fichier national commun de la relation frauduleuse (7 mai 2026) : IBAN frauduleux partagés entre PSP. API réservée aux PSP à ce jour — l'interface est prête, le connecteur s'activera à l'ouverture.",
    status: "en_attente_api",
    mode: "slot",
    env_vars: ["FNC_RF_API_URL", "FNC_RF_API_KEY"],
    signals: ["master_data_changes", "/master-history", "/fnc-rf-fraude-iban"],
    docs_url:
      "https://www.banque-france.fr/fr/communiques-de-presse/lancement-de-la-plateforme-des-iban-suspects-un-nouvel-outil-cle-de-lutte-contre-la-fraude-aux",
  },
  {
    id: "vop",
    name: "VoP · Verification of Payee (IPR 2024/886)",
    category: "bancaire",
    description:
      "Pré-check nom ↔ IBAN à la saisie du RIB, avant que le virement n'atteigne la couche VoP du PSP. Simulation locale sans prestataire ; bascule sur prestataire (SEPAmail Diamond, Swift PMPC…) par config.",
    status: "disponible",
    mode: "demo",
    env_vars: ["VOP_PROVIDER_URL", "VOP_PROVIDER_KEY"],
    signals: ["master_data_changes", "pré-check saisie RIB"],
    docs_url:
      "https://www.europeanpaymentscouncil.eu/what-we-do/other-schemes/verification-payee",
  },
  // ── Notifications & alertes push ───────────────────────────────────────────
  {
    id: "slack",
    name: "Slack (Incoming Webhook)",
    category: "notifications",
    description: "Alerte push sur déclenchement de détecteur critique.",
    status: "config_requise",
    mode: "slot",
    env_vars: ["SLACK_WEBHOOK_URL"],
    signals: ["alertes findings CRITICAL/HIGH", "/alerts"],
    docs_url: "https://api.slack.com/messaging/webhooks",
  },
  {
    id: "teams",
    name: "Microsoft Teams (Incoming Webhook)",
    category: "notifications",
    description: "Alerte push MessageCard vers un canal Teams.",
    status: "config_requise",
    mode: "slot",
    env_vars: ["TEAMS_WEBHOOK_URL"],
    signals: ["alertes findings CRITICAL/HIGH", "/alerts"],
    docs_url:
      "https://learn.microsoft.com/fr-fr/microsoftteams/platform/webhooks-and-connectors/",
  },
  {
    id: "smtp",
    name: "Email (SMTP)",
    category: "notifications",
    description:
      "Alerte email directe (préférer un service transactionnel en prod).",
    status: "config_requise",
    mode: "slot",
    env_vars: ["SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM", "SMTP_TO"],
    signals: ["alertes findings CRITICAL/HIGH", "/alerts"],
    docs_url: "",
  },
  {
    id: "webhook_siem",
    name: "Webhook SIEM signé (HMAC-SHA256)",
    category: "notifications",
    description:
      "Chaque événement case.* est POSTé signé vers le SIEM (Splunk, Sentinel, Elastic) — retry exponentiel.",
    status: "config_requise",
    mode: "slot",
    env_vars: ["WEBHOOK_URL", "WEBHOOK_SECRET", "WEBHOOK_TIMEOUT"],
    signals: ["événements case.*", "/audit"],
    docs_url: "",
  },
];

export const CONNECTOR_CATEGORIES: { id: string; label: string; glyph: string }[] = [
  { id: "registres", label: "Registres d'entreprises", glyph: "▦" },
  { id: "marches_publics", label: "Marchés publics", glyph: "§" },
  { id: "sanctions", label: "Sanctions & conformité", glyph: "✕" },
  { id: "bancaire", label: "Couche bancaire (aval)", glyph: "◫" },
  { id: "notifications", label: "Notifications & alertes push", glyph: "!" },
];

/** Fusionne le catalogue local avec le registre backend (le backend fait foi). */
export function mergeConnectors(api?: import("@/lib/api-client").ConnectorOut[] | null) {
  if (!api || api.length === 0) return LOCAL_CONNECTORS;
  const byId = new Map(LOCAL_CONNECTORS.map((c) => [c.id, c]));
  for (const c of api) byId.set(c.id, c);
  return Array.from(byId.values());
}
