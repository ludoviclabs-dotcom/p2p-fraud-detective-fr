"""Page audit trail — visualisation et vérification d'intégrité du journal.

Le journal est partagé avec la page File d'investigation via le service
case management mis en cache (`@st.cache_resource`). Cette page est en
**lecture seule** : aucune action n'altère l'état.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from p2p_fraud.streamlit_theme import init_page
from pages._helpers import get_case_service

init_page(
    title="Piste d'audit",
    surtitle="Investigation",
    kicker=("Journal immutable hash-chaîné SHA-256"),
)
st.caption(
    "Journal immutable chaîné par hash SHA-256. Toute altération est détectable. "
    "Conforme aux exigences ISA 240 §32, AFA, ACPR (DORA art. 28)."
)


service = get_case_service()
audit = service.audit_log
entries = audit.all()

c1, c2, c3 = st.columns(3)
c1.metric("Entrées", len(entries))
c2.metric("Première (seq)", entries[0].seq if entries else 0)
c3.metric("Dernière (seq)", entries[-1].seq if entries else 0)

st.divider()
st.subheader("🔐 Vérification d'intégrité")
if st.button("Recalculer la chaîne de hash", type="primary"):
    valid, invalid = audit.verify_chain()
    if valid:
        st.success(f"✅ Chaîne valide. {len(entries)} entrées vérifiées.")
    else:
        st.error(f"❌ Chaîne altérée. Séquences invalides : {invalid}")

st.divider()
st.subheader("📋 Entrées")
if entries:
    # Filtre par seq via query_param `seq` (deep-link partageable)
    qp_seq = st.query_params.get("seq", "")
    seq_filter_str = st.text_input(
        "Filtrer par seq (deep-link `?seq=N`)",
        value=qp_seq,
        help="Saisir une séquence pour pointer une entrée précise. Vide = toutes.",
    )
    if seq_filter_str and seq_filter_str != st.query_params.get("seq"):
        st.query_params["seq"] = seq_filter_str
    elif not seq_filter_str and "seq" in st.query_params:
        del st.query_params["seq"]

    rows = [
        {
            "seq": e.seq,
            "at": e.at,
            "actor": e.actor,
            "kind": e.kind,
            "payload": e.payload,
            "prev_hash (8)": e.prev_hash[:8],
            "hash (8)": e.hash[:8],
        }
        for e in entries
    ]
    if seq_filter_str:
        try:
            target_seq = int(seq_filter_str)
            rows = [r for r in rows if r["seq"] == target_seq]
        except ValueError:
            st.warning(f"Seq invalide : `{seq_filter_str}` n'est pas un entier.")
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, height=420)

    st.subheader("📦 Export JSONL (archivage WORM)")
    if st.button("Télécharger le journal en JSON Lines"):
        export = "\n".join(audit.export_jsonl())
        st.download_button(
            "⬇️ audit_trail.jsonl",
            data=export,
            file_name="audit_trail.jsonl",
            mime="application/jsonl",
        )
else:
    st.info(
        "Aucune entrée. Direction la page **🗂️ File d'investigation** pour créer "
        "des cases — chaque action y est journalisée immédiatement."
    )
