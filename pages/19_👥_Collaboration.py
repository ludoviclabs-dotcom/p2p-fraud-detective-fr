"""Page Collaboration — multi-user, @mentions, SLA configurable, OIDC."""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import requests
import streamlit as st

from p2p_fraud.cases.mentions import extract_mentions
from p2p_fraud.cases.sla import SLAConfig
from p2p_fraud.config import get_settings
from p2p_fraud.i18n import _, init_locale_from_session
from p2p_fraud.security.oidc import OIDCConfig
from p2p_fraud.streamlit_theme import init_page
from pages._helpers import get_case_service

init_locale_from_session()

init_page(
    title=_("nav.page_collab"),
    surtitle=_("nav.surtitle_pilotage"),
    kicker=_("nav.kicker_collab"),
)
st.caption(
    "Configuration de l'équipe d'auditeurs, gestion des @mentions dans les commentaires, "
    "SLA paramétrable par sévérité, authentification fédérée OIDC."
)

service = get_case_service()

# ─── Identité courante ────────────────────────────────────────────────────────
st.divider()
st.subheader("👤 Identité utilisateur")

_settings = get_settings()
_oidc_active = bool(
    _settings.oidc_issuer and _settings.oidc_client_id and _settings.oidc_redirect_uri
)


def _fetch_oidc_identity() -> dict | None:
    """Interroge `GET /oidc/me` via le reverse proxy local (cookie de session partagé)."""
    if not _oidc_active:
        return None
    base = _settings.oidc_redirect_uri.rsplit("/oidc/", 1)[0]
    try:
        r = requests.get(f"{base}/oidc/me", timeout=2.0)
    except requests.RequestException:
        return None
    if r.status_code != 200:
        return None
    return r.json()


_oidc_identity = _fetch_oidc_identity()
if _oidc_identity:
    st.session_state["current_user"] = _oidc_identity.get("username", "").lower()
    st.success(
        f"✅ **Identité OIDC active** — `{_oidc_identity.get('username')}` "
        f"({_oidc_identity.get('email')}) · rôle RBAC : `{_oidc_identity.get('role')}`"
    )
    with st.expander("Claims OIDC reçus"):
        st.json(_oidc_identity)
    st.caption(
        "Identité fournie par votre IdP (Entra ID / Auth0 / Keycloak). "
        "Le champ ci-dessous est verrouillé en lecture seule."
    )
    st.text_input(
        "Nom d'utilisateur (verrouillé OIDC)",
        value=_oidc_identity.get("username", ""),
        disabled=True,
    )
else:
    _saved_user = st.session_state.get("current_user", "")
    new_user = st.text_input(
        "Nom d'utilisateur (utilisé dans les @mentions et l'audit log)",
        value=_saved_user,
        placeholder="ex: jdupont, sbernard, audit.senior",
        help="Format alphanumérique + tirets/underscores. Sera utilisé pour tracer "
        "l'auteur des commentaires et alimenter les notifications @mention.",
        max_chars=40,
    )
    if new_user and new_user != _saved_user:
        st.session_state["current_user"] = new_user.strip().lower()
        st.success(f"✅ Utilisateur courant : `{new_user.strip().lower()}`")
    if _oidc_active:
        st.info(
            "OIDC est configuré côté serveur mais aucune session n'est ouverte. "
            "Cliquez sur **🔑 Se connecter (OIDC)** dans la sidebar pour vous authentifier."
        )

current_user = st.session_state.get("current_user", "")

# ─── SLA configurable ─────────────────────────────────────────────────────────
st.divider()
st.subheader("⏱️ SLA configurable par sévérité")

st.caption(
    "Délai de clôture cible par sévérité. Au-delà, le case est marqué « en retard SLA » "
    "dans le Cockpit. Valeurs alignées sur AMLD6 art. 24 (déclaration sans délai pour CRITICAL)."
)

current_sla: SLAConfig = service.sla
c1, c2, c3, c4 = st.columns(4)
crit_h = c1.number_input(
    "CRITICAL (h)", min_value=1, max_value=720, value=current_sla.critical_hours
)
high_h = c2.number_input("HIGH (h)", min_value=1, max_value=720, value=current_sla.high_hours)
med_h = c3.number_input("MEDIUM (h)", min_value=1, max_value=720, value=current_sla.medium_hours)
low_h = c4.number_input("LOW (h)", min_value=1, max_value=8760, value=current_sla.low_hours)

