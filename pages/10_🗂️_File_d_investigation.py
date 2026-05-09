"""Page file d'investigation — case management v0.

Crée des cases depuis les findings de la session, permet assignation, commentaire,
escalade et clôture motivée.
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd
import streamlit as st

from p2p_fraud.cases.models import CaseStatus
from p2p_fraud.cases.service import CaseClosedError
from p2p_fraud.schema import Finding
from p2p_fraud.streamlit_theme import init_page
from pages._helpers import get_case_service

init_page(
    title="File d'investigation",
    surtitle="Pilotage",
    kicker=("Case management + audit log immutable"),
)
st.caption(
    "Case management v0 avec audit log immutable chaîné par hash SHA-256. "
    "Toute mutation est journalisée et vérifiable."
)


service = get_case_service()


def _collect_session_findings() -> list[Finding]:
    keys: Iterable[str] = (
        "findings_master_data",
        "findings_sanctions",
        "findings_benford",
        "findings_duplicates",
        "findings_thresholds",
        "findings_sirene",
        "findings_isolation_forest",
        "findings_graph",
    )
    out: list[Finding] = []
    for k in keys:
        v = st.session_state.get(k)
        if v:
            out.extend(v)
    return out


actor = st.text_input(
    "Utilisateur courant (actor pour l'audit log)",
    value=st.session_state.get("current_user", "auditeur.demo"),
)
st.session_state["current_user"] = actor

st.divider()
st.subheader("➕ Créer un case depuis un finding")

available = _collect_session_findings()
if not available:
    st.info(
        "Aucun finding en session. Lancez d'abord les détecteurs (master data, "
        "sanctions, doublons, etc.) puis revenez ici."
    )
else:
    options = {
        f"{f.detector} · {f.rule_id} · {f.invoice_id} ({f.severity.value})": i
        for i, f in enumerate(available)
    }
    pick_label = st.selectbox("Finding", list(options.keys()))
    if st.button("Créer un case", type="primary"):
        idx = options[pick_label]
        finding = available[idx]
        case = service.create_case_from_finding(finding, actor=actor)
        st.success(f"Case `{case.case_id}` créé (sévérité {case.severity}).")

st.divider()
st.subheader("🗂️ Cases ouverts")

cases = service.list_cases()
if not cases:
    st.write("Aucun case enregistré.")
else:
    df = pd.DataFrame(
        [
            {
                "case_id": c.case_id,
                "status": c.status.value,
                "severity": c.severity,
                "vendor_id": c.vendor_id,
                "exposure_eur": c.exposure_eur,
                "assignee": c.assignee,
                "title": c.title,
                "created_at": c.created_at,
                "closed_at": c.closed_at,
                "closure_reason": c.closure_reason,
            }
            for c in cases
        ]
    ).sort_values("exposure_eur", ascending=False, na_position="last")
    st.dataframe(df, use_container_width=True, height=320)

    case_ids = [c.case_id for c in cases]
    qp_case = st.query_params.get("case_id", "")
    default_idx = case_ids.index(qp_case) if qp_case in case_ids else 0
    selected = st.selectbox(
        "Case à inspecter / muter",
        case_ids,
        index=default_idx,
        key="selected_case",
    )
    if selected and selected != st.query_params.get("case_id"):
        st.query_params["case_id"] = selected
    case = service.get(selected)
    st.markdown(f"**Statut** : `{case.status.value}` · **Assignee** : {case.assignee or '—'}")

    cols = st.columns(4)
    with cols[0]:
        new_assignee = st.text_input("Assigner à", key=f"assign_{selected}")
        if st.button("Assigner", key=f"btn_assign_{selected}"):
            try:
                service.assign(selected, new_assignee, actor=actor)
                st.success("Assigné.")
                st.rerun()
            except CaseClosedError as e:
                st.error(str(e))

    with cols[1]:
        comment_text = st.text_input("Commentaire", key=f"comment_{selected}")
        if st.button("Commenter", key=f"btn_comment_{selected}"):
            service.comment(selected, actor=actor, text=comment_text)
            st.success("Commentaire ajouté.")
            st.rerun()

    with cols[2]:
        esc_reason = st.text_input("Motif d'escalade", key=f"esc_{selected}")
        if st.button("Escalader", key=f"btn_esc_{selected}"):
            try:
                service.escalate(selected, actor=actor, channel="legal", reason=esc_reason)
                st.success("Escaladé.")
                st.rerun()
            except CaseClosedError as e:
                st.error(str(e))

    with cols[3]:
        closure_status = st.selectbox(
            "Clôture",
            [
                CaseStatus.CLOSED_CONFIRMED.value,
                CaseStatus.CLOSED_REJECTED.value,
                CaseStatus.CLOSED_FALSE_POSITIVE.value,
            ],
            key=f"close_status_{selected}",
        )
        closure_reason = st.text_input("Motif (obligatoire)", key=f"close_reason_{selected}")
        if st.button("Clore", key=f"btn_close_{selected}"):
            try:
                service.close(
                    selected,
                    CaseStatus(closure_status),
                    actor=actor,
                    reason=closure_reason,
                )
                st.success("Case clos.")
                st.rerun()
            except (ValueError, CaseClosedError) as e:
                st.error(str(e))

    st.divider()
    st.subheader("📜 Historique des événements")
    events = service.list_events(selected)
    if events:
        st.dataframe(
            pd.DataFrame(
                [
                    {"at": e.at, "actor": e.actor, "kind": e.kind, "payload": e.payload}
                    for e in events
                ]
            ),
            use_container_width=True,
        )
