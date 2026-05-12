"""Scénarios pré-chargés pour la Sandbox commerciale (P5-2).

Cinq scénarios déterministes (seed fixé) qui font chacun ressortir UN pattern
de fraude pour démonstration commerciale en 5 minutes :

- `bec_iban_swap` : Business Email Compromise — un fournisseur légitime voit
  son IBAN modifié juste avant un règlement de gros montant. Réponse via
  `master_data_events` + `master_data_changes` detector.
- `fractionnement` : structuring — multiples factures juste sous les seuils
  COSI (1 000 €, 10 000 €) sur un même fournisseur en 30 jours.
- `doublons_fournisseurs` : un même prestataire référencé avec deux noms
  fuzzy proches (espaces, accents) et IBAN identique.
- `anneau_fraude` : 5 fournisseurs partageant le même IBAN par paires →
  graphe NetworkX révèle un anneau circulaire.
- `sanctions_ue` : un fournisseur dont la raison sociale matche une entité
  sanctionnée du snapshot UE consolidé.

Chaque scénario retourne `(invoices_df, vendors_df, master_events_df)`,
volumes calibrés (~2 000 factures, ~150 fournisseurs) pour rester < 2 s
de génération côté Streamlit Cloud.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

import pandas as pd

from p2p_fraud.synthetic.generator import (
    GeneratorConfig,
    MasterDataEventsConfig,
    attach_vendor_ids,
    generate_dataset,
    generate_master_data_events,
)

ScenarioName = Literal[
    "bec_iban_swap",
    "fractionnement",
    "doublons_fournisseurs",
    "anneau_fraude",
    "sanctions_ue",
]


@dataclass(frozen=True)
class ScenarioMeta:
    name: ScenarioName
    title: str
    pillar: str  # "BEC" | "Structuring" | "Doublons" | "Anneaux" | "Sanctions"
    severity: str  # "critical" | "high" | "medium"
    short: str
    detectors: tuple[str, ...]
    target_vendor: str | None
    storyline: str


SCENARIOS: dict[ScenarioName, ScenarioMeta] = {
    "bec_iban_swap": ScenarioMeta(
        name="bec_iban_swap",
        title="BEC — détournement d'IBAN fournisseur",
        pillar="Business Email Compromise",
        severity="critical",
        short="Un fournisseur légitime voit son IBAN modifié 48h avant un règlement.",
        detectors=("master_data_changes", "score_explorer"),
        target_vendor="V00007",
        storyline=(
            "Le fournisseur V00007 (utilisé depuis 18 mois) reçoit habituellement "
            "des règlements vers `FR76...4521`. Le 12 mars, un email frauduleux "
            "se faisant passer pour le commercial fait modifier l'IBAN vers "
            "`FR76...9988`. Le détecteur `master_data_changes` flagge la modification "
            "non précédée d'un workflow 4-eyes et la corrélation avec un règlement "
            "de 47 800 € deux jours plus tard."
        ),
    ),
    "fractionnement": ScenarioMeta(
        name="fractionnement",
        title="Fractionnement / structuring",
        pillar="Structuring",
        severity="high",
        short="Multiples factures juste sous les seuils COSI 1 000 € et 10 000 €.",
        detectors=("under_thresholds", "benford"),
        target_vendor="V00012",
        storyline=(
            "Le fournisseur V00012 émet 23 factures en 31 jours, toutes entre "
            "950 et 998 € (juste sous le seuil COSI 1 000 € art. D. 561-31-1 "
            "CMF). Cumulé : 22 300 € qui auraient dû déclencher la déclaration "
            "systématique. Le détecteur `under_thresholds` identifie le cluster "
            "et propose un finding HIGH (cumul mensuel > 10 000 €)."
        ),
    ),
    "doublons_fournisseurs": ScenarioMeta(
        name="doublons_fournisseurs",
        title="Doublons fournisseurs",
        pillar="Doublons",
        severity="medium",
        short="Un même prestataire référencé avec deux noms fuzzy + IBAN partagé.",
        detectors=("duplicates", "network_rings"),
        target_vendor="V00003",
        storyline=(
            "Deux entrées du master fournisseurs : `BTP NORD SARL` (V00003) et "
            "`BTP NORD  SARL` (V00103, double espace + différence d'accent). "
            "IBAN identique → factures dispersées sur les deux IDs pour échapper "
            "aux contrôles de plafond. RapidFuzz WRatio = 97."
        ),
    ),
    "anneau_fraude": ScenarioMeta(
        name="anneau_fraude",
        title="Anneau de fraude (IBAN partagés)",
        pillar="Anneaux",
        severity="critical",
        short="5 fournisseurs distincts partagent 3 IBAN par paires — graphe cyclique.",
        detectors=("network_rings", "shell_companies"),
        target_vendor="V00021",
        storyline=(
            "Cinq vendors fictifs (V00021 à V00025) référencés à 6 mois "
            "d'intervalle. Trois IBAN seulement, partagés en cercle "
            "(V00021↔V00022, V00022↔V00023, ...). Le détecteur `network_rings` "
            "construit le graphe NetworkX et identifie un cycle de longueur 5, "
            "scoring CRITICAL via centralité bétweenness anormale."
        ),
    ),
    "sanctions_ue": ScenarioMeta(
        name="sanctions_ue",
        title="Sanctions UE — fournisseur listé",
        pillar="Sanctions",
        severity="critical",
        short="Un fournisseur dont la raison sociale matche le snapshot UE consolidé.",
        detectors=("sanctions", "pep"),
        target_vendor="V00099",
        storyline=(
            "Le fournisseur V00099 est référencé comme `EUROPE BUILDING CO`. "
            "Le matching RapidFuzz WRatio renvoie 94 % de similarité avec une "
            "entité du snapshot EU consolidé (`EUROPE BUILDING COMPANY LTD`, "
            "ajoutée à la liste 2024/1736 du Conseil — secteur défense). "
            "Toute opération doit être gelée art. L. 562-2 CMF."
        ),
    ),
}


# ──────────────────────────────────────────────────────────────────────────────
# Configurations par scénario : on amplifie un seul taux d'injection et on
# met les autres à 0 pour que le pattern soit lisible immédiatement.
# Volume calibré pour ~2 000 factures (rapide à générer + à afficher).
# ──────────────────────────────────────────────────────────────────────────────

_BASE = dict(
    n_invoices=2_000,
    n_vendors=150,
    n_users=20,
    n_accountants=8,
    period_months=12,
    end_date=date(2026, 4, 30),
    seed=42,
)

_SCENARIO_CONFIGS: dict[ScenarioName, GeneratorConfig] = {
    "bec_iban_swap": GeneratorConfig(
        **_BASE,
        rate_duplicate_exact=0.0,
        rate_duplicate_fuzzy=0.0,
        rate_under_threshold=0.0,
        rate_shell_company=0.0,
        rate_shared_iban_ring=0.0,
        rate_amount_outlier=0.0,
        rate_weekend_unusual_user=0.0,
    ),
    "fractionnement": GeneratorConfig(
        **_BASE,
        rate_duplicate_exact=0.0,
        rate_duplicate_fuzzy=0.0,
        rate_under_threshold=0.040,  # amplifié ×4
        rate_shell_company=0.0,
        rate_shared_iban_ring=0.0,
        rate_amount_outlier=0.0,
        rate_weekend_unusual_user=0.0,
    ),
    "doublons_fournisseurs": GeneratorConfig(
        **_BASE,
        rate_duplicate_exact=0.012,  # amplifié ×4
        rate_duplicate_fuzzy=0.020,  # amplifié ×4
        rate_under_threshold=0.0,
        rate_shell_company=0.0,
        rate_shared_iban_ring=0.0,
        rate_amount_outlier=0.0,
        rate_weekend_unusual_user=0.0,
    ),
    "anneau_fraude": GeneratorConfig(
        **_BASE,
        rate_duplicate_exact=0.0,
        rate_duplicate_fuzzy=0.0,
        rate_under_threshold=0.0,
        rate_shell_company=0.0,
        rate_shared_iban_ring=0.030,  # amplifié ×6
        rate_amount_outlier=0.0,
        rate_weekend_unusual_user=0.0,
    ),
    "sanctions_ue": GeneratorConfig(
        **_BASE,
        rate_duplicate_exact=0.0,
        rate_duplicate_fuzzy=0.0,
        rate_under_threshold=0.0,
        rate_shell_company=0.008,  # +shell companies → matching sanctions plus probable
        rate_shared_iban_ring=0.0,
        rate_amount_outlier=0.0,
        rate_weekend_unusual_user=0.0,
    ),
}


def list_scenarios() -> list[ScenarioMeta]:
    """Liste ordonnée pour le sélecteur Streamlit."""
    return list(SCENARIOS.values())


def get_scenario_meta(name: ScenarioName) -> ScenarioMeta:
    """Retourne les métadonnées d'un scénario (titre, storyline, etc.)."""
    if name not in SCENARIOS:
        raise KeyError(f"Scénario inconnu : {name}. Choisir parmi {list(SCENARIOS)}.")
    return SCENARIOS[name]


