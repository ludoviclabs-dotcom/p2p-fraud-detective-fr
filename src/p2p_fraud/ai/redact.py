"""Redaction des données sensibles avant envoi à un LLM — Sprint 5 MandateGuard.

Rôle :
- Bloquer les IBAN clairs (pattern reconnaissable) avant tout appel modèle
- Masquer les ICS (Identifiant Créancier SEPA) en gardant uniquement
  les 4 premiers + 3 derniers caractères
- Refuser de transmettre nom + IBAN ensemble (`LeakingFieldError`)
- Permettre d'auditer la chaîne : la fonction `is_safe_for_llm` peut être
  appelée APRÈS un build de prompt pour confirmer qu'aucune fuite résiduelle
  n'a échappé à la redaction

Le module n'envoie PAS au LLM lui-même — il prépare le payload. Le caller
(narrative_generator, dispute_draft, etc.) est responsable de l'invocation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# IBAN format ISO 13616 : 2 lettres pays + 2 chiffres clé + 11-30 alphanum.
# On accepte les IBAN avec ou sans espace (cas Excel/CSV typique).
IBAN_LEAK_PATTERN = re.compile(
    r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]){11,30}\b",
    flags=re.IGNORECASE,
)

# ICS : pattern français [PAYS][ZZZ + 6 digits + 3 alpha] (ex. FR18ZZZ002305)
ICS_PATTERN = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{9,12}\b")

# Numéros à 10+ digits suspectés d'être des n° de CB / téléphone / SIREN
LONG_DIGIT_SEQ = re.compile(r"\b\d{10,}\b")

# Email
EMAIL_PATTERN = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")


class LeakingFieldError(ValueError):
    """Le payload contient encore une donnée sensible après redaction."""

    def __init__(self, field_name: str, pattern: str) -> None:
        super().__init__(
            f"Donnée sensible non redactée dans '{field_name}' "
            f"(pattern={pattern})"
        )
        self.field_name = field_name
        self.pattern = pattern


@dataclass(frozen=True)
class RedactionConfig:
    """Politique de redaction — overridable au cas par cas."""

    redact_iban: bool = True
    redact_ics: bool = True
    redact_long_digits: bool = True
    redact_emails: bool = True
    # Champs qui doivent rester intégraux (ex. reason codes, montants)
    preserve_fields: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {
                "code",
                "rule_id",
                "severity",
                "score",
                "decision",
                "level",
                "domain",
                "engine_version",
                "amount_cents",
                "currency",
            }
        )
    )
    iban_replacement: str = "[IBAN_REDACTED]"
    email_replacement: str = "[EMAIL_REDACTED]"


DEFAULT_CONFIG = RedactionConfig()


def redact_iban_patterns(text: str, *, replacement: str = "[IBAN_REDACTED]") -> str:
    """Remplace tout pattern IBAN-like par `replacement`.

    Préserve les chaînes qui ressemblent à un IBAN mais sont en fait des
    fingerprints HMAC : un fingerprint fait exactement 64 hex chars sans
    code pays au début, donc pas matché par notre regex.
    """
    return IBAN_LEAK_PATTERN.sub(replacement, text)


def _mask_ics(value: str) -> str:
    """`FR18ZZZ002305` → `FR18…305` (préserve pays + dernière partie)."""
    if len(value) < 7:
        return "[ICS_REDACTED]"
    return f"{value[:4]}…{value[-3:]}"


def redact_text(
    text: str | None,
    *,
    config: RedactionConfig | None = None,
) -> str:
    """Applique la redaction sur une chaîne libre.

    Ordre d'application :
    1. IBAN → `[IBAN_REDACTED]`
    2. ICS → masqué façon `FR18…305`
    3. Séquences ≥ 10 digits → `[NUMBER_REDACTED]` (couvre SIREN, CB, tel)
    4. Email → `[EMAIL_REDACTED]`
    """
    if text is None:
        return ""
    cfg = config or DEFAULT_CONFIG
    result = text
    if cfg.redact_iban:
        result = IBAN_LEAK_PATTERN.sub(cfg.iban_replacement, result)
    if cfg.redact_ics:
        result = ICS_PATTERN.sub(lambda m: _mask_ics(m.group(0)), result)
    if cfg.redact_long_digits:
        result = LONG_DIGIT_SEQ.sub("[NUMBER_REDACTED]", result)
    if cfg.redact_emails:
        result = EMAIL_PATTERN.sub(cfg.email_replacement, result)
    return result


def redact_risk_input(
    payload: dict[str, Any],
    *,
    config: RedactionConfig | None = None,
) -> dict[str, Any]:
    """Redaction récursive d'un dict — utilisée avant tout prompt LLM.

    Garde les champs structurés (`code`, `score`, `severity`, `amount_cents`…)
    intacts. Redacte le contenu textuel des autres champs.
    """
    cfg = config or DEFAULT_CONFIG
    return _redact_value(payload, cfg, "$")


def _redact_value(value: Any, cfg: RedactionConfig, path: str) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for k, v in value.items():
            child_path = f"{path}.{k}"
            if k in cfg.preserve_fields:
                out[k] = v
            else:
                out[k] = _redact_value(v, cfg, child_path)
        return out
    if isinstance(value, list):
        return [_redact_value(v, cfg, f"{path}[{i}]") for i, v in enumerate(value)]
    if isinstance(value, str):
        return redact_text(value, config=cfg)
    return value


def is_safe_for_llm(
    payload: dict[str, Any] | str,
    *,
    raise_on_leak: bool = False,
    config: RedactionConfig | None = None,
) -> bool:
    """Vérifie qu'AUCUN pattern d'IBAN/ICS ne subsiste dans le payload.

    `raise_on_leak=True` → lève `LeakingFieldError` au premier match (utile
    pour fail-closed dans un pipeline AI).
    """
    cfg = config or DEFAULT_CONFIG
    leaks: list[tuple[str, str]] = []
    if isinstance(payload, str):
        _scan_text(payload, "$", cfg, leaks)
    else:
        _scan_value(payload, "$", cfg, leaks)
    if leaks and raise_on_leak:
        path, pat = leaks[0]
        raise LeakingFieldError(path, pat)
    return not leaks


def _scan_value(
    value: Any, path: str, cfg: RedactionConfig, leaks: list[tuple[str, str]]
) -> None:
    if isinstance(value, dict):
        for k, v in value.items():
            if k in cfg.preserve_fields:
                continue
            _scan_value(v, f"{path}.{k}", cfg, leaks)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            _scan_value(v, f"{path}[{i}]", cfg, leaks)
    elif isinstance(value, str):
        _scan_text(value, path, cfg, leaks)


def _scan_text(
    text: str, path: str, cfg: RedactionConfig, leaks: list[tuple[str, str]]
) -> None:
    if cfg.redact_iban and IBAN_LEAK_PATTERN.search(text):
        leaks.append((path, "IBAN"))
