"""Fraîcheur des sources de données externes (ADR-0007, manque produit).

Une liste de sanctions ou un référentiel Sirene périmés sont un passif
d'audit : ce module enregistre la date du dernier appel réussi de chaque
source live et l'expose pour l'UI de gouvernance.

Implémentation volontairement légère : un fichier JSON par déploiement
(`data/cache/source_freshness.json`), écrit de façon atomique. Les clients
d'enrichissement appellent `record_sync("<source>")` après chaque réponse
réussie — un échec n'écrit rien, donc `last_sync` reflète bien la dernière
donnée réellement obtenue.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from p2p_fraud.config import get_settings

DEFAULT_PATH = Path("data") / "cache" / "source_freshness.json"

# Sources suivies : label affiché + comment savoir si elles sont configurées.
KNOWN_SOURCES: dict[str, str] = {
    "sirene": "Sirene v3 (INSEE)",
    "decp": "DECP (data.economie.gouv.fr)",
    "sanctions": "Sanctions / PEP (OpenSanctions Yente)",
    "pappers": "Pappers (RCS)",
}


def _registry_path(path: str | Path | None = None) -> Path:
    return Path(path) if path is not None else DEFAULT_PATH


def record_sync(source: str, *, detail: str = "", path: str | Path | None = None) -> None:
    """Enregistre un appel réussi pour `source` (écriture atomique, best-effort).

    Ne lève jamais : la traçabilité de fraîcheur ne doit pas faire échouer
    l'enrichissement lui-même.
    """
    target = _registry_path(path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        data = _read(target)
        data[source] = {
            "last_sync": datetime.now(UTC).isoformat(),
            "detail": detail,
        }
        fd, tmp = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, sort_keys=True)
        os.replace(tmp, target)
    except OSError:
        pass


def _read(target: Path) -> dict:
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def get_freshness(path: str | Path | None = None) -> list[dict]:
    """État de fraîcheur de toutes les sources connues, pour l'API/UI."""
    settings = get_settings()
    configured = {
        "sirene": bool(settings.sirene_api_token),
        "decp": True,  # API publique sans clé
        "sanctions": bool(settings.yente_base_url),
        "pappers": bool(settings.pappers_api_key),
    }
    data = _read(_registry_path(path))
    out: list[dict] = []
    for source, label in KNOWN_SOURCES.items():
        entry = data.get(source) or {}
        out.append(
            {
                "source": source,
                "label": label,
                "configured": configured.get(source, False),
                "last_sync": entry.get("last_sync"),
                "detail": entry.get("detail") or "",
            }
        )
    return out
