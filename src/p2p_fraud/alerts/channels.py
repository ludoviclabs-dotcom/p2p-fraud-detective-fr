"""Canaux d'alerte — Slack, Microsoft Teams (Incoming Webhook), SMTP.

Tous les canaux implémentent la même interface `send(...)`. Les payloads
sont formatés selon les conventions de chaque service.
"""

from __future__ import annotations

import json
import logging
import smtplib
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Protocol

import requests

log = logging.getLogger(__name__)

_TIMEOUT = 10  # secondes

_SEVERITY_COLOR = {
    "critical": "#A23E48",
    "high": "#C97B1F",
    "medium": "#E5A93A",
    "low": "#3E7C5A",
}


class AlertChannel(Protocol):
    """Interface commune à tous les canaux d'alerte."""

    name: str

    def send(
        self,
        *,
        title: str,
        body: str,
        severity: str,
        metadata: dict | None = None,
    ) -> bool: ...


@dataclass
class SlackWebhook:
    """Canal Slack via Incoming Webhook (https://api.slack.com/messaging/webhooks).

    Configurer un webhook pour le canal cible et fournir l'URL.
    """

    url: str
    name: str = "slack"

    def send(
        self,
        *,
        title: str,
        body: str,
        severity: str,
        metadata: dict | None = None,
    ) -> bool:
        color = _SEVERITY_COLOR.get(severity.lower(), "#5A6478")
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": title,
                    "text": body,
                    "fields": [
                        {
                            "title": k,
                            "value": str(v),
                            "short": len(str(v)) < 30,
                        }
                        for k, v in (metadata or {}).items()
                    ],
                    "footer": "P2P Fraud Detective FR — alertes automatiques",
                }
            ]
        }
        try:
            resp = requests.post(
                self.url,
                json=payload,
                timeout=_TIMEOUT,
                headers={"Content-Type": "application/json"},
            )
            return 200 <= resp.status_code < 300
        except requests.RequestException as exc:
            log.warning("Slack webhook failed: %s", exc)
            return False


@dataclass
class TeamsWebhook:
    """Canal Microsoft Teams via Incoming Webhook (Connector).

    Format MessageCard adaptive — compatible avec les workflows Power Automate.
    """

    url: str
    name: str = "teams"

    def send(
        self,
        *,
        title: str,
        body: str,
        severity: str,
        metadata: dict | None = None,
    ) -> bool:
        color = _SEVERITY_COLOR.get(severity.lower(), "5A6478").lstrip("#")
        facts = [{"name": k, "value": str(v)} for k, v in (metadata or {}).items()]
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color,
            "summary": title,
            "title": title,
            "text": body,
            "sections": [
                {
                    "activityTitle": "P2P Fraud Detective FR",
                    "activitySubtitle": f"Sévérité : {severity.upper()}",
                    "facts": facts,
                    "markdown": True,
                }
            ],
        }
        try:
            resp = requests.post(
                self.url,
                data=json.dumps(payload),
                timeout=_TIMEOUT,
                headers={"Content-Type": "application/json"},
            )
            return 200 <= resp.status_code < 300
        except requests.RequestException as exc:
            log.warning("Teams webhook failed: %s", exc)
            return False


@dataclass
class SMTPChannel:
    """Canal email via SMTP (envoi direct, sans queue).

    Pour un usage production, préférer un MTA dédié (Postfix) ou un service
    transactionnel (SendGrid, AWS SES) via leurs propres webhooks.
    """

    host: str
    port: int
    username: str
    password: str
    from_addr: str
    to_addrs: list[str]
    use_tls: bool = True
    name: str = "smtp"

    def send(
        self,
        *,
        title: str,
        body: str,
        severity: str,
        metadata: dict | None = None,
    ) -> bool:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[P2P Fraud {severity.upper()}] {title}"
        msg["From"] = self.from_addr
        msg["To"] = ", ".join(self.to_addrs)

        meta_lines = (
            "\n".join(f"  - {k}: {v}" for k, v in (metadata or {}).items())
            or "  (aucune métadonnée)"
        )
        text_body = (
            f"{title}\n\n{body}\n\nMétadonnées :\n{meta_lines}\n\n"
            "— P2P Fraud Detective FR (alertes automatiques)\n"
        )
        msg.attach(MIMEText(text_body, "plain", "utf-8"))

        try:
            with smtplib.SMTP(self.host, self.port, timeout=_TIMEOUT) as server:
                if self.use_tls:
                    server.starttls()
                if self.username:
                    server.login(self.username, self.password)
                server.send_message(msg)
            return True
        except (smtplib.SMTPException, OSError) as exc:
            log.warning("SMTP send failed: %s", exc)
            return False
