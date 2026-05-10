"""Wrapper APScheduler — runs quotidiens de détection + dispatch d'alertes.

Pour Streamlit Cloud (re-runs fréquents), la persistance est limitée :
préférer un déploiement Docker / cron / systemd timer pour les runs en
production. Le mode `BackgroundScheduler` reste utile en démo / dev.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd

from p2p_fraud.alerts.channels import AlertChannel
from p2p_fraud.alerts.rules import AlertRule, evaluate_rules
from p2p_fraud.alerts.store import AlertStore
from p2p_fraud.detectors.duplicates import detect_duplicates
from p2p_fraud.detectors.sanctions import detect_sanctioned_vendors
from p2p_fraud.detectors.thresholds import detect_threshold_splits

log = logging.getLogger(__name__)


@dataclass
class SchedulerStatus:
    running: bool
    next_run: str | None
    last_run: str | None
    n_jobs: int


def _run_detection_and_alert(
    invoices_provider: Callable[[], pd.DataFrame],
    rules: list[AlertRule],
    channels: dict[str, AlertChannel],
    store: AlertStore,
    state: dict[str, Any],
) -> dict:
    """Exécute les détecteurs déterministes + évalue les règles + dispatch.

    Cette fonction est appelée par APScheduler à chaque tick.
    """
    state["last_run"] = datetime.now().isoformat()

    df = invoices_provider()
    if df is None or df.empty:
        log.info("Scheduler: pas de données — skip")
        state["last_status"] = "skipped (no data)"
        return {"status": "skipped", "n_alerts": 0}

    findings = []
    findings.extend(detect_duplicates(df))
    findings.extend(detect_threshold_splits(df))
    findings.extend(detect_sanctioned_vendors(df))

    alerts = evaluate_rules(findings, rules)
    n_delivered = 0
    n_failed = 0

    for alert in alerts:
        rule = next((r for r in rules if r.name == alert.rule_name), None)
        target_channels = rule.channels if rule else list(channels.keys())
        for ch_name in target_channels:
            channel = channels.get(ch_name)
            if channel is None:
                continue
            try:
                ok = channel.send(
                    title=alert.title,
                    body=alert.body,
                    severity=alert.severity,
                    metadata=alert.metadata,
                )
            except (ConnectionError, TimeoutError, OSError) as exc:
                log.warning("Channel %s send failed: %s", ch_name, exc)
                ok = False
            store.record(alert, channel=ch_name, delivered=ok)
            if ok:
                n_delivered += 1
            else:
                n_failed += 1

    state["last_status"] = f"{len(alerts)} alerte(s) — {n_delivered} livrées, {n_failed} échecs"
    return {
        "status": "ok",
        "n_alerts": len(alerts),
        "n_delivered": n_delivered,
        "n_failed": n_failed,
    }


def create_scheduler() -> Any:
    """Crée un BackgroundScheduler APScheduler (timezone Europe/Paris).

    Importé tardivement pour ne pas charger APScheduler si non utilisé.
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError as exc:
        raise ImportError(
            "Le package 'apscheduler' est requis pour le scheduler. "
            "Installez-le avec : pip install apscheduler>=3.10"
        ) from exc

    return BackgroundScheduler(timezone="Europe/Paris")


def schedule_daily_detection_job(
    scheduler: Any,
    *,
    invoices_provider: Callable[[], pd.DataFrame],
    rules: list[AlertRule],
    channels: dict[str, AlertChannel],
    store: AlertStore,
    hour: int = 6,
    minute: int = 0,
    state: dict[str, Any] | None = None,
) -> Any:
    """Planifie un run quotidien à l'heure indiquée (timezone Europe/Paris).

    Retourne le job APScheduler créé.
    """
    if state is None:
        state = {}

    return scheduler.add_job(
        _run_detection_and_alert,
        trigger="cron",
        hour=hour,
        minute=minute,
        args=[invoices_provider, rules, channels, store, state],
        id="daily_detection",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
