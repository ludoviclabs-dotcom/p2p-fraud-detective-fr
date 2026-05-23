"""Module IA — wrappers sécurisés autour des appels LLM.

Selon le spec MandateGuard §11 et ADR-0003 :
- Toute donnée envoyée à un LLM DOIT passer par `redact.py` au préalable
- L'IA ne décide jamais seule d'une fraude (rule-engine first)
- Fallback déterministe (template) si le LLM est indisponible ou si la
  redaction détecte un risque de fuite

Ce module ne remplace pas le `llm/narrative_generator.py` existant —
il fournit les primitives de protection que le narrative_generator
DOIT utiliser pour rester conforme.
"""

from p2p_fraud.ai.redact import (
    IBAN_LEAK_PATTERN,
    LeakingFieldError,
    RedactionConfig,
    is_safe_for_llm,
    redact_iban_patterns,
    redact_risk_input,
    redact_text,
)

__all__ = [
    "IBAN_LEAK_PATTERN",
    "LeakingFieldError",
    "RedactionConfig",
    "is_safe_for_llm",
    "redact_iban_patterns",
    "redact_risk_input",
    "redact_text",
]
