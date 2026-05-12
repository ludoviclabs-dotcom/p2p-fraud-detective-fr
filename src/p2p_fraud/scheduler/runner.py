"""Scheduler de détection P2P — runs périodiques + dispatch d'alertes multi-canal.

Architecture P4-4 (juillet 2026) :
- `run_detection_once()` : fonction réentrante, sans état, **exécutable en CLI**
  ou depuis le scheduler APScheduler embarqué. Sert aussi de point d'entrée
  pour Cloud Scheduler HTTP / cron systemd.
- `create_scheduler()` + `schedule_daily_detection_job()` : conservés pour la
  démo Streamlit Cloud / le mode dev local (`BackgroundScheduler`).
- Retry exponentiel via `tenacity` (max 3 tentatives, 1s → 2s → 4s) sur les
  canaux d'alerte (Slack, Teams, SMTP) — robustesse réseau pour Cloud Run.

Pour la production (pilote ETI), utiliser le CLI :

    python -m p2p_fraud.scheduler --once     # single-shot (Cloud Scheduler HTTP)
    python -m p2p_fraud.scheduler --daily 06:00  # long-running

Voir `docs/deployment-cloud-run.md` pour les recettes complètes.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from p2p_fraud.alerts.channels import AlertChannel
from p2p_fraud.alerts.rules import AlertRule, evaluate_rules
from p2p_fraud.alerts.store import AlertStore
from p2p_fraud.detectors.duplicates import detect_duplicates
from p2p_fraud.detectors.sanctions import detect_sanctioned_vendors
from p2p_fraud.detectors.thresholds import detect_under_threshold

log = logging.getLogger(__name__)


@dataclass
class SchedulerStatus:
    running: bool
    next_run: str | None
    last_run: str | None
    n_jobs: int


@dataclass
class DetectionRunResult:
    """Sortie structurée de `run_detection_once()`."""

    status: str  # "ok" | "skipped" | "error"
    n_invoices: int
    n_findings: int
    n_alerts: int
    n_delivered: int
    n_failed: int
    started_at: str
    finished_at: str
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "n_invoices": self.n_invoices,
            "n_findings": self.n_findings,
            "n_alerts": self.n_alerts,
            "n_delivered": self.n_delivered,
            "n_failed": self.n_failed,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "error": self.error,
        }


_RETRY_ERRORS = (ConnectionError, TimeoutError, OSError)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(_RETRY_ERRORS),
    reraise=True,
)
def _send_with_retry(
    channel: AlertChannel,
    *,
    title: str,
    body: str,
    severity: str,
    metadata: dict[str, Any],
) -> bool:
    """Envoi sur un canal avec backoff exponentiel (1s → 2s → 4s, max 3 essais).

    Retry uniquement sur erreurs réseau transitoires ; les erreurs métier
    (mauvais token, payload invalide) ne sont pas retryées et remontent direct.
    """
    return channel.send(title=title, body=body, severity=severity, metadata=metadata)


def run_detection_once(
    *,
    invoices_provider: Callable[[], pd.DataFrame | None],
    rules: list[AlertRule],
    channels: dict[str, AlertChannel],
    store: AlertStore,
) -> DetectionRunResult:
    """Exécute un cycle complet : détection → règles → dispatch → audit.

    Réentrante, sans état partagé. Peut être appelée :
    - Par le scheduler APScheduler (mode démo, `BackgroundScheduler`)
    - Par le CLI `python -m p2p_fraud.scheduler --once` (Cloud Scheduler)
    - Par un cron systemd / Kubernetes CronJob

    Args:
        invoices_provider: callable renvoyant un DataFrame de factures fraîches.
            Peut renvoyer `None` ou un DataFrame vide → run skip.
        rules: règles d'alerte à évaluer sur les findings.
        channels: canaux disponibles (Slack, Teams, SMTP, ...).
        store: persistance de l'historique des alertes.

    Returns:
        `DetectionRunResult` structuré (JSON-sérialisable).
    """
    started_at = datetime.now().isoformat()
    log.info("Detection run started")

    try:
        df = invoices_provider()
    except Exception as exc:
        log.exception("Provider de factures a échoué")
        return DetectionRunResult(
            status="error",
            n_invoices=0,
            n_findings=0,
            n_alerts=0,
            n_delivered=0,
            n_failed=0,
            started_at=started_at,
            finished_at=datetime.now().isoformat(),
            error=f"provider: {exc}",
        )

    if df is None or df.empty:
        log.info("Pas de données — run skip")
        return DetectionRunResult(
            status="skipped",
            n_invoices=0,
            n_findings=0,
            n_alerts=0,
            n_delivered=0,
            n_failed=0,
            started_at=started_at,
            finished_at=datetime.now().isoformat(),
        )

    findings = []
    findings.extend(detect_duplicates(df))
    findings.extend(detect_under_threshold(df))
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
                ok = _send_with_retry(
                    channel,
                    title=alert.title,
                    body=alert.body,
                    severity=alert.severity,
                    metadata=alert.metadata,
                )
            except (RetryError, *_RETRY_ERRORS) as exc:
                log.warning("Channel %s a échoué après 3 tentatives : %s", ch_name, exc)
                ok = False
            except Exception:
                log.exception("Channel %s a levé une exception non-réseau", ch_name)
                ok = False
            store.record(alert, channel=ch_name, delivered=ok)
            if ok:
                n_delivered += 1
            else:
                n_failed += 1

    log.info(
        "Detection run done — %d findings, %d alerts, %d delivered, %d failed",
        len(findings),
        len(alerts),
        n_delivered,
        n_failed,
    )

    return DetectionRunResult(
        status="ok",
        n_invoices=len(df),
        n_findings=len(findings),
        n_alerts=len(alerts),
        n_delivered=n_delivered,
        n_failed=n_failed,
        started_at=started_at,
        finished_at=datetime.now().isoformat(),
    )


# ─── Compat : ancien wrapper utilisé par le scheduler embarqué ────────────────


def _run_detection_and_alert(
    invoices_provider: Callable[[], pd.DataFrame],
    rules: list[AlertRule],
    channels: dict[str, AlertChannel],
    store: AlertStore,
    state: dict[str, Any],
) -> dict:
    """Adapter rétrocompatible : appelle `run_detection_once()` et alimente `state`."""
    result = run_detection_once(
        invoices_provider=invoices_provider, rules=rules, channels=channels, store=store
    )
    state["last_run"] = result.finished_at
    if result.status == "skipped":
        state["last_status"] = "skipped (no data)"
    elif result.status == "error":
        state["last_status"] = f"error: {result.error}"
    else:
        state["last_status"] = (
            f"{result.n_alerts} alerte(s) — {result.n_delivered} livrées, {result.n_failed} échecs"
        )
    return {
        "status": result.status,
        "n_alerts": result.n_alerts,
        "n_delivered": result.n_delivered,
        "n_failed": result.n_failed,
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
