import io

import pandas as pd

from p2p_fraud.ingestion.parsers import load_invoices


def _to_csv_bytes(df: pd.DataFrame, sep: str = ",", encoding: str = "utf-8") -> io.BytesIO:
    s = df.to_csv(index=False, sep=sep)
    return io.BytesIO(s.encode(encoding))


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "invoice_id": ["INV001", "INV002", "INV003"],
            "vendor_name": ["ACME SARL", "Beta SAS", "Gamma SA"],
            "amount": ["1234.56", "5000.00", "789.01"],
            "invoice_date": ["2025-01-15", "2025-02-20", "2025-03-10"],
            "siren": ["123456789", "987654321", "555444333"],
            "currency": ["EUR", "EUR", "USD"],
        }
    )


def test_load_csv_canonical_headers():
    df_in = _sample_df()
    buf = _to_csv_bytes(df_in)
    df_out, report = load_invoices(buf, suffix=".csv")
    assert report["missing_required"] == []
    assert len(df_out) == 3
    assert df_out["amount"].iloc[0] == 1234.56
    assert df_out["currency"].iloc[2] == "USD"


def test_load_csv_french_headers():
    df_in = _sample_df().rename(
        columns={
            "invoice_id": "N° Facture",
            "vendor_name": "Fournisseur",
            "amount": "Montant TTC",
            "invoice_date": "Date facture",
        }
    )
    buf = _to_csv_bytes(df_in)
    df_out, report = load_invoices(buf, suffix=".csv")
    assert report["missing_required"] == []
    assert len(df_out) == 3


def test_load_csv_semicolon_separator():
    df_in = _sample_df()
    buf = _to_csv_bytes(df_in, sep=";")
    df_out, _ = load_invoices(buf, suffix=".csv")
    assert len(df_out) == 3


def test_load_csv_comma_decimal():
    df_in = _sample_df()
    df_in["amount"] = ["1 234,56", "5 000,00", "789,01"]
    buf = _to_csv_bytes(df_in, sep=";")
    df_out, _ = load_invoices(buf, suffix=".csv")
    assert df_out["amount"].iloc[0] == 1234.56


def test_invalid_rows_filtered():
    df_in = _sample_df()
    df_in.loc[1, "amount"] = "-100"  # négatif → invalide
    buf = _to_csv_bytes(df_in)
    df_out, report = load_invoices(buf, suffix=".csv")
    assert len(df_out) == 2
    assert len(report["errors"]) == 1


def test_missing_required_reported():
    df_in = pd.DataFrame({"foo": ["a"], "bar": ["b"]})
    buf = _to_csv_bytes(df_in)
    df_out, report = load_invoices(buf, suffix=".csv")
    assert df_out.empty
    assert "invoice_id" in report["missing_required"]
