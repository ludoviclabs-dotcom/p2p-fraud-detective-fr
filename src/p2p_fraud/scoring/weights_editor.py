"""Validation des fichiers `weights.yaml` éditables depuis la page Gouvernance.

Extrait pour pouvoir être testé sans dépendance Streamlit. La validation est
appliquée à la sauvegarde du formulaire `pages/16_🛡️_Gouvernance.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ALLOWED_DETECTORS: frozenset[str] = frozenset(
    {
        "duplicates",
        "thresholds",
        "benford",
        "sirene",
        "isolation_forest",
        "graph",
        "master_data",
        "sanctions",
    }
)
REQUIRED_SEVERITIES: frozenset[str] = frozenset({"low", "medium", "high", "critical"})


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    message: str
    parsed: dict[str, Any] | None = None


def validate_weights_yaml(text: str) -> ValidationResult:
    """Valide la structure du YAML weights.

    Règles :
    - Document racine = dict.
    - Section `detector_weights` (dict) : clés ∈ ALLOWED_DETECTORS, valeurs >= 0.
    - Section `severity_multiplier` (dict) : clés == REQUIRED_SEVERITIES,
      valeurs ∈ [0, 1].
    """
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return ValidationResult(False, f"YAML invalide : {exc}")

    if not isinstance(data, dict):
        return ValidationResult(False, "Le document doit être un dict YAML racine.")

    dw = data.get("detector_weights")
    if not isinstance(dw, dict):
        return ValidationResult(False, "Section `detector_weights` manquante ou non-dict.")
    for k, v in dw.items():
        if k not in ALLOWED_DETECTORS:
            return ValidationResult(False, f"Détecteur inconnu : `{k}`.")
        if not isinstance(v, (int, float)) or v < 0:
            return ValidationResult(False, f"Poids `{k}` doit être un nombre >= 0 (reçu : {v!r}).")

    sm = data.get("severity_multiplier")
    if not isinstance(sm, dict) or set(sm.keys()) != REQUIRED_SEVERITIES:
        return ValidationResult(
            False,
            f"`severity_multiplier` doit contenir exactement {sorted(REQUIRED_SEVERITIES)}.",
        )
    for k, v in sm.items():
        if not isinstance(v, (int, float)) or not 0 <= v <= 1:
            return ValidationResult(False, f"Multiplier `{k}` doit être ∈ [0, 1] (reçu : {v!r}).")

    return ValidationResult(True, "Validation OK.", parsed=data)


def write_weights(path: Path, text: str) -> ValidationResult:
    """Valide puis écrit le fichier. Si invalide, n'écrit pas."""
    result = validate_weights_yaml(text)
    if not result.ok:
        return result
    path.write_text(text, encoding="utf-8")
    return result
