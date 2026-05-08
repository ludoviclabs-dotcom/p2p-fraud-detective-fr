"""Helpers Streamlit partagés entre pages.

Les fichiers du dossier `pages/` qui commencent par `_` ne sont pas listés
automatiquement par Streamlit dans la sidebar — ils servent de modules
utilitaires pour les vraies pages.
"""

from __future__ import annotations

import streamlit as st

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.cases.seed import seed_demo_cases
from p2p_fraud.cases.service import CaseService


@st.cache_resource
def get_case_service() -> CaseService:
    """Service case management partagé entre toutes les pages.

    `@st.cache_resource` garantit qu'il n'y a qu'une seule instance par
    session Streamlit (et donc qu'un case créé sur la page File
    d'investigation est visible sur la page Audit trail).

    En mode vitrine (Streamlit Cloud, base éphémère), 5 cases de démo sont
    seedés au premier appel pour que les visiteurs voient immédiatement
    des dossiers réalistes.
    """
    service = CaseService(":memory:", AuditLog(":memory:"))
    seed_demo_cases(service)
    return service
