from p2p_fraud.ingestion.column_mapper import auto_map_columns, missing_required


def test_canonical_passthrough():
    headers = ["invoice_id", "vendor_name", "amount", "invoice_date"]
    mapping = auto_map_columns(headers)
    assert mapping == {h: h for h in headers}


def test_sap_aliases():
    headers = ["BELNR", "LIFNR_NAME", "WRBTR", "BLDAT", "USNAM"]
    mapping = auto_map_columns(headers)
    assert mapping["BELNR"] == "invoice_id"
    assert mapping["LIFNR_NAME"] == "vendor_name"
    assert mapping["WRBTR"] == "amount"
    assert mapping["BLDAT"] == "invoice_date"
    assert mapping["USNAM"] == "user_id"


def test_french_aliases_with_accents():
    headers = ["N° Facture", "Fournisseur", "Montant TTC", "Date facture", "Compte général"]
    mapping = auto_map_columns(headers)
    assert mapping["N° Facture"] == "invoice_id"
    assert mapping["Fournisseur"] == "vendor_name"
    assert mapping["Montant TTC"] == "amount"
    assert mapping["Date facture"] == "invoice_date"
    assert mapping["Compte général"] == "gl_account"


def test_unmapped_returns_none():
    headers = ["foo_bar_baz_qux"]
    mapping = auto_map_columns(headers)
    assert mapping["foo_bar_baz_qux"] is None


def test_missing_required_detected():
    mapping = {"X": "vendor_name", "Y": "amount"}
    missing = missing_required(mapping)
    assert "invoice_id" in missing
    assert "invoice_date" in missing


def test_no_double_mapping():
    headers = ["invoice_no", "n_facture"]  # tous deux aliasés sur invoice_id
    mapping = auto_map_columns(headers)
    targets = [v for v in mapping.values() if v is not None]
    assert targets.count("invoice_id") == 1
