"""Logging centralisé — texte simple ou JSON structuré selon `Settings`.

Format JSON utilisé en production (Cloud Run, Aiven, observabilité), facile
à indexer dans Loki / Cloud Logging. Format texte lisible en local et tests.

Idempotent : appeler `configure_logging()` plusieurs fois remplace les
handlers du root logger sans en créer de nouveaux.
"""

from __future__ import annotations

import logging
import sys

from .config import Settings, get_settings


def configure_logging(settings: Settings | None = None) -> None:
    """Configure le root logger avec le niveau et format depuis `Settings`.

    À appeler au boot de l'application (Streamlit, FastAPI, scheduler CLI).
    """
    cfg = settings or get_settings()
    level = getattr(logging, cfg.log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_make_formatter(cfg.log_format))

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)


def _make_formatter(fmt: str) -> logging.Formatter:
    if fmt.lower() == "json":
        try:
            from pythonjsonlogger import jsonlogger
        except ImportError:
            return _text_formatter()
        return jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s",
            rename_fields={"asctime": "ts", "levelname": "level"},
        )
    return _text_formatter()


def _text_formatter() -> logging.Formatter:
    return logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
