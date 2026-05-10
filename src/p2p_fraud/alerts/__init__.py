"""Module alertes — canaux (Teams/Slack/SMTP), règles, historique persistant."""

from p2p_fraud.alerts.channels import (
    AlertChannel,
    SlackWebhook,
    SMTPChannel,
    TeamsWebhook,
)
from p2p_fraud.alerts.rules import Alert, AlertRule, evaluate_rules
from p2p_fraud.alerts.store import AlertStore

__all__ = [
    "Alert",
    "AlertChannel",
    "AlertRule",
    "AlertStore",
    "SMTPChannel",
    "SlackWebhook",
    "TeamsWebhook",
    "evaluate_rules",
]