if st.button("💾 Mettre à jour la SLA", type="primary"):
    new_sla = SLAConfig(
        critical_hours=int(crit_h),
        high_hours=int(high_h),
        medium_hours=int(med_h),
        low_hours=int(low_h),
    )
    service._sla = new_sla
    st.success(
        f"✅ SLA mise à jour — CRITICAL: {crit_h}h, HIGH: {high_h}h, "
        f"MEDIUM: {med_h}h, LOW: {low_h}h."
    )

# ─── @mentions ────────────────────────────────────────────────────────────────
st.divider()
st.subheader("💬 Mentions reçues (@user)")

if not current_user:
    st.info("Saisissez votre nom d'utilisateur ci-dessus pour voir vos mentions.")
else:
    only_unread = st.checkbox("Afficher uniquement les non lues", value=True)
    user_mentions = service.mentions.for_user(current_user, only_unread=only_unread)

    if not user_mentions:
        st.success(f"Aucune mention {'non lue' if only_unread else ''} pour `{current_user}`.")
    else:
        st.write(f"**{len(user_mentions)}** mention(s) {'non lue(s)' if only_unread else ''} :")
        for m in user_mentions[:50]:
            with st.container(border=True):
                col_a, col_b = st.columns([3, 1])
                col_a.markdown(
                    f"**@{m.mentioned_by}** vous a mentionné dans le case "
                    f"`{m.case_id}` ({m.created_at[:19]})"
                )
                col_b.caption(m.case_id)
                st.text(m.text)
        if st.button("✅ Marquer toutes comme lues", key="mark_all_read"):
            n = service.mentions.mark_read(username=current_user)
            st.success(f"{n} mention(s) marquée(s) comme lue(s).")
            st.rerun()

# ─── Test d'extraction @mentions ──────────────────────────────────────────────
st.divider()
st.subheader("🧪 Tester le parsing @mentions")

sample_text = st.text_area(
    "Exemple de commentaire",
    value="Bonjour @sbernard, peux-tu valider cette alerte ? Cc @audit.senior et @jdupont.",
    height=80,
)
extracted = extract_mentions(sample_text)
st.write(f"**Mentions détectées** : {extracted if extracted else '(aucune)'}")

# ─── Vue équipe ───────────────────────────────────────────────────────────────
st.divider()
st.subheader("👥 Équipe d'auditeurs")

cases = service.list_cases()
if cases:
    assignees = sorted(
        {c.assignee for c in cases if c.assignee} | {c.created_by for c in cases if c.created_by}
    )
    df_team = pd.DataFrame(
        [
            {
                "user": user,
                "cases_assigned": sum(
                    1 for c in cases if c.assignee == user and not c.status.is_closed
                ),
                "cases_created": sum(1 for c in cases if c.created_by == user),
                "cases_closed": sum(1 for c in cases if c.assignee == user and c.status.is_closed),
            }
            for user in assignees
        ]
    )
    st.dataframe(df_team, use_container_width=True, height=200)
else:
    st.info("Aucun case en session — l'équipe sera détectée à mesure des assignations.")

# ─── SLA overdue ──────────────────────────────────────────────────────────────
st.divider()
st.subheader("⚠️ Cases en dépassement SLA")

now = datetime.now(UTC)
overdue = []
for c in cases:
    if c.status.is_closed:
        continue
    deadline = service.sla.deadline_for(c.severity, from_dt=c.created_at)
    if deadline < now:
        overdue.append(
            {
                "case_id": c.case_id,
                "severity": c.severity,
                "title": c.title,
                "assignee": c.assignee or "(non assigné)",
                "exposure_eur": c.exposure_eur,
                "created_at": c.created_at.isoformat()
                if hasattr(c.created_at, "isoformat")
                else c.created_at,
                "overdue_hours": int((now - deadline).total_seconds() / 3600),
            }
        )

if overdue:
    st.error(f"🚨 {len(overdue)} case(s) en dépassement SLA")
    df_overdue = pd.DataFrame(overdue).sort_values("overdue_hours", ascending=False)
    st.dataframe(df_overdue, use_container_width=True, height=240)
