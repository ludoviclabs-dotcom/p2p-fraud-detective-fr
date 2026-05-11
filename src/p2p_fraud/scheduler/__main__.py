"""CLI scheduler — exécute la détection P2P en single-shot ou long-running.

Trois modes :

1. **Single-shot** (`--once`) : un run de détection puis exit 0 (ou 1 en erreur).
   Idéal pour Cloud Scheduler HTTP / Kubernetes CronJob / cron systemd.

2. **Daily long-running** (`--daily HH:MM`) : APScheduler `BackgroundScheduler`
   qui reste en vie et ré-exécute le run quotidien. Idéal pour un container
   long-lived (Cloud Run min instances=1, Dokku, systemd service).

3. **Health check** (`--health`) : affiche la configuration détectée et exit.

Sources de factures supportées :
- `--invoices PATH` : CSV / Parquet / Excel local.
- *(défaut)* : provider vide → run skip (test de connectivité).

Canaux d'alerte activés via variables d'environnement :
- `SLACK_WEBHOOK_URL`
- `TEAMS_WEBHOOK_URL`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_TO`

Exemples :

    python -m p2p_fraud.scheduler --once --invoices /data/invoices.parquet
    python -m p2p_fraud.scheduler --daily 06:00 --invoices /data/invoices.parquet
    python -m p2p_fraud.scheduler --health

Voir `docs/deployment-cloud-run.md` pour les recettes complètes.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

import pandas as pd

from p2p_fraud.alerts.channels import AlertChannel, SlackWebhook, SMTPChannel, TeamsWebhook
from p2p_fraud.alerts.rules import AlertRule
from p2p_fraud.alerts.store import AlertStore
from p2p_fraud.config import get_settings
from p2p_fraud.logging_setup import configure_logging
from p2p_fraud.scheduler.runner import run_detection_once

log = logging.getLogger("p2p_fraud.scheduler.cli")


# ─── Provider de factures ─────────────────────────────────────────────────────


def _empty_provider() -> pd.DataFrame | None:
    """Provider par défaut — DataFrame vide → run skip."""
    return None


def _file_provider(path: Path):
    """Crée un provider qui charge le fichier à chaque appel (lazy)."""

    def _load() -> pd.DataFrame | None:
        if not path.exists():
            log.warning("Fichier source absent : %s", path)
            return None
        suffix = path.suffix.lower()
        if suffix in {".csv", ".tsv"}:
            return pd.read_csv(path, sep=None, engine="python")
        if suffix == ".parquet":
            return pd.read_parquet(path)
        if suffix in {".xlsx", ".xls"}:
            return pd.read_excel(path)
        log.error("Format non supporté : %s", suffix)
        return None

    return _load


# ─── Channels & rules depuis l'environnement ──────────────────────────────────


def _build_channels() -> dict[str, AlertChannel]:
    """Construit les canaux d'alerte selon les variables d'environnement."""
    s = get_settings()
    channels: dict[str, AlertChannel] = {}

    if s.slack_webhook_url:
        channels["slack"] = SlackWebhook(url=s.slack_webhook_url)
        log.info("Slack channel activé")
    if s.teams_webhook_url:
        channels["teams"] = TeamsWebhook(url=s.teams_webhook_url)
        log.info("Teams channel activé")

    smtp_host = os.environ.get("SMTP_HOST", "")
    if smtp_host:
        channels["smtp"] = SMTPChannel(
            host=smtp_host,
            port=int(os.environ.get("SMTP_PORT", "587")),
            username=os.environ.get("SMTP_USERNAME", ""),
            password=os.environ.get("SMTP_PASSWORD", ""),
            from_addr=os.environ.get("SMTP_FROM", ""),
            to_addrs=[a.strip() for a in os.environ.get("SMTP_TO", "").split(",") if a.strip()],
        )
        log.info("SMTP channel activé (host=%s)", smtp_host)

    return channels


def _default_rules() -> list[AlertRule]:
    """Règles d'alerte par défaut — critiques + high uniquement."""
    return [
        AlertRule(
            name="critical_findings",
            severity_threshold="critical",
            channels=["slack", "teams", "smtp"],
        ),
        AlertRule(
            name="high_findings",
            severity_threshold="high",
            channels=["slack", "teams"],
        ),
    ]


# ─── Modes ────────────────────────────────────────────────────────────────────


def _run_once(invoices_path: Path | None) -> int:
    """Exécute un cycle de détection unique. Renvoie l'exit code."""
    provider = _file_provider(invoices_path) if invoices_path else _empty_provider
    channels = _build_channels()
    store = AlertStore()
    result = run_detection_once(
        invoices_provider=provider,
        rules=_default_rules(),
        channels=channels,
        store=store,
    )
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    if result.status == "error":
        return 1
    return 0


def _run_daily(invoices_path: Path | None, hour: int, minute: int) -> int:
    """Démarre un BackgroundScheduler quotidien — bloque jusqu'à SIGINT/SIGTERM."""
    from p2p_fraud.scheduler.runner import create_scheduler, schedule_daily_detection_job

    provider = _file_provider(invoices_path) if invoices_path else _empty_provider
    channels = _build_channels()
    store = AlertStore()
    scheduler = create_scheduler()
    schedule_daily_detection_job(
        scheduler,
        invoices_provider=provider,
        rules=_default_rules(),
        channels=channels,
        store=store,
        hour=hour,
        minute=minute,
    )
    scheduler.start()
    log.info("Scheduler démarré — prochain run quotidien à %02d:%02d Europe/Paris", hour, minute)

    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        log.info("Arrêt demandé — shutdown du scheduler")
        scheduler.shutdown(wait=False)
        return 0


def _print_health() -> int:
    """Affiche la configuration détectée + sources d'alerting."""
    s = get_settings()
    config = {
        "log_level": s.log_level,
        "log_format": s.log_format,
        "database_url_configured": bool(s.database_url),
        "fraud_cases_db": s.fraud_cases_db,
        "channels": {
            "slack": bool(s.slack_webhook_url),
            "teams": bool(s.teams_webhook_url),
            "smtp": bool(os.environ.get("SMTP_HOST")),
        },
    }
    print(json.dumps(config, indent=2))
    return 0


# ─── CLI parser ───────────────────────────────────────────────────────────────


def _parse_hhmm(raw: str) -> tuple[int, int]:
    try:
        h_str, m_str = raw.split(":")
        h, m = int(h_str), int(m_str)
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError
        return h, m
    except (ValueError, AttributeError) as exc:
        raise argparse.ArgumentTypeError(
            f"Format attendu HH:MM (00-23:00-59), reçu : {raw!r}"
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m p2p_fraud.scheduler",
        description="Scheduler de détection P2P Fraud Detective FR.",
    )
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--once", action="store_true", help="Single-shot run, puis exit (Cloud Scheduler-friendly)"
    )
    mode.add_argument(
        "--daily",
        type=_parse_hhmm,
        metavar="HH:MM",
        help="Long-running, run quotidien à l'heure indiquée (Europe/Paris)",
    )
    mode.add_argument("--health", action="store_true", help="Affiche la config détectée et exit")
    p.add_argument(
        "--invoices",
        type=Path,
        default=None,
        help="Chemin du fichier de factures (CSV/Parquet/Excel). Si absent, run skip.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    args = build_parser().parse_args(argv)
    if args.health:
        return _print_health()
    if args.once:
        return _run_once(args.invoices)
    return _run_daily(args.invoices, *args.daily)


if __name__ == "__main__":
    sys.exit(main())
