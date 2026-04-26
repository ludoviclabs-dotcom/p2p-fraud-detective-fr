"""Parsers Excel/CSV — détection séparateur/encoding, validation Pydantic, dataframe canonique."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import ValidationError

from p2p_fraud.ingestion.column_mapper import (
    CANONICAL_COLUMNS,
    auto_map_columns,
    missing_required,
    reverse_mapping,
)
from p2p_fraud.schema import Invoice


class IngestionError(Exception):
    """Erreur métier d'ingestion (séparateur introuvable, colonnes obligatoires manquantes, etc.)."""


def _read_csv(source: Path | io.IOBase) -> pd.DataFrame:
    """Tente plusieurs combinaisons (encoding × séparateur) jusqu'à obtenir > 1 colonne."""
    encodings = ["utf-8", "utf-8-sig", "cp1252", "latin-1"]
    separators = [",", ";", "\t", "|"]
    last_err: Exception | None = None
    for enc in encodings:
        for sep in separators:
            try:
                if isinstance(source, Path):
                    df = pd.read_csv(
                        source,
                        encoding=enc,
                        sep=sep,
                        dtype=str,
                        keep_default_na=False,
                        na_values=["", "NA", "NaN"],
                    )
                else:
                    source.seek(0)
                    df = pd.read_csv(
                        source,
                        encoding=enc,
                        sep=sep,
                        dtype=str,
                        keep_default_na=False,
                        na_values=["", "NA", "NaN"],
                    )
                if df.shape[1] > 1:
                    return df
            except Exception as e:
                last_err = e
                continue
    raise IngestionError(
        f"Impossible de parser le CSV (testé {len(encodings)}×{len(separators)} combinaisons). Dernière erreur : {last_err}"
    )


def _read_excel(source: Path | io.IOBase) -> pd.DataFrame:
    return pd.read_excel(source, dtype=str)


def load_dataframe(source: Path | io.IOBase | str, *, suffix: str | None = None) -> pd.DataFrame:
    """Lit un CSV ou un Excel selon l'extension. Renvoie un DataFrame en str (typage différé après mapping)."""
    if isinstance(source, str):
        source = Path(source)
    if isinstance(source, Path):
        suffix = suffix or source.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return _read_excel(source)
    return _read_csv(source)


def _parse_dates(series: pd.Series) -> pd.Series:
    """Tente plusieurs formats de date courants : ISO d'abord, puis dayfirst FR."""
    s = series.astype("string").str.strip()
    parsed = pd.to_datetime(s, errors="coerce", format="ISO8601")
    mask = parsed.isna() & s.notna()
    if mask.any():
        # Formats français : 15/01/2025, 15-01-2025
        fallback = pd.to_datetime(s[mask], errors="coerce", dayfirst=True)
        parsed.loc[mask] = fallback
    return parsed.dt.date


def _coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    """Cast les colonnes canoniques connues vers leurs types attendus avant validation Pydantic."""
    out = df.copy()
    if "amount" in out:
        # Gérer formats "1 234,56" et "1,234.56"
        out["amount"] = (
            out["amount"]
            .astype(str)
            .str.replace(" ", "", regex=False)
            .str.replace(" ", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        out["amount"] = pd.to_numeric(out["amount"], errors="coerce")
    for col in ("invoice_date", "posting_date"):
        if col in out:
            out[col] = _parse_dates(out[col])
    for col in (
        "invoice_id",
        "siren",
        "vendor_name",
        "iban",
        "currency",
        "po_number",
        "user_id",
        "cost_center",
        "gl_account",
    ):
        if col in out:
            out[col] = out[col].astype("string").str.strip()
    return out


def validate_invoices(
    df: pd.DataFrame, *, max_errors: int = 50
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Valide chaque ligne contre le schéma `Invoice`. Renvoie (df_validé, erreurs_collectées).

    Les lignes invalides sont écartées du DataFrame retourné mais consignées dans `errors`.
    """
    errors: list[dict[str, Any]] = []
    valid_rows: list[dict[str, Any]] = []
    for i, row in df.iterrows():
        payload = {k: (None if pd.isna(v) else v) for k, v in row.items() if k in CANONICAL_COLUMNS}
        try:
            invoice = Invoice(**payload)
            valid_rows.append(invoice.model_dump())
        except ValidationError as ve:
            if len(errors) < max_errors:
                errors.append({"row": int(i), "errors": ve.errors()})
    return pd.DataFrame(valid_rows, columns=CANONICAL_COLUMNS), errors


def load_invoices(
    source: Path | io.IOBase | str,
    *,
    column_overrides: dict[str, str] | None = None,
    suffix: str | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Pipeline complet : lecture → auto-mapping → typage → validation Pydantic.

    `column_overrides` : forçage manuel `{header_original: canonical}` quand l'auto-mapping échoue.

    Renvoie `(df_canonique_valide, report)` où `report` contient mapping, missing, errors, n_rows.
    """
    df_raw = load_dataframe(source, suffix=suffix)
    headers = list(df_raw.columns)
    mapping = auto_map_columns(headers)
    if column_overrides:
        for orig, canon in column_overrides.items():
            if orig in mapping:
                mapping[orig] = canon

    missing = missing_required(mapping)
    if missing:
        return pd.DataFrame(columns=CANONICAL_COLUMNS), {
            "mapping": mapping,
            "missing_required": missing,
            "errors": [],
            "n_rows_input": len(df_raw),
            "n_rows_valid": 0,
        }

    df_renamed = df_raw.rename(columns=reverse_mapping(mapping))
    keep = [c for c in CANONICAL_COLUMNS if c in df_renamed.columns]
    df_canon = df_renamed[keep].copy()
    df_typed = _coerce_types(df_canon)
    df_valid, errors = validate_invoices(df_typed)

    return df_valid, {
        "mapping": mapping,
        "missing_required": [],
        "errors": errors,
        "n_rows_input": len(df_raw),
        "n_rows_valid": len(df_valid),
    }