else:
    st.success("✅ Aucun case en dépassement SLA.")

# ─── OIDC / Microsoft Entra ID ────────────────────────────────────────────────
st.divider()
st.subheader("🔐 Authentification fédérée OIDC")

oidc_cfg = OIDCConfig.from_env()
if oidc_cfg is None:
    st.warning(
        "**OIDC non configuré.** Pour activer l'authentification fédérée Microsoft Entra ID, "
        "Auth0 ou Keycloak, configurez les variables d'environnement suivantes :"
    )
    st.code(
        """
OIDC_ISSUER=https://login.microsoftonline.com/{tenant_id}/v2.0
OIDC_CLIENT_ID=<application_id>
OIDC_CLIENT_SECRET=<application_secret>
OIDC_REDIRECT_URI=https://yourapp.com/oidc/callback
OIDC_SCOPES=openid email profile
OIDC_ROLE_MAP={"DG-Audit":"admin","Audit-Senior":"manager","Audit-Junior":"analyst"}
OIDC_SESSION_SECRET=$(python -c 'import secrets; print(secrets.token_urlsafe(48))')
        """,
        language="bash",
    )
    st.markdown(
        "**Configuration recommandée** : créer une application dans Microsoft Entra ID "
        "avec un redirect URI vers `/oidc/callback` de votre déploiement, configurer les "
        "scopes `openid email profile groups`, et mapper les groupes Entra ID vers les "
        "rôles RBAC via `OIDC_ROLE_MAP`. Le service FastAPI doit être joignable derrière "
        "le même domaine que Streamlit (cookies partagés via reverse proxy)."
    )
else:
    st.success(f"✅ OIDC configuré — issuer : `{oidc_cfg.issuer}`")
    if not _settings.oidc_session_secret:
        st.error(
            "⚠️ `OIDC_SESSION_SECRET` manquant — les endpoints `/oidc/login` et "
            "`/oidc/callback` retourneront 503. Générez un secret de ≥ 32 octets."
        )
    elif _oidc_identity:
        if st.button("🔓 Se déconnecter (OIDC)"):
            base = _settings.oidc_redirect_uri.rsplit("/oidc/", 1)[0]
            try:
                requests.post(f"{base}/oidc/logout", timeout=2.0)
                st.success("Session OIDC fermée. Rechargez la page.")
            except requests.RequestException as exc:
                st.error(f"Logout impossible : {exc}")
    else:
        st.info(
            "OIDC prêt. Cliquez sur **🔑 Se connecter (OIDC)** dans la sidebar pour démarrer le flow."
        )

# ─── Backend persistant ───────────────────────────────────────────────────────
st.divider()
st.subheader("🗄️ Backend de persistance")

st.info(
    "**Mode démo** : SQLite en mémoire (`:memory:`) — données perdues à chaque redémarrage. "
    "**Mode production** : SQLite fichier (`cases.db`) ou PostgreSQL via SQLAlchemy. "
    "Configurer via `FRAUD_CASES_DB` (chemin SQLite) ou `DATABASE_URL` "
    "(`postgresql://user:pass@host:5432/db`)."
)

with st.expander("📚 Migration SQLite → PostgreSQL"):
    st.markdown(
        """
        **Étapes** :
        1. Provisionner une base PostgreSQL 14+ (Aiven, Neon, Supabase, RDS).
        2. Créer le schéma via les migrations Alembic (`alembic/`).
        3. Configurer `DATABASE_URL=postgresql://user:pass@host:5432/p2pfd`.
        4. Migrer les données existantes :
           ```bash
           sqlite3 cases.db ".dump cases" > cases.sql
           # Adapter la syntaxe SQLite → PostgreSQL puis :
           psql $DATABASE_URL < cases.sql
           ```
        5. Redémarrer l'application — `CaseService` détecte le backend via `DATABASE_URL`.

        **Avantages PostgreSQL** :
        - Multi-utilisateurs concurrents (verrous SKIP LOCKED)
        - Recherche fulltext (tsvector) sur titres/commentaires
        - JSONB pour les payloads d'événements
        - Backup point-in-time (PITR)
        - Réplication streaming pour HA
        """
    )
