export type Locale = "fr" | "en";

export const LOCALE_STORAGE_KEY = "p2pfd_locale";

export type Translations = Record<string, Record<Locale, string>>;

export const TRANSLATIONS: Translations = {
  "common.app_name": {
    fr: "P2P Fraud Detective FR",
    en: "P2P Fraud Detective FR",
  },
  "common.language": { fr: "Langue", en: "Language" },
  "common.loading": { fr: "Chargement...", en: "Loading..." },
  "nav.section_command": { fr: "Command center", en: "Command center" },
  "nav.section_investigation": { fr: "Investigation", en: "Investigation" },
  "nav.section_controls": { fr: "Controles", en: "Controls" },
  "nav.section_data": { fr: "Donnees", en: "Data" },
  "nav.section_governance": { fr: "Gouvernance", en: "Governance" },
  "nav.home": { fr: "Accueil", en: "Home" },
  "nav.cockpit": { fr: "Cockpit", en: "Cockpit" },
  "nav.tour": { fr: "Demo guidee", en: "Guided demo" },
  "nav.sandbox": { fr: "Scenarios fraude", en: "Fraud scenarios" },
  "nav.cases": { fr: "File d'investigation", en: "Investigation queue" },
  "nav.alerts": { fr: "Alertes & monitoring", en: "Alerts & monitoring" },
  "nav.collab": { fr: "Collaboration", en: "Collaboration" },
  "nav.upload": { fr: "Import des donnees", en: "Data import" },
  "nav.master_history": {
    fr: "Historique referentiel",
    en: "Master data history",
  },
  "nav.sirene": { fr: "Controle Sirene", en: "Sirene check" },
  "nav.benford": { fr: "Loi de Benford", en: "Benford's Law" },
  "nav.duplicates": { fr: "Doublons", en: "Duplicates" },
  "nav.structuring": { fr: "Fractionnement", en: "Structuring" },
  "nav.sanctions": { fr: "Sanctions & PEP", en: "Sanctions & PEP" },
  "nav.decp_rbe": { fr: "DECP & RBE INPI", en: "DECP & RBE INPI" },
  "nav.anomalies": { fr: "Anomalies ML", en: "ML anomalies" },
  "nav.rings": { fr: "Anneaux de fraude", en: "Fraud rings" },
  "nav.score": { fr: "Explorateur de score", en: "Score explorer" },
  "nav.findings": { fr: "Findings", en: "Findings" },
  "nav.vendors": { fr: "Fournisseur 360", en: "Vendor 360" },
  "nav.exports": { fr: "Synthese & export", en: "Summary export" },
  "nav.audit": { fr: "Piste d'audit", en: "Audit trail" },
  "nav.methodology": { fr: "Methodologie", en: "Methodology" },
  "nav.governance": { fr: "Conformite", en: "Compliance" },
  "shell.open_nav": { fr: "Ouvrir la navigation", en: "Open navigation" },
  "shell.close_nav": { fr: "Fermer la navigation", en: "Close navigation" },
  "shell.search_placeholder": {
    fr: "Rechercher un SIREN, fournisseur, IBAN, case ou alerte...",
    en: "Search a SIREN, vendor, IBAN, case or alert...",
  },
  "shell.public_sources": {
    fr: "Sources publiques actives",
    en: "Public sources active",
  },
  "shell.toggle_theme": { fr: "Changer de theme", en: "Toggle theme" },
  "shell.request_demo": { fr: "Demander une demo", en: "Request a demo" },
  "shell.brand_subtitle": { fr: "Command Center", en: "Command Center" },
  "shell.priority_risk": { fr: "Risque prioritaire", en: "Priority risk" },
  "shell.vendor_score": { fr: "Score fournisseur", en: "Vendor score" },
  "shell.audit_signed": { fr: "Audit signe", en: "Signed audit" },
  "shell.badge_live": { fr: "Live", en: "Live" },
  "shell.badge_risk": { fr: "Risque", en: "Risk" },
  "shell.badge_new": { fr: "Demo", en: "Demo" },
  "alerts.kicker": { fr: "Pilotage", en: "Operations" },
  "alerts.title": { fr: "Alertes & monitoring", en: "Alerts & monitoring" },
  "alerts.description": {
    fr: "Flux d'evenements depuis l'audit log immutable. La page utilise un flux Server-Sent Events quand FastAPI est configure, puis retombe en polling 5 secondes pour garder la demo Vercel utilisable.",
    en: "Event stream from the immutable audit log. The page uses Server-Sent Events when FastAPI is configured, then falls back to 5-second polling to keep the Vercel demo usable.",
  },
  "alerts.metric_total": {
    fr: "Total events (50 derniers)",
    en: "Total events (last 50)",
  },
  "alerts.metric_critical": { fr: "Critiques", en: "Critical" },
  "alerts.metric_signed": { fr: "Signes Ed25519", en: "Ed25519 signed" },
  "alerts.metric_kinds": { fr: "Types distincts", en: "Distinct types" },
  "alerts.channels_title": {
    fr: "Configuration canaux d'alerte (statut)",
    en: "Alert channel configuration (status)",
  },
  "alerts.channel": { fr: "Canal", en: "Channel" },
  "alerts.status": { fr: "Statut", en: "Status" },
  "alerts.target": { fr: "Cible", en: "Target" },
  "alerts.slack_target": { fr: "canal #fraud-alerts", en: "#fraud-alerts channel" },
  "alerts.teams_target": {
    fr: "Incoming Webhook connector",
    en: "Incoming Webhook connector",
  },
  "alerts.webhook_target": { fr: "SIEM/ERP/SOC (P5-3)", en: "SIEM/ERP/SOC (P5-3)" },
  "alerts.configurable_via": { fr: "Configurable via", en: "Configurable via" },
  "alerts.hmac_signed_via": { fr: "HMAC-SHA256 signe via", en: "HMAC-SHA256 signed via" },
  "alerts.feed_title": { fr: "Flux d'evenements (live)", en: "Event feed (live)" },
  "alerts.connecting": { fr: "Connexion au flux...", en: "Connecting to stream..." },
  "alerts.empty": { fr: "Aucun evenement.", en: "No event." },
  "alerts.cursor": { fr: "curseur replay", en: "replay cursor" },
  "alerts.stream_connecting": { fr: "Connexion SSE...", en: "Connecting SSE..." },
  "alerts.stream_connected": { fr: "SSE connecte", en: "SSE connected" },
  "alerts.stream_active": { fr: "SSE actif", en: "SSE active" },
  "alerts.stream_malformed": {
    fr: "Evenement SSE ignore: payload invalide.",
    en: "SSE event ignored: invalid payload.",
  },
  "alerts.stream_backend_missing": {
    fr: "Backend FastAPI absent, bascule en polling.",
    en: "FastAPI backend missing, switching to polling.",
  },
  "alerts.stream_interrupted": {
    fr: "Flux SSE interrompu, fallback polling.",
    en: "SSE stream interrupted, polling fallback.",
  },
  "alerts.by_actor": { fr: "par", en: "by" },
  "alerts.case": { fr: "case", en: "case" },
  "alerts.ed25519": { fr: "Ed25519", en: "Ed25519" },
  "stream.live_sse": { fr: "Live SSE", en: "Live SSE" },
  "stream.polling_fetching": {
    fr: "Polling - refresh en cours...",
    en: "Polling - refresh in progress...",
  },
  "stream.fallback_polling": {
    fr: "Fallback polling - {seconds}s",
    en: "Polling fallback - {seconds}s",
  },
};

export function translate(
  key: string,
  locale: Locale,
  params: Record<string, string | number> = {},
): string {
  const entry = TRANSLATIONS[key];
  const template = entry?.[locale] ?? entry?.fr ?? key;
  return Object.entries(params).reduce(
    (text, [name, value]) => text.replaceAll(`{${name}}`, String(value)),
    template,
  );
}

export function isLocale(value: string | null): value is Locale {
  return value === "fr" || value === "en";
}
