"""Sérialisation canonique JSON pour Evidence Pack — déterministe et stable.

Spec RFC 8785 (JSON Canonicalization Scheme) approximée :
- clés triées alphabétiquement (récursivement)
- séparateurs sans espaces (",", ":")
- pas d'indentation
- encodage UTF-8 strict
- nombres conservés tels quels (déjà déterministes via json.dumps)

Pourquoi : deux serveurs (ou deux runs) construisant le même pack DOIVENT
produire exactement les mêmes octets → même SHA-256. C'est l'exigence
de rejouabilité ISA 240 / preuve probante.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(payload: Any) -> str:
    """Sérialise `payload` en JSON canonique stable (RFC 8785-like)."""
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sha256_hex(text: str) -> str:
    """SHA-256 hex d'un texte UTF-8."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_hash(payload: Any) -> tuple[str, str]:
    """Renvoie `(canonical_json, sha256_hex)` en un seul appel."""
    canonical = canonical_json(payload)
    return canonical, sha256_hex(canonical)
