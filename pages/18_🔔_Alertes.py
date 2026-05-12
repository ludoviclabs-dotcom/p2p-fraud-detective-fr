"""Page Alertes — configuration canaux (Slack/Teams/SMTP) + règles + historique."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from p2p_fraud.alerts import (
    AlertRule,
    AlertStore,
    SlackWebhook,
    SMTPChannel,
    TeamsWebhook,
    evaluate_rules,
)
from p2p_fraud.streamlit_theme import init_page

init_page(
    title="Alertes & monitoring",
    surtitle="Pilotage",
    kicker="Slack · Teams · SMTP — règles, dispatch et historique",
)
st.caption(
    "Configure les canaux d'alerte (Slack, Microsoft Teams, SMTP), définis les règles "
    "de déclenchement (sévérité, exposition €, détecteur) et consulte l'historique "
    "complet des notifications envoyées."
)

with st.expander("ℹ️ Modèle d'opération"):
    st.markdown(
        """
        - **Mode démo / dev** : déclenchement manuel via le bouton « Évaluer maintenant ».
        - **Mode production** : programmer un cron daily via Docker (image `p2pfd_api`)
          ou un systemd timer qui appelle l'API `POST /detect`. Un démarrage APScheduler
          intégré est disponible pour les déploiements long-running.
        - **Persistance** : les alertes envoyées sont journalisées dans SQLite
          (`alerts.db`). L'historique est conservé sans limite — purge manuelle requise.
        """
    )


@st.cache_resource
def _store() -> AlertStore:
    return AlertStore("alerts.db")


store = _store()

if "alert_rules" not in st.session_state:
    st.session_state["alert_rules"] = [
        AlertRule(
            name="Sanctions CRITICAL",
            severity_threshold="critical",
            detector_filter=["sanctions", "decp_rbe"],
            channels=["slack"],
            enabled=True,
        ),
        AlertRule(
            name="Master data BEC HIGH+",
            severity_threshold="high",
            detector_filter=["master_data"],
            exposure_min_eur=10_000.0,
            channels=["teams"],
            enabled=True,
        ),
        AlertRule(
            name="Doublons & seuils HIGH (exposition > 50 k€)",
            severity_threshold="high",
            detector_filter=["duplicates", "thresholds"],
            exposure_min_eur=50_000.0,
            channels=["slack", "teams"],
            enabled=True,
        ),
    ]

if "alert_channels" not in st.session_state:
    st.session_state["alert_channels"] = {}

st.divider()
st.subheader("📡 Canaux d'alerte")

tab_slack, tab_teams, tab_smtp, tab_webhook = st.tabs(
    ["Slack Webhook", "Microsoft Teams", "SMTP (email)", "🔗 Webhook B2B (CloudEvents)"]
)

with tab_slack:
    slack_url = st.text_input(
        "Slack Incoming Webhook URL",
        type="password",
        value=st.session_state.get("slack_webhook_url", ""),
        help="Créer un webhook : https://api.slack.com/messaging/webhooks",
    )
    if slack_url:
        st.session_state["slack_webhook_url"] = slack_url
        st.session_state["alert_channels"]["slack"] = SlackWebhook(url=slack_url)
        st.success("✅ Canal Slack configuré.")
    if st.button("📤 Envoyer un test Slack", key="test_slack") and slack_url:
        ch = SlackWebhook(url=slack_url)
        ok = ch.send(
            title="Test P2P Fraud Detective FR",
            body="Ceci est un message de test. Si vous voyez ce message, le canal est correctement configuré.",
            severity="low",
            metadata={"environnement": "démo", "version": "0.3.0"},
        )
        st.toast("✅ Envoyé" if ok else "❌ Échec", icon="✅" if ok else "❌")

with tab_teams:
    teams_url = st.text_input(
        "Microsoft Teams Incoming Webhook URL",
        type="password",
        value=st.session_state.get("teams_webhook_url", ""),
        help="Créer un webhook : Apps > Incoming Webhook dans le canal cible.",
    )
    if teams_url:
        st.session_state["teams_webhook_url"] = teams_url
        st.session_state["alert_channels"]["teams"] = TeamsWebhook(url=teams_url)
        st.success("✅ Canal Teams configuré.")
    if st.button("📤 Envoyer un test Teams", key="test_teams") and teams_url:
        ch = TeamsWebhook(url=teams_url)
        ok = ch.send(
            title="Test P2P Fraud Detective FR",
            body="Ceci est un message de test. Si vous voyez ce message, le canal est correctement configuré.",
            severity="low",
            metadata={"environnement": "démo", "version": "0.3.0"},
        )
        st.toast("✅ Envoyé" if ok else "❌ Échec", icon="✅" if ok else "❌")

with tab_smtp:
    c1, c2 = st.columns(2)
    smtp_host = c1.text_input("SMTP host", value=st.session_state.get("smtp_host", ""))
    smtp_port = c2.number_input(
        "SMTP port", min_value=1, max_value=65535, value=st.session_state.get("smtp_port", 587)
    )
    c3, c4 = st.columns(2)
    smtp_user = c3.text_input("Username", value=st.session_state.get("smtp_user", ""))
    smtp_pass = c4.text_input("Password", type="password")
    smtp_from = st.text_input(
        "From address", value=st.session_state.get("smtp_from", "alerts@p2p-fraud.local")
    )
    smtp_to = st.text_input(
        "To addresses (séparées par des virgules)",
        value=st.session_state.get("smtp_to", ""),
    )
    smtp_tls = st.checkbox("Utiliser STARTTLS", value=True)

    if st.button("💾 Enregistrer SMTP", key="save_smtp") and smtp_host and smtp_to:
        st.session_state["smtp_host"] = smtp_host
        st.session_state["smtp_port"] = int(smtp_port)
        st.session_state["smtp_user"] = smtp_user
        st.session_state["smtp_from"] = smtp_from
        st.session_state["smtp_to"] = smtp_to
        st.session_state["alert_channels"]["smtp"] = SMTPChannel(
            host=smtp_host,
            port=int(smtp_port),
            username=smtp_user,
            password=smtp_pass,
            from_addr=smtp_from,
            to_addrs=[a.strip() for a in smtp_to.split(",") if a.strip()],
            use_tls=smtp_tls,
        )
        st.success("✅ Canal SMTP configuré.")

# ─── Webhook B2B sortant (P5-3) ───────────────────────────────────────────────
with tab_webhook:
    from p2p_fraud.config import get_settings
    from p2p_fraud.webhooks.dispatcher import (
        WebhookDeliveryError,
        WebhookDispatcher,
    )
    from p2p_fraud.webhooks.events import WebhookEventKind, build_test_event

    _settings_wh = get_settings()
    st.markdown(
        """
        **Webhook sortant CloudEvents v1.0 simplifié** — émet automatiquement
        un POST signé HMAC-SHA256 vers votre SIEM / ERP / SOC à chaque événement
        `case.created`, `case.assigned`, `case.commented`, `case.evidence_attached`,
        `case.escalated`, `case.status_changed`, `case.closed`.

        En-tête de signature : `X-P2PFD-Signature: sha256=<hex>`. Le récepteur
        valide via la fonction `verify_signature()` documentée dans
        [`src/p2p_fraud/webhooks/dispatcher.py`](https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/blob/main/src/p2p_fraud/webhooks/dispatcher.py).

        Retry exponentiel via `tenacity` : 3 tentatives, backoff 1s → 2s → 4s,
        retryable uniquement sur erreurs réseau (timeout, 5xx). Les 4xx
        signalent une erreur de configuration côté destinataire et ne sont
        pas re-tentés.
        """
    )
    if _settings_wh.webhook_url:
        st.success(
            f"✅ Webhook configuré : `{_settings_wh.webhook_url}` "
            f"(timeout {_settings_wh.webhook_timeout}s, "
            f"secret {'défini' if _settings_wh.webhook_secret else 'non défini (signatures désactivées)'})."
        )
    else:
        st.info(
            "🔬 Webhook désactivé. Pour activer en pilote, définir "
            "`WEBHOOK_URL=https://siem.votre-domaine.fr/p2pfd` "
            "et `WEBHOOK_SECRET=...` côté FastAPI."
        )

    st.markdown("#### 🧪 Tester la configuration")
    if st.button("Envoyer un événement `webhook.test`", type="primary"):
        if not _settings_wh.webhook_url:
            st.warning("Aucun `WEBHOOK_URL` configuré — rien à tester.")
        else:
            dispatcher_test = WebhookDispatcher(
                url=_settings_wh.webhook_url,
                secret=_settings_wh.webhook_secret,
                timeout=_settings_wh.webhook_timeout,
            )
            try:
                result = dispatcher_test.dispatch(build_test_event(actor="streamlit-ui"))
                if result.get("ok"):
                    st.success(
                        f"✅ Reçu : HTTP {result['status']} en {result.get('duration_ms', '?')} ms."
                    )
                else:
                    st.error(f"❌ Échec : {result}")
            except WebhookDeliveryError as exc:
                st.error(f"❌ Livraison échouée après retries : {exc}")

    st.markdown("#### 📜 8 événements émis automatiquement")
    st.dataframe(
        [{"type": ev.value} for ev in WebhookEventKind],
        hide_index=True,
        use_container_width=True,
    )

st.divider()
st.subheader("📋 Règles d'alerte")

rules: list[AlertRule] = st.session_state["alert_rules"]
df_rules = pd.DataFrame(
    [
        {
            "name": r.name,
            "severity_threshold": r.severity_threshold,
            "detectors": ", ".join(r.detector_filter or ["*"]),
            "exposure_min_eur": r.exposure_min_eur,
            "channels": ", ".join(r.channels) or "(par défaut)",
            "enabled": r.enabled,
        }
        for r in rules
    ]
)
st.dataframe(df_rules, use_container_width=True, height=200)

with st.expander("➕ Ajouter une règle"):
    c1, c2 = st.columns(2)
    new_name = c1.text_input("Nom de la règle", key="new_rule_name")
    new_sev = c2.selectbox(
        "Sévérité minimale", ["low", "medium", "high", "critical"], index=2, key="new_rule_sev"
    )
    c3, c4 = st.columns(2)
    new_dets = c3.multiselect(
        "Détecteurs (vide = tous)",
        ["master_data", "sanctions", "duplicates", "thresholds", "sirene", "decp_rbe"],
        key="new_rule_dets",
    )
    new_exp = c4.number_input(
        "Exposition minimale (€, 0 = aucune)", min_value=0, value=0, key="new_rule_exp"
    )
    new_chans = st.multiselect(
        "Canaux", ["slack", "teams", "smtp"], default=["slack"], key="new_rule_chans"
    )
    if st.button("✅ Créer la règle", key="add_rule") and new_name:
        rules.append(
            AlertRule(
                name=new_name,
                severity_threshold=new_sev,
                detector_filter=new_dets or None,
                exposure_min_eur=float(new_exp) if new_exp > 0 else None,
                channels=new_chans,
                enabled=True,
            )
        )
        st.session_state["alert_rules"] = rules
        st.success(f"Règle « {new_name} » ajoutée.")
        st.rerun()

st.divider()
st.subheader("🚀 Évaluation manuelle")

findings_keys = (
    "findings_master_data",
    "findings_sanctions",
    "findings_duplicates",
    "findings_thresholds",
    "findings_sirene",
    "findings_decp_rbe",
)

session_findings = []
for k in findings_keys:
    v = st.session_state.get(k)
    if v:
        session_findings.extend(v)

st.write(
    f"**{len(session_findings)} finding(s)** disponible(s) en session. "
    f"**{len(st.session_state['alert_channels'])} canal/canaux** configuré(s)."
)

if st.button("🔔 Évaluer les règles maintenant", type="primary", disabled=not session_findings):
    alerts = evaluate_rules(session_findings, rules)
    st.write(f"**{len(alerts)} alerte(s) déclenchée(s).**")

    delivered = 0
    failed = 0
    channels = st.session_state["alert_channels"]

    for alert in alerts:
        rule = next((r for r in rules if r.name == alert.rule_name), None)
        target = rule.channels if rule else list(channels.keys())
        for ch_name in target:
            ch = channels.get(ch_name)
            if ch is None:
                store.record(alert, channel=ch_name, delivered=False)
                failed += 1
                continue
            try:
                ok = ch.send(
                    title=alert.title,
                    body=alert.body,
                    severity=alert.severity,
                    metadata=alert.metadata,
                )
            except (ConnectionError, TimeoutError, OSError):
                ok = False
            store.record(alert, channel=ch_name, delivered=ok)
            if ok:
                delivered += 1
            else:
                failed += 1

    if alerts:
        st.success(f"✅ {delivered} alerte(s) livrée(s) · ❌ {failed} échec(s).")

st.divider()
st.subheader("📜 Historique des alertes")

stats = store.stats()
c1, c2, c3 = st.columns(3)
c1.metric("Total alertes", stats["total"])
c2.metric("CRITICAL", stats["by_severity"].get("critical", 0))
c3.metric("HIGH", stats["by_severity"].get("high", 0))

history = store.all(limit=200)
if history:
    df_hist = pd.DataFrame(
        [
            {
                "seq": h.seq,
                "triggered_at": h.triggered_at,
                "rule_name": h.rule_name,
                "severity": h.severity,
                "channel": h.channel,
                "delivered": "✅" if h.delivered else "❌",
                "title": h.title,
            }
            for h in history
        ]
    )
    st.dataframe(df_hist, use_container_width=True, height=320)

    if st.button("⬇️ Exporter l'historique (JSONL)"):
        st.download_button(
            "Télécharger alerts_history.jsonl",
            data="\n".join(store.export_jsonl()),
            file_name="alerts_history.jsonl",
            mime="application/jsonl",
        )
else:
    st.info("Aucune alerte dans l'historique.")
