"""Registre des connecteurs externes — statut unique, calculé depuis Settings.

Source de vérité pour la page `/connecteurs` du frontend et l'endpoint
``GET /api/v1/connectors``. Chaque connecteur déclare :

- son **statut** effectif, dérivé des variables d'environnement :
  - ``actif``          — opérationnel dans le mode courant (démo embarquée ou live) ;
  - ``disponible``     — implémenté, activable par configuration (env vars listées) ;
  - ``config_requise`` — implémenté, inerte tant que la variable n'est pas posée ;
  - ``en_attente_api`` — emplacement réservé, l'API amont n'est pas encore
    ouverte (ex. FNC-RF, réservé aux PSP à ce jour) ;
  - ``roadmap``        — emplacement réservé, client non implémenté.
- ses **variables d'environnement** (l'« emplacement » du connecteur) ;
- les **signaux alimentés** (détecteurs/pages produit).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from p2p_fraud.config import Settings, get_settings


@dataclass(frozen=True)
class ConnectorInfo:
    """Fiche d'un connecteur externe, prête à sérialiser."""

    id: str
    name: str
    category: str  # registres | marches_publics | sanctions | bancaire | notifications
    description: str
    status: str  # actif | disponible | config_requise | en_attente_api | roadmap
    mode: str  # demo | live | slot
    env_vars: list[str] = field(default_factory=list)
    signals: list[str] = field(default_factory=list)
    docs_url: str = ""


