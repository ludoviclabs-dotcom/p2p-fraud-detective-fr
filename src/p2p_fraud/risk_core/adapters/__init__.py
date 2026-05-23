"""Adapters — branchent les détecteurs P2P existants sur l'interface `RiskRule`.

Le principe : ne pas réécrire les détecteurs P2P historiques (master_data,
sanctions, duplicates, etc.). Les exposer comme `RiskRule` via des adaptateurs
fins qui :
- convertissent leur output (`list[Finding]`) en `list[RiskSignal]` ;
- attribuent un score par sévérité cohérent avec le scoring Risk Core (spec §06) ;
- mappent leur `rule_id` historique sur un `code` canonique du registre.

Cela valide que l'abstraction Risk Core est utilisable sans casser l'existant
et prépare l'ajout de règles SEPA natives en Sprint 2.
"""

from p2p_fraud.risk_core.adapters.finding_bridge import (
    DEFAULT_SCORE_BY_SEVERITY,
    finding_to_signal,
)

__all__ = ["DEFAULT_SCORE_BY_SEVERITY", "finding_to_signal"]
