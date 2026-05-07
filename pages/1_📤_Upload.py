"""Page Upload — ingestion d'un export Excel/CSV ou génération d'un dataset synthétique."""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import streamlit as st

from p2p_fraud.ingestion.column_mapper import CANONICAL_COLUMNS
from p2p_fraud.ingestion.parsers import IngestionError, load_invoices
from p2p_fraud.ingestion.presets import (
    auto_detect_preset,
    list_presets,
    load_preset,
)
from p2p_fraud.synthetic.generator import GeneratorConfig, generate_dataset

st.set_page_config(page_title="Upload — P2P Fraud Detective", page_icon="📤", layout="wide")
st.title("📤 Upload des factures")
st.caption(
    "Importez un export Excel/CSV de factures fournisseurs, ou générez un dataset synthétique pour la démo."
)

tab_upload, tab_erp, tab_synthetic, tab_sample = st.tabs(
    [
        "📁 Importer un fichier",
        "🔌 Connecteur ERP (presets)",
        "🎲 Générer un dataset",
        "📦 Charger l'échantillon",
    ]
)


def _persist(df: pd.DataFrame, source_label: str) -> None:
    st.session_state["df_invoices"] = df
    st.session_state["source_label"] = source_label
    if "fraud_type" in df.columns:
        st.session_state["has_ground_truth"] = True


def _show_summary(df: pd.DataFrame) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Factures", f"{len(df):,}")
    c2.metric("Fournisseurs", f"{df['vendor_name'].nunique():,}")
    if "amount" in df.columns:
        c3.metric("Total", f"{df['amount'].sum():,.0f} €")
    if "fraud_type" in df.columns:
        n_fraud = int(df["is_fraud"].sum())
        c4.metric(
            "Fraudes étiquetées",
            f"{n_fraud:,}",
            help="Ground truth — disponible uniquement sur dataset synthétique",
        )
    st.dataframe(df.head(50), use_container_width=True, height=320)


with tab_upload:
    st.markdown(
        "**Formats acceptés** : `.csv`, `.xlsx`. Les en-têtes habituelles SAP/Sage/Cegid sont auto-détectées."
    )
    uploaded = st.file_uploader("Déposez votre fichier", type=["csv", "xlsx", "xls"])
    if uploaded is not None:
        try:
            buf = io.BytesIO(uploaded.read())
            df, report = load_invoices(buf, suffix=Path(uploaded.name).suffix.lower())
        except IngestionError as e:
            st.error(f"Erreur de lecture : {e}")
            st.stop()

        if report["missing_required"]:
            st.error(
                f"❌ Colonnes obligatoires manquantes : {', '.join(report['missing_required'])}"
            )
            st.write("**Mapping détecté** :")
            st.json({k: v for k, v in report["mapping"].items()})
            st.info("Conseil : renommez vos colonnes pour matcher les noms canoniques attendus.")
            st.code("\n".join(CANONICAL_COLUMNS))
            st.stop()

        st.success(
            f"✅ {report['n_rows_valid']:,} factures valides sur {report['n_rows_input']:,} lignes lues."
        )
        if report["errors"]:
            with st.expander(f"⚠️ {len(report['errors'])} ligne(s) écartée(s)"):
                st.json(report["errors"])
        with st.expander("🔗 Mapping de colonnes"):
            st.json(report["mapping"])
        _persist(df, source_label=uploaded.name)
        _show_summary(df)

