"""Presets ERP — chargement YAML, auto-détection et application au DataFrame.

Workflow :
1. `load_preset("sap_lfa1_rbkp")` ou `auto_detect_preset(headers)`.
2. `Preset.apply(df)` → DataFrame renommé vers le schéma canonique, avec
   conversion de format de date et de séparateurs si besoin.
3. Fallback gracieux : si un champ du preset est absent dans l'export, il est
   ignoré (warning log) plutôt que crash.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

from p2p_fraud.ingestion.column_mapper import auto_map_columns

log = logging.getLogger(__name__)

PRESETS_DIR = Path(__file__).resolve().parent
DEFAULT_AUTO_DETECT_THRESHOLD = 3  # nb de signature_columns nécessaires


@dataclass(frozen=True)
class Preset:
    name: str
    label: str
    description: str
    signature_columns: list[str]
    mapping: dict[str, str]  # canonical_name -> source_column_in_export
    date_format: str | None = None
    decimal_separator: str = "."
    thousand_separator: str = ""

    @classmethod
    def from_yaml(cls, path: Path) -> Preset:
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(
            name=data["name"],
            label=data.get("label", data["name"]),
            description=data.get("description", ""),
            signature_columns=list(data.get("signature_columns") or []),
            mapping=dict(data.get("mapping") or {}),
            date_format=data.get("date_format"),
            decimal_separator=data.get("decimal_separator", "."),
            thousand_separator=data.get("thousand_separator", ""),
        )

    def signature_match_score(self, headers: Iterable[str]) -> int:
        """Compte le nombre de signature_columns présentes dans `headers`."""
        if not self.signature_columns:
            return 0
        normalized_headers = {h.strip() for h in headers}
        return sum(1 for c in self.signature_columns if c in normalized_headers)

    def apply(
        self, df: pd.DataFrame, *, parse_dates: bool = True, parse_amounts: bool = True
    ) -> pd.DataFrame:
        """Applique le preset au DataFrame brut, retourne un DF au schéma canonique.

        - Renomme les colonnes selon `mapping`.
        - Si `parse_dates=True`, parse `invoice_date` / `posting_date` selon `date_format`.
        - Si `parse_amounts=True`, parse `amount` selon les séparateurs.
        - Les colonnes du mapping absentes du DF sont ignorées avec un warning.
        """
        rename: dict[str, str] = {}
        missing: list[str] = []
        for canonical, source in self.mapping.items():
            if source in df.columns:
                rename[source] = canonical
            else:
                missing.append(canonical)

        if missing:
            log.info(
                "Preset %s : champs canoniques sans correspondance dans l'export : %s",
                self.name,
                missing,
            )

        out = df.rename(columns=rename).copy()

        if parse_dates and self.date_format:
            for col in ("invoice_date", "posting_date"):
                if col in out.columns:
                    out[col] = pd.to_datetime(
                        out[col], format=self.date_format, errors="coerce"
                    ).dt.date

        if parse_amounts and "amount" in out.columns:
            out["amount"] = _coerce_amount(
                out["amount"], self.decimal_separator, self.thousand_separator
            )

        return out


def _coerce_amount(
    series: pd.Series, decimal_sep: str, thousand_sep: str
) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(float)
    cleaned = series.astype(str).str.strip()
    if thousand_sep:
        cleaned = cleaned.str.replace(thousand_sep, "", regex=False)
    if decimal_sep != ".":
        cleaned = cleaned.str.replace(decimal_sep, ".", regex=False)
    return pd.to_numeric(cleaned, errors="coerce")


def list_presets() -> list[Preset]:
    """Charge tous les presets YAML disponibles."""
    presets: list[Preset] = []
    for path in sorted(PRESETS_DIR.glob("*.yaml")):
        try:
            presets.append(Preset.from_yaml(path))
        except (yaml.YAMLError, KeyError) as e:
            log.warning("Preset %s ignoré (erreur YAML) : %s", path.name, e)
    return presets


def load_preset(name: str) -> Preset:
    """Charge un preset par son nom (ex. 'sap_lfa1_rbkp')."""
    path = PRESETS_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Preset inconnu : {name}")
    return Preset.from_yaml(path)


def auto_detect_preset(
    headers: Iterable[str],
    *,
    threshold: int = DEFAULT_AUTO_DETECT_THRESHOLD,
) -> Preset | None:
    """Détecte le preset le plus probable depuis la signature de colonnes.

    Si aucun preset n'atteint `threshold` colonnes signature, on tente le
    fallback `column_mapper.auto_map_columns` : si au moins 4 champs canoniques
    requis sont mappés, on renvoie le preset générique.
    """
    headers = list(headers)
    candidates = [
        (p, p.signature_match_score(headers))
        for p in list_presets()
        if p.signature_columns
    ]
    candidates.sort(key=lambda x: x[1], reverse=True)
    if candidates and candidates[0][1] >= threshold:
        return candidates[0][0]

    # Fallback générique
    canonical_mapping = auto_map_columns(headers)
    n_canonical_mapped = sum(1 for v in canonical_mapping.values() if v is not None)
    if n_canonical_mapped >= 4:
        try:
            return load_preset("generic_csv")
        except FileNotFoundError:
            return None
    return None


__all__ = [
    "Preset",
    "auto_detect_preset",
    "list_presets",
    "load_preset",
]
