"""Page file d'investigation — case management v0.

Crée des cases depuis les findings de la session, permet assignation, commentaire,
escalade et clôture motivée. Tableau AgGrid avec sélection de ligne persistée.
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, DataReturnMode, GridOptionsBuilder, GridUpdateMode

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

    # AgGrid : sélection multiple (checkbox) — bulk ops P5-3
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_selection(
        "multiple",
        use_checkbox=True,
        header_checkbox=True,
        pre_selected_rows=[0],
    )
    gb.configure_column(
        "exposure_eur",
        header_name="Exposition €",
        type=["numericColumn"],
        valueFormatter="'€ ' + value?.toLocaleString('fr-FR', {maximumFractionDigits:0})",
    )
    gb.configure_column("case_id", header_name="Case ID")
    gb.configure_column("status", header_name="Statut")
    gb.configure_column("severity", header_name="Sévérité")
    gb.configure_column("title", flex=2)
    gb.configure_default_column(sortable=True, filter=True, resizable=True)
    gb.configure_grid_options(domLayout="normal")
    grid_options = gb.build()

    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        height=320,
        use_container_width=True,
        allow_unsafe_jscode=True,
    )

    # Résoudre le case sélectionné (AgGrid ou query_param)
    selected_rows = grid_response.get("selected_rows")
    case_ids = [c.case_id for c in cases]
    qp_case = st.query_params.get("case_id", "")

    # Extraction de la liste complète des sélections (bulk ops P5-3)
    selected_ids: list[str] = []
    if selected_rows is not None and len(selected_rows) > 0:
        if isinstance(selected_rows, pd.DataFrame):
            selected_ids = [str(c) for c in selected_rows["case_id"].tolist()]
        else:
            selected_ids = [str(r["case_id"]) for r in selected_rows]

    if selected_ids:
        selected_case_id = selected_ids[0]
    elif qp_case in case_ids:
        selected_case_id = qp_case
    else:
        selected_case_id = case_ids[0]

    # ─── Bulk operations (P5-3) ──────────────────────────────────────────
    if len(selected_ids) >= 2:
        st.markdown(f"#### 🧰 Actions groupées sur **{len(selected_ids)} cases** sélectionnés")
        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            bulk_assignee = st.text_input(
                "Assigner à",
                value=actor,
                key="bulk_assignee",
                placeholder="email ou identifiant",
            )
            if st.button(
                f"👥 Assigner {len(selected_ids)} cases",
                key="bulk_assign",
                use_container_width=True,
            ):
                done = 0
                errors = 0
                for cid in selected_ids:
                    try:
                        service.assign(cid, bulk_assignee, actor=actor)
                        done += 1
                    except Exception:
                        errors += 1
                st.success(f"Bulk assign : {done} OK, {errors} erreurs")
                st.rerun()
        with bc2:
            bulk_reason = st.text_input(
                "Motif de clôture commun",
                key="bulk_close_reason",
                placeholder="ex. faux positif — qualifié.",
            )
            if st.button(
                f"✅ Clôturer {len(selected_ids)} cases (false positive)",
                key="bulk_close",
                use_container_width=True,
            ):
                if not bulk_reason.strip():
                    st.error("Motif obligatoire pour clôturer plusieurs cases.")
                else:
                    done = 0
                    errors = 0
                    for cid in selected_ids:
                        try:
                            service.close(
                                cid,
                                CaseStatus.CLOSED_FALSE_POSITIVE,
                                actor=actor,
                                reason=bulk_reason.strip(),
                            )
                            done += 1
                        except Exception:
                            errors += 1
                    st.success(f"Bulk close : {done} OK, {errors} erreurs")
                    st.rerun()
        with bc3:
            if st.button(
                f"📥 Exporter {len(selected_ids)} cases (CSV)",
                key="bulk_export",
                use_container_width=True,
            ):
                subset = df[df["case_id"].isin(selected_ids)]
                st.download_button(
                    "⬇️ Télécharger la sélection",
                    data=subset.to_csv(index=False).encode("utf-8"),
                    file_name=f"cases_selection_{len(selected_ids)}.csv",
                    mime="text/csv",
                    key="bulk_export_dl",
                )

    default_idx = case_ids.index(selected_case_id) if selected_case_id in case_ids else 0
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