with tab_erp:
    st.markdown(
        "**Import via preset ERP** — auto-détecte le format depuis les en-têtes "
        "(SAP, Cegid Loop, Sage X3, Oracle AP) et applique le mapping + parse "
        "des dates et montants au bon format."
    )

    presets = list_presets()
    preset_names = [p.name for p in presets]
    preset_labels = {p.name: f"{p.label} ({p.name})" for p in presets}

    erp_uploaded = st.file_uploader(
        "Déposez votre export ERP", type=["csv", "xlsx", "xls"], key="erp_uploader"
    )

    if erp_uploaded is not None:
        try:
            erp_buf = io.BytesIO(erp_uploaded.read())
            suffix = Path(erp_uploaded.name).suffix.lower()
            if suffix in {".xlsx", ".xls"}:
                raw_df = pd.read_excel(erp_buf)
            else:
                raw_df = pd.read_csv(erp_buf, sep=None, engine="python")
        except (pd.errors.ParserError, ValueError) as e:
            st.error(f"Erreur de lecture brute : {e}")
            st.stop()

        st.write(f"📊 {len(raw_df):,} lignes lues, {len(raw_df.columns)} colonnes.")
        with st.expander("🔍 En-têtes détectées"):
            st.write(list(raw_df.columns))

        detected = auto_detect_preset(raw_df.columns.tolist())
        default_idx = preset_names.index(detected.name) if detected else 0
        if detected:
            st.success(f"✅ Preset auto-détecté : **{detected.label}** ({detected.name})")
        else:
            st.info("Aucun preset détecté — sélectionnez manuellement.")

        chosen_name = st.selectbox(
            "Preset",
            preset_names,
            index=default_idx,
            format_func=lambda n: preset_labels.get(n, n),
        )
        chosen = load_preset(chosen_name)

        with st.expander("ℹ️ Description du preset"):
            st.markdown(chosen.description or "—")
            st.write(
                {
                    "date_format": chosen.date_format,
                    "decimal_separator": chosen.decimal_separator,
                    "thousand_separator": chosen.thousand_separator,
                    "signature_columns": chosen.signature_columns,
                    "mapping": chosen.mapping,
                }
            )

        if st.button("🚀 Appliquer le preset", type="primary"):
            try:
                canonical_df = chosen.apply(raw_df)
            except (KeyError, ValueError) as e:
                st.error(f"Erreur d'application du preset : {e}")
                st.stop()

            missing = [
                c
                for c in ("invoice_id", "vendor_name", "amount", "invoice_date")
                if c not in canonical_df.columns
            ]
            if missing:
                st.error(f"❌ Colonnes obligatoires manquantes après mapping : {missing}")
                st.stop()

            # Drop des lignes invalides (amount NaN ou invoice_id null)
            before = len(canonical_df)
            canonical_df = canonical_df.dropna(subset=["amount", "invoice_id"]).reset_index(
                drop=True
            )
            after = len(canonical_df)
            st.success(
                f"✅ {after:,} factures importées via preset `{chosen.name}` "
                f"(filtrées : {before - after} lignes invalides)."
            )
            _persist(canonical_df, source_label=f"erp:{chosen.name}:{erp_uploaded.name}")
            _show_summary(canonical_df)


with tab_synthetic:
    st.markdown(
        "Génère un dataset réaliste avec **fraudes étiquetées** (`is_fraud`, `fraud_type`)."
        " Permet d'évaluer la précision/rappel/F1 de chaque détecteur."
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        n_invoices = st.number_input(
            "Nombre de factures", min_value=1_000, max_value=200_000, value=50_000, step=1_000
        )
    with c2:
        n_vendors = st.number_input(
            "Nombre de fournisseurs", min_value=100, max_value=20_000, value=5_000, step=100
        )
    with c3:
        seed = st.number_input("Seed", min_value=0, max_value=2**31 - 1, value=42)

    if st.button("🎲 Générer", type="primary"):
        with st.spinner("Génération en cours…"):
            cfg = GeneratorConfig(
                n_invoices=int(n_invoices), n_vendors=int(n_vendors), seed=int(seed)
            )
            invoices, vendors = generate_dataset(cfg)
        st.session_state["df_vendors"] = vendors
        _persist(invoices, source_label=f"synthetic_{n_invoices}")
        st.success(f"✅ Généré : {len(invoices):,} factures · {len(vendors):,} fournisseurs.")
        _show_summary(invoices)

with tab_sample:
    sample_path = Path(__file__).resolve().parent.parent / "data" / "samples" / "sample_5k.csv"
    st.write(
        f"Échantillon versionné : `{sample_path.relative_to(Path.cwd()) if sample_path.exists() else sample_path}`"
    )
    if sample_path.exists():
        if st.button("📦 Charger l'échantillon (5 000 lignes)"):
            df = pd.read_csv(sample_path)
            for col in ("invoice_date", "posting_date"):
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
            _persist(df, source_label="sample_5k.csv")
            st.success(f"✅ Échantillon chargé : {len(df):,} lignes.")
            _show_summary(df)
    else:
        st.warning(
            "L'échantillon n'est pas encore généré. Utilisez l'onglet « Générer un dataset » avec 5 000 lignes."
        )
