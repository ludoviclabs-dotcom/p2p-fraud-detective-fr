"""Page audit trail — visualisation et vérification d'intégrité du journal.

Le journal est partagé avec la page File d'investigation via le service
case management mis en cache (`@st.cache_resource`). Cette page est en
**lecture seule** : aucune action n'altère l'état.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from pages._helpers import get_case_service

st.set_page_config(
    page_title="Audit trail — P2P Fraud Detective",
    page_icon="📜",
    layout="wide",
)
st.title("📜 Audit trail (lecture seule)")
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
    df = pd.DataFrame(
        [
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
    )
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
