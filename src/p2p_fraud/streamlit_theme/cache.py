"""Wrappers Streamlit avec `@st.cache_data` autour des clients d'enrichissement.

Les clients du cœur métier (`SireneClient`, `SanctionsClient`) sont
indépendants de Streamlit. Ce module ajoute une couche de cache au niveau
de la session Streamlit : on évite de re-interroger Sirene à chaque rerun
et de re-charger le snapshot sanctions à chaque navigation entre pages.

TTL choisis :
- Sirene : 1 h (les données INSEE bougent à la journée)
- Sanctions : 24 h (snapshot embarqué, pas de raison de re-charger souvent)
"""

from __future__ import annotations

import streamlit as st

from p2p_fraud.enrichment.sanctions_client import SanctionMatch, SanctionsClient
from p2p_fraud.enrichment.sirene_client import SireneClient, SireneRecord


@st.cache_data(ttl=3600, show_spinner="Interrogation INSEE Sirene…")
def cached_lookup_siren(siren: str, *, _client_token: str = "default") -> SireneRecord | None:
    """Wrapper cache pour `SireneClient.lookup_siren`.

    `_client_token` permet d'invalider manuellement le cache si la config
    du client change (ex. nouveau token API, mode offline). Par défaut,
    une seule instance partagée est utilisée.
    """
    del _client_token  # le token ne sert qu'à isoler la clé de cache
    client = _get_sirene_client()
    return client.lookup_siren(siren)


@st.cache_data(ttl=86400, show_spinner="Recherche sanctions / PEP…")
def cached_sanctions_search(
    query: str,
    *,
    country: str | None = None,
    _client_token: str = "default",
) -> list[SanctionMatch]:
    """Wrapper cache pour `SanctionsClient.search`.

    Chaque tuple `(query, country)` est mémoïsé pour la session — on évite
    de re-tokeniser et re-comparer les listes pour la même requête après
    re-run Streamlit.
    """
    del _client_token
    client = _get_sanctions_client()
    return client.search(query, country=country)


@st.cache_resource(show_spinner=False)
def _get_sirene_client() -> SireneClient:
    """Instance unique de `SireneClient` partagée entre pages (session)."""
    return SireneClient()


@st.cache_resource(show_spinner=False)
def _get_sanctions_client() -> SanctionsClient:
    """Instance unique de `SanctionsClient` partagée entre pages (session)."""
    return SanctionsClient()