def list_connectors(settings: Settings | None = None) -> list[ConnectorInfo]:
    """Construit le registre complet avec statuts calculés depuis l'environnement."""
    s = settings or get_settings()
    live = s.enrichment_mode == "live"

    return [
        # ── Registres d'entreprises ──────────────────────────────────────────
        ConnectorInfo(
            id="sirene",
            name="INSEE Sirene v3",
            category="registres",
            description=(
                "Existence légale et état administratif des unités : cross-check "
                "SIREN à l'import et sur chaque fiche fournisseur."
            ),
            status="actif",
            mode="live" if (live and s.sirene_api_token) else "demo",
            env_vars=["SIRENE_API_TOKEN", "ENRICHMENT_MODE"],
            signals=["shell_companies", "ghost_vendor", "/sirene"],
            docs_url="https://api.insee.fr/catalogue/",
        ),
        ConnectorInfo(
            id="pappers_rbe",
            name="Pappers · RBE (bénéficiaires effectifs)",
            category="registres",
            description=(
                "Bénéficiaires effectifs et dirigeants (RNE consolidé). Un changement "
                "de bénéficiaire effectif est un signal de risque master data."
            ),
            status="actif" if s.pappers_api_key else "disponible",
            mode="live" if s.pappers_api_key else "demo",
            env_vars=["P2PFD_PAPPERS_API_KEY", "PAPPERS_BASE_URL"],
            signals=["network_rings", "conflicts_of_interest", "/decp-rbe"],
            docs_url="https://www.pappers.fr/api/documentation",
        ),
        ConnectorInfo(
            id="bodacc",
            name="Bodacc (procédures collectives)",
            category="registres",
            description=(
                "Sauvegarde, redressement, liquidation : une procédure collective "
                "récente sur un fournisseur actif est un signal critique."
            ),
            status="actif",
            mode="live" if live else "demo",
            env_vars=["BODACC_BASE_URL", "ENRICHMENT_MODE"],
            signals=["shell_companies", "score_explorer"],
            docs_url="https://bodacc-datadila.opendatasoft.com/explore/dataset/annonces-commerciales/",
        ),
        # ── Marchés publics ──────────────────────────────────────────────────
        ConnectorInfo(
            id="decp",
            name="DECP (données essentielles de la commande publique)",
            category="marches_publics",
            description=(
                "Historique des marchés attribués : concentration anormale, "
                "fournisseur sans marché formalisé, croisement favoritisme."
            ),
            status="actif",
            mode="live" if live else "demo",
            env_vars=["DECP_LIVE_BASE_URL", "DECP_PARQUET_PATH", "ENRICHMENT_MODE"],
            signals=["under_thresholds", "/decp-rbe", "/structuring"],
            docs_url="https://data.economie.gouv.fr/explore/dataset/decp_augmente/",
        ),
        ConnectorInfo(
            id="chorus_pro",
            name="Chorus Pro (facturation électronique publique)",
            category="marches_publics",
            description=(
                "Flux Factur-X structuré des entités publiques (AIFE) — ingestion "
                "directe des factures dans le pipeline de détection. Emplacement réservé."
            ),
            status="roadmap",
            mode="slot",
            env_vars=["CHORUS_PRO_API_URL", "CHORUS_PRO_API_KEY"],
            signals=["ingestion secteur public", "/secteur-public"],
            docs_url="https://developer.aife.economie.gouv.fr",
        ),
        # ── Sanctions & conformité ───────────────────────────────────────────
        ConnectorInfo(
            id="opensanctions",
            name="OpenSanctions · Yente (OFAC, UE, Trésor FR)",
            category="sanctions",
            description=(
                "Matching fuzzy multi-listes (SDN, UE consolidée, gels Trésor FR) "
                "sur raisons sociales et bénéficiaires effectifs."
            ),
            status="actif",
            mode="live" if live else "demo",
            env_vars=["YENTE_BASE_URL", "ENRICHMENT_MODE"],
            signals=["sanctions", "pep", "/sanctions"],
            docs_url="https://www.opensanctions.org/docs/api/",
        ),
        # ── Couche bancaire (complémentarité aval) ───────────────────────────
        ConnectorInfo(
            id="fnc_rf",
            name="FNC-RF · Banque de France (IBAN frauduleux)",
            category="bancaire",
            description=(
                "Fichier national commun de la relation frauduleuse (7 mai 2026) : "
                "IBAN frauduleux partagés entre PSP. API réservée aux PSP à ce jour — "
                "l'interface est prête, le connecteur s'activera à l'ouverture."
            ),
            status="actif" if s.fnc_rf_api_url else "en_attente_api",
            mode="live" if s.fnc_rf_api_url else "slot",
            env_vars=["FNC_RF_API_URL", "FNC_RF_API_KEY"],
            signals=["master_data_changes", "/master-history", "/fnc-rf-fraude-iban"],
            docs_url="https://www.banque-france.fr/fr/communiques-de-presse/lancement-de-la-plateforme-des-iban-suspects-un-nouvel-outil-cle-de-lutte-contre-la-fraude-aux",
        ),
        ConnectorInfo(
            id="vop",
            name="VoP · Verification of Payee (IPR 2024/886)",
            category="bancaire",
            description=(
                "Pré-check nom ↔ IBAN à la saisie du RIB, avant que le virement "
                "n'atteigne la couche VoP du PSP. Simulation locale sans prestataire ; "
                "bascule sur prestataire (SEPAmail Diamond, Swift PMPC…) par config."
            ),
            status="actif" if s.vop_provider_url else "disponible",
            mode="live" if s.vop_provider_url else "demo",
            env_vars=["VOP_PROVIDER_URL", "VOP_PROVIDER_KEY"],
            signals=["master_data_changes", "pré-check saisie RIB"],
            docs_url="https://www.europeanpaymentscouncil.eu/what-we-do/other-schemes/verification-payee",
        ),
        # ── Notifications & alertes push ─────────────────────────────────────
        ConnectorInfo(
            id="slack",
            name="Slack (Incoming Webhook)",
            category="notifications",
            description="Alerte push sur déclenchement de détecteur critique.",
            status="actif" if s.slack_webhook_url else "config_requise",
            mode="live" if s.slack_webhook_url else "slot",
            env_vars=["SLACK_WEBHOOK_URL"],
            signals=["alertes findings CRITICAL/HIGH", "/alerts"],
            docs_url="https://api.slack.com/messaging/webhooks",
        ),
        ConnectorInfo(
            id="teams",
            name="Microsoft Teams (Incoming Webhook)",
            category="notifications",
            description="Alerte push MessageCard vers un canal Teams.",
            status="actif" if s.teams_webhook_url else "config_requise",
            mode="live" if s.teams_webhook_url else "slot",
            env_vars=["TEAMS_WEBHOOK_URL"],
            signals=["alertes findings CRITICAL/HIGH", "/alerts"],
            docs_url="https://learn.microsoft.com/fr-fr/microsoftteams/platform/webhooks-and-connectors/",
        ),
        ConnectorInfo(
            id="smtp",
            name="Email (SMTP)",
            category="notifications",
            description="Alerte email directe (préférer un service transactionnel en prod).",
            status="actif" if s.smtp_host else "config_requise",
            mode="live" if s.smtp_host else "slot",
            env_vars=[
                "SMTP_HOST",
                "SMTP_PORT",
                "SMTP_USERNAME",
                "SMTP_PASSWORD",
                "SMTP_FROM",
                "SMTP_TO",
            ],
            signals=["alertes findings CRITICAL/HIGH", "/alerts"],
            docs_url="",
        ),
        ConnectorInfo(
            id="webhook_siem",
            name="Webhook SIEM signé (HMAC-SHA256)",
            category="notifications",
            description=(
                "Chaque événement case.* est POSTé signé vers le SIEM "
                "(Splunk, Sentinel, Elastic) — retry exponentiel."
            ),
            status="actif" if s.webhook_url else "config_requise",
            mode="live" if s.webhook_url else "slot",
            env_vars=["WEBHOOK_URL", "WEBHOOK_SECRET", "WEBHOOK_TIMEOUT"],
            signals=["événements case.*", "/audit"],
            docs_url="",
        ),
    ]
