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
  "nav.section_workbench": { fr: "Workbench P2P", en: "P2P Workbench" },
  "nav.section_investigation": { fr: "Investigation", en: "Investigation" },
  "nav.section_controls": { fr: "Controles", en: "Controls" },
  "nav.section_data": { fr: "Donnees", en: "Data" },
  "nav.section_governance": { fr: "Gouvernance", en: "Governance" },
  "nav.section_ecosystem": { fr: "Ecosysteme & marches", en: "Ecosystem & markets" },
  "nav.ghost_vendor": { fr: "Ghost vendor", en: "Ghost vendor" },
  "nav.conflicts": { fr: "Conflits d'interets", en: "Conflicts of interest" },
  "nav.connectors": { fr: "Connecteurs", en: "Connectors" },
  "nav.secteur_public": { fr: "Secteur public", en: "Public sector" },
  "nav.cac_partner": { fr: "CAC Partner", en: "Audit partner" },
  "nav.fnc_rf": { fr: "FNC-RF & VoP", en: "FNC-RF & VoP" },
  "nav.home": { fr: "Accueil", en: "Home" },
  "nav.cockpit": { fr: "Cockpit", en: "Cockpit" },
  "nav.tour": { fr: "Demo guidee", en: "Guided demo" },
  "nav.sandbox": { fr: "Scenarios fraude", en: "Fraud scenarios" },
  "nav.p2p_scenarios": { fr: "Scenarios P2P", en: "P2P scenarios" },
  "nav.risk_test_lab": { fr: "Test Lab", en: "Test Lab" },
  "nav.risk_lab_sepa": { fr: "Risk Lab SEPA", en: "Risk Lab SEPA" },
  "nav.case_360": { fr: "Fraud Case 360", en: "Fraud Case 360" },
  "nav.risk_docs": { fr: "Docs & glossaire", en: "Docs & glossary" },
  "nav.cases": { fr: "File d'investigation", en: "Investigation queue" },
  "nav.cases_mobile": { fr: "Cases", en: "Cases" },
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
  "nav.detection_studio": { fr: "Detection Studio", en: "Detection Studio" },
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
  "shell.search_label": {
    fr: "Recherche globale dans la demo",
    en: "Global demo search",
  },
  "shell.search_no_results": {
    fr: "Aucun resultat. Essayez case, P2P, IBAN, score ou sanctions.",
    en: "No result. Try case, P2P, IBAN, score or sanctions.",
  },
  "shell.public_sources": {
    fr: "Sources publiques actives",
    en: "Public sources active",
  },
  "shell.toggle_theme": { fr: "Changer de theme", en: "Toggle theme" },
  "shell.request_demo": { fr: "Lancer la demo", en: "Launch demo" },
  "shell.brand_subtitle": { fr: "Command Center", en: "Command Center" },
  "shell.priority_risk": { fr: "Risque prioritaire", en: "Priority risk" },
  "shell.vendor_score": { fr: "Score fournisseur", en: "Vendor score" },
  "shell.audit_signed": { fr: "Audit signe", en: "Signed audit" },
  "shell.badge_live": { fr: "Live", en: "Live" },
  "shell.badge_risk": { fr: "Risque", en: "Risk" },
  "shell.badge_new": { fr: "Demo", en: "Demo" },
  "dashboard.kicker": {
    fr: "Cockpit P2P · vue consolidee",
    en: "P2P cockpit · consolidated view",
  },
  "dashboard.title": { fr: "Cockpit risque P2P", en: "P2P risk cockpit" },
  "dashboard.description": {
    fr: "Vue consolidee des risques fournisseurs, triee par exposition financiere et prete pour la decision audit.",
    en: "Consolidated vendor risk view, sorted by financial exposure and ready for audit decisioning.",
  },
  "dashboard.analyze_scenario": {
    fr: "Analyser un scenario",
    en: "Analyze scenario",
  },
  "dashboard.prepare_export": {
    fr: "Preparer l'export",
    en: "Prepare export",
  },
  "dashboard.backend_unavailable_title": {
    fr: "Backend indisponible",
    en: "Backend unavailable",
  },
  "dashboard.backend_unavailable_body": {
    fr: "Les KPI live ne sont pas accessibles. Vous pouvez tout de meme lancer une demo synthetique pour explorer le parcours.",
    en: "Live KPIs are not available. You can still launch a synthetic demo to explore the workflow.",
  },
  "dashboard.launch_sandbox": {
    fr: "Lancer la sandbox",
    en: "Launch sandbox",
  },
  "dashboard.top_vendors_title": {
    fr: "Top fournisseurs par exposition",
    en: "Top vendors by exposure",
  },
  "dashboard.top_vendors_subtitle": {
    fr: "Le tri favorise l'impact financier, pas seulement le score brut.",
    en: "Ranking favors financial impact, not only the raw score.",
  },
  "dashboard.vendors_unloaded_title": {
    fr: "Fournisseurs non charges",
    en: "Vendors not loaded",
  },
  "dashboard.vendors_unloaded_body": {
    fr: "Verifiez la variable NEXT_PUBLIC_API_URL ou explorez un scenario precharge.",
    en: "Check NEXT_PUBLIC_API_URL or explore a preloaded scenario.",
  },
  "dashboard.view_scenarios": {
    fr: "Voir les scenarios",
    en: "View scenarios",
  },
  "dashboard.priority_kicker": {
    fr: "Priorite du jour",
    en: "Today's priority",
  },
  "dashboard.priority_title": {
    fr: "Reduire l'exposition critique",
    en: "Reduce critical exposure",
  },
  "dashboard.priority_body": {
    fr: "Traitez d'abord les fournisseurs a criticite maximale avec retard SLA ou absence d'assignation. Chaque case doit produire une preuve d'audit exploitable.",
    en: "Prioritize maximum-criticality vendors with SLA delays or missing assignment. Every case must produce usable audit evidence.",
  },
  "dashboard.next_action": { fr: "Next action", en: "Next action" },
  "dashboard.assign_reviewer": {
    fr: "Assigner reviewer",
    en: "Assign reviewer",
  },
  "dashboard.evidence": { fr: "Preuve", en: "Evidence" },
  "dashboard.audit_trail": { fr: "Audit trail", en: "Audit trail" },
  "dashboard.kpi_total_exposure": {
    fr: "Exposition totale",
    en: "Total exposure",
  },
  "dashboard.kpi_critical_exposure": {
    fr: "Exposition critique",
    en: "Critical exposure",
  },
  "dashboard.kpi_open_cases": {
    fr: "Cases ouverts",
    en: "Open cases",
  },
  "dashboard.kpi_sla_delays": {
    fr: "Retards SLA",
    en: "SLA delays",
  },
  "dashboard.kpi_unassigned": {
    fr: "{count} non assignes",
    en: "{count} unassigned",
  },
  "dashboard.trend_created": {
    fr: "Cases crees",
    en: "Cases created",
  },
  "dashboard.trend_closed": {
    fr: "Cases clotures",
    en: "Cases closed",
  },
  "dashboard.trend_critical_alerts": {
    fr: "Alertes critiques",
    en: "Critical alerts",
  },
  "dashboard.trend_audit_activity": {
    fr: "Activite audit",
    en: "Audit activity",
  },
  "dashboard.trend_window": {
    fr: "Tendance 30 jours",
    en: "30-day trend",
  },
  "dashboard.breakdown_unavailable_title": {
    fr: "Breakdown demo indisponible",
    en: "Demo breakdown unavailable",
  },
  "dashboard.breakdown_unavailable_body": {
    fr: "Les metriques statiques du graphe ne sont pas accessibles pour le moment.",
    en: "Static graph metrics are not available right now.",
  },
  "dashboard.open_graph": { fr: "Ouvrir le graphe", en: "Open graph" },
  "dashboard.vercel_demo": { fr: "Demo Vercel", en: "Vercel demo" },
  "dashboard.signal_breakdown": {
    fr: "Repartition des signaux",
    en: "Signal breakdown",
  },
  "dashboard.explore_graph": {
    fr: "Explorer le graphe",
    en: "Explore graph",
  },
  "dashboard.recommended_path": {
    fr: "Parcours recommande",
    en: "Recommended path",
  },
  "dashboard.step_qualify_title": {
    fr: "Qualifier la case",
    en: "Qualify the case",
  },
  "dashboard.step_qualify_body": {
    fr: "Verifier score, source et exposition.",
    en: "Check score, source and exposure.",
  },
  "dashboard.step_vendor_title": {
    fr: "Ouvrir fournisseur 360",
    en: "Open Vendor 360",
  },
  "dashboard.step_vendor_body": {
    fr: "Valider liens SIREN, IBAN et historique.",
    en: "Validate SIREN, IBAN and history links.",
  },
  "dashboard.step_export_title": {
    fr: "Exporter la preuve",
    en: "Export evidence",
  },
  "dashboard.step_export_body": {
    fr: "Signer et archiver la piste d'audit.",
    en: "Sign and archive the audit trail.",
  },
  "dashboard.empty_findings_title": {
    fr: "Aucun finding charge",
    en: "No findings loaded",
  },
  "dashboard.empty_findings_body": {
    fr: "Le Top 10 se calcule sur les findings de la session. Lancez un scenario synthetique pour voir le cockpit rempli.",
    en: "The Top 10 is calculated from session findings. Launch a synthetic scenario to populate the cockpit.",
  },
  "dashboard.table_vendor": { fr: "Fournisseur", en: "Vendor" },
  "dashboard.table_exposure": { fr: "Exposition", en: "Exposure" },
  "dashboard.table_findings": { fr: "Findings", en: "Findings" },
  "dashboard.table_severity": { fr: "Severite", en: "Severity" },
  "dashboard.table_action": { fr: "Action", en: "Action" },
  "dashboard.open_360": { fr: "Ouvrir 360", en: "Open 360" },
  "dashboard.retry": { fr: "Reessayer", en: "Retry" },
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
