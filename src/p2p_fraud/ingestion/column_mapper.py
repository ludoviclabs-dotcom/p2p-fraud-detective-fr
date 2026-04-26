"""Mapping des en-têtes hétérogènes (SAP LFA1/RBKP/BSEG, Sage, Cegid, exports Excel libres)
vers le schéma canonique de `Invoice`.

Permet à l'utilisateur d'uploader un fichier sans renommer manuellement ses colonnes.
"""

from __future__ import annotations

import re
import unicodedata

CANONICAL_COLUMNS: list[str] = [
    "invoice_id",
    "siren",
    "vendor_name",
    "iban",
    "amount",
    "currency",
    "invoice_date",
    "posting_date",
    "po_number",
    "user_id",
    "cost_center",
    "gl_account",
]

# Synonymes connus → colonne canonique. Comparaison normalisée (lowercase, sans accent, sans ponctuation).
_ALIAS_MAP: dict[str, list[str]] = {
    "invoice_id": [
        "invoice_id",
        "invoice_no",
        "invoice_number",
        "belnr",
        "n_facture",
        "numero_facture",
        "doc_no",
        "document_no",
        "piece",
        "n_piece",
    ],
    "siren": ["siren", "siret", "vendor_siren", "lifnr_siren", "lifnr_taxnum"],
    "vendor_name": [
        "vendor_name",
        "vendor",
        "fournisseur",
        "lifnr_name",
        "name1",
        "supplier",
        "supplier_name",
        "raison_sociale",
        "tiers",
    ],
    "iban": ["iban", "bank_iban", "compte_bancaire", "rib_iban"],
    "amount": [
        "amount",
        "wrbtr",
        "montant",
        "ttc",
        "ht",
        "net_amount",
        "montant_ttc",
        "montant_ht",
        "amount_local",
        "amount_eur",
    ],
    "currency": ["currency", "waers", "devise"],
    "invoice_date": [
        "invoice_date",
        "bldat",
        "date_facture",
        "doc_date",
        "date_piece",
    ],
    "posting_date": [
        "posting_date",
        "budat",
        "date_compta",
        "date_comptabilisation",
    ],
    "po_number": ["po_number", "po", "ebeln", "n_commande", "purchase_order"],
    "user_id": ["user_id", "usnam", "utilisateur", "saisi_par", "user"],
    "cost_center": ["cost_center", "kostl", "centre_de_cout", "cc"],
    "gl_account": ["gl_account", "hkont", "compte_general", "compte"],
}


def _normalize(name: str) -> str:
    """Lowercase, strip accents, collapse non-alphanumeric to '_'."""
    decomposed = unicodedata.normalize("NFKD", name)
    ascii_only = decomposed.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_only.lower().strip()
    cleaned = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    return cleaned


_NORMALIZED_LOOKUP: dict[str, str] = {}
for canonical, aliases in _ALIAS_MAP.items():
    for alias in aliases:
        _NORMALIZED_LOOKUP[_normalize(alias)] = canonical


def auto_map_columns(headers: list[str]) -> dict[str, str | None]:
    """Mappe une liste d'en-têtes utilisateur vers le schéma canonique.

    Renvoie un dict `{header_original: canonical_or_None}`.
    """
    mapping: dict[str, str | None] = {}
    used_canonical: set[str] = set()
    for h in headers:
        normalized = _normalize(h)
        canonical = _NORMALIZED_LOOKUP.get(normalized)
        if canonical and canonical not in used_canonical:
            mapping[h] = canonical
            used_canonical.add(canonical)
        else:
            mapping[h] = None
    return mapping


def reverse_mapping(mapping: dict[str, str | None]) -> dict[str, str]:
    """Inverse pour `df.rename(columns=...)`. Filtre les non-mappés."""
    return {orig: canon for orig, canon in mapping.items() if canon is not None}


def missing_required(
    mapping: dict[str, str | None],
    required: tuple[str, ...] = ("invoice_id", "vendor_name", "amount", "invoice_date"),
) -> list[str]:
    """Retourne les colonnes canoniques requises non présentes dans le mapping."""
    mapped = {c for c in mapping.values() if c is not None}
    return [c for c in required if c not in mapped]