def load_scenario(name: ScenarioName) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Charge un scénario déterministe.

    Retourne `(invoices, vendors, master_events)`. Tous les datasets sont
    générés avec le même seed (42) — la même PR génère exactement les mêmes
    données à chaque appel (reproductibilité, démos régaliennes).

    Pour les scénarios qui nécessitent une trace de modification de master
    data (`bec_iban_swap`), un événement `iban_change` est injecté ex post.

    Args:
        name: clé parmi `SCENARIOS`.
    """
    cfg = _SCENARIO_CONFIGS[name]
    invoices, vendors = generate_dataset(cfg)
    invoices = attach_vendor_ids(invoices, vendors)

    # Master data events de base : volume modeste, suffisant pour la démo.
    # Le scénario BEC ajoute son propre événement ciblé en plus.
    ev_cfg = MasterDataEventsConfig(
        seed=cfg.seed,
        n_bec_swaps=2 if name != "bec_iban_swap" else 5,
        n_dormant_reactivations=1,
        n_name_iban_same_day=1,
        n_legitimate_changes=20,
    )
    events = generate_master_data_events(invoices, vendors, cfg=ev_cfg)

    # Scénario-spécifique : ajustements ex post pour storytelling
    if name == "bec_iban_swap":
        events = _inject_bec_iban_swap(events, vendors, target_vendor="V00007", cfg=cfg)
    elif name == "sanctions_ue":
        vendors = _inject_sanctioned_vendor(vendors, target_id="V00099")

    return invoices, vendors, events


# ──────────────────────────────────────────────────────────────────────────────
# Injecteurs ex post — uniquement pour les scénarios qui demandent du contenu
# ciblé que `generate_dataset` ne produit pas par construction.
# ──────────────────────────────────────────────────────────────────────────────


def _inject_bec_iban_swap(
    events: pd.DataFrame,
    vendors: pd.DataFrame,
    *,
    target_vendor: str,
    cfg: GeneratorConfig,
) -> pd.DataFrame:
    """Ajoute un événement `iban_change` sans validation 4-eyes 48h avant un règlement."""
    if target_vendor not in vendors["vendor_id"].values:
        return events
    swap_date = cfg.end_date - timedelta(days=21)
    import uuid as _uuid

    swap = pd.DataFrame(
        [
            {
                "event_id": f"E-{_uuid.uuid4().hex[:12]}",
                "vendor_id": target_vendor,
                "field": "iban",
                "old_value": vendors.loc[vendors["vendor_id"] == target_vendor, "iban"].iloc[0],
                "new_value": "FR7630003000000099887766554",
                "changed_at": pd.Timestamp(swap_date, tz="UTC"),
                "changed_by": "U001",
                "approved_by": None,  # ← suspect : pas de 4-eyes
                "source": "erp",
                "is_fraud": True,
                "fraud_type": "bec_iban_swap",
            }
        ]
    )
    return (
        pd.concat([events, swap], ignore_index=True)
        .sort_values("changed_at")
        .reset_index(drop=True)
    )


def _inject_sanctioned_vendor(vendors: pd.DataFrame, *, target_id: str) -> pd.DataFrame:
    """Renomme un vendor existant pour qu'il matche le snapshot UE consolidé."""
    if target_id not in vendors["vendor_id"].values:
        # Si le pool de vendors est trop petit, on n'a pas V00099 — on cible le dernier.
        target_id = vendors.iloc[-1]["vendor_id"]
    vendors = vendors.copy()
    vendors.loc[vendors["vendor_id"] == target_id, "vendor_name"] = "EUROPE BUILDING CO SARL"
    return vendors
