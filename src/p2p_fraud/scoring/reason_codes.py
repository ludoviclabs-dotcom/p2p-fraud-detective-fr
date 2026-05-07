"""Table de mapping rule_id -> phrase explicative en français.

Toute alerte affichée dans le cockpit ou exportée vers un comité d'audit doit
disposer d'un *reason code* lisible par un non-data-scientist. C'est aussi
l'exigence de transparence du règlement (UE) 2024/1689 (AI Act) pour les
systèmes IA à risque limité (art. 50).

Chaque template peut référencer des variables issues de `Finding.evidence` ou
des champs Finding eux-mêmes via `format_map`. Si une variable manque, le
template est rendu avec un placeholder neutre (`?`) plutôt que d'échouer.
"""

from __future__ import annotations

from dataclasses import dataclass

from p2p_fraud.schema import Finding


@dataclass(frozen=True)
class ReasonCode:
    rule_id: str
    template_fr: str
    citation: str  # référentiel d'audit / réglementation

    def render(self, finding: Finding) -> str:
        """Rendu de la phrase FR à partir du template + evidence + champs Finding."""
        ev = dict(finding.evidence or {})
        ev.setdefault("invoice_id", finding.invoice_id)
        ev.setdefault("severity", finding.severity.value)
        ev.setdefault("signal", finding.signal)
        # `format_map` avec dict tolérant aux clés manquantes.
        return self.template_fr.format_map(_SafeMap(ev))


class _SafeMap(dict):
    def __missing__(self, key: str) -> str:
        return "?"


_REASON_CODES: dict[str, ReasonCode] = {
    # --- Master data history (Sprint 1) ---
    "MD_IBAN_NO_4EYES": ReasonCode(
        rule_id="MD_IBAN_NO_4EYES",
        template_fr=(
            "IBAN modifié le {changed_at} par {changed_by} sans validation "
            "d'un second utilisateur (4-eyes manquant). "
            "Exposition financière estimée : {exposure_eur} € sur les "
            "{exposure_window_days} jours suivants."
        ),
        citation="AFP 2026 §BEC ; ISA 240 §32",
    ),
    "MD_DORMANT_REACTIVATED": ReasonCode(
        rule_id="MD_DORMANT_REACTIVATED",
        template_fr=(
            "Fournisseur inactif depuis {dormant_days} jours dont l'IBAN a "
            "été modifié juste avant un nouveau paiement. Exposition : {exposure_eur} €."
        ),
        citation="AFP 2026 ; Sapin 2 art. 17",
    ),
    "MD_NAME_AND_IBAN_SAME_DAY": ReasonCode(
        rule_id="MD_NAME_AND_IBAN_SAME_DAY",
        template_fr=(
            "Nom de fournisseur et IBAN modifiés le même jour ({iban_changed_at}) — "
            "schéma typique de clone vendor (typosquatting). "
            "Exposition : {exposure_eur} €."
        ),
        citation="ACFE Report to the Nations 2024",
    ),
    # --- Sirene (existant) ---
    "SIRENE_404": ReasonCode(
        rule_id="SIRENE_404",
        template_fr=(
            "SIREN {siren} introuvable dans le référentiel INSEE Sirene v3. "
            "Fournisseur potentiellement fictif."
        ),
        citation="ISA 240 §32 ; Sapin 2 art. 17 (3)",
    ),
    "SIRENE_CEASED": ReasonCode(
        rule_id="SIRENE_CEASED",
        template_fr=(
            "SIREN {siren} en cessation administrative (date : {closure_date}). "
            "Aucun paiement ne devrait être émis."
        ),
        citation="INSEE Sirene v3",
    ),
    "SIRENE_NEW_VENDOR": ReasonCode(
        rule_id="SIRENE_NEW_VENDOR",
        template_fr=(
            "Fournisseur créé le {creation_date} et déjà facturé le "
            "{first_invoice_date} (écart : {gap_days} jours). "
            "Vérifier la légitimité du référencement."
        ),
        citation="Sapin 2 art. 17 ; AFA Recommandations",
    ),
    # --- Sanctions / PEP (Sprint 2) ---
    "SANCTIONS_VENDOR_HIT": ReasonCode(
        rule_id="SANCTIONS_VENDOR_HIT",
        template_fr=(
            "Fournisseur '{vendor_name}' correspond à l'entité sanctionnée "
            "'{matched_name}' ({list_source}, {country}, score {score}/100). "
            "Motif : {reason}."
        ),
        citation="LCB-FT ; Règl. UE 2580/2001 ; OFAC",
    ),
    "SANCTIONS_VENDOR_PEP": ReasonCode(
        rule_id="SANCTIONS_VENDOR_PEP",
        template_fr=(
            "Fournisseur '{vendor_name}' correspond à une personne politiquement "
            "exposée '{matched_name}' ({list_source}). Vigilance renforcée requise."
        ),
        citation="LCB-FT ; Sapin 2 art. 17 (3)",
    ),
    # --- Doublons ---
    "DUP_EXACT": ReasonCode(
        rule_id="DUP_EXACT",
        template_fr=(
            "Doublon exact détecté avec la facture {duplicate_of}. "
            "Risque de double paiement."
        ),
        citation="AICPA Audit Data Standards",
    ),
    "DUP_FUZZY": ReasonCode(
        rule_id="DUP_FUZZY",
        template_fr=(
            "Doublon probable avec la facture {duplicate_of} (similarité nom : "
            "{name_similarity}, écart montant : {amount_delta} €, écart date : "
            "{date_delta_days} j)."
        ),
        citation="AICPA Audit Data Standards",
    ),
    # --- Sous-seuils ---
    "THRESHOLD_NEAR_LIMIT": ReasonCode(
        rule_id="THRESHOLD_NEAR_LIMIT",
        template_fr=(
            "Montant {amount} € positionné juste sous le seuil de validation "
            "{threshold} € (écart : {delta} €) — schéma classique de "
            "contournement du contrôle quatre yeux."
        ),
        citation="ICFR / SOX ; Code de la commande publique pour le secteur public",
    ),
    # --- Isolation Forest ---
    "IFOREST_ANOMALY": ReasonCode(
        rule_id="IFOREST_ANOMALY",
        template_fr=(
            "Comportement statistiquement atypique (Isolation Forest, score "
            "{anomaly_score}). Variables contributives dominantes : {top_features}."
        ),
        citation="ML anomaly detection (modèle non supervisé)",
    ),
    # --- Graphe / anneaux ---
    "GRAPH_RING_SHARED_IBAN": ReasonCode(
        rule_id="GRAPH_RING_SHARED_IBAN",
        template_fr=(
            "Anneau de fraude détecté : {ring_size} fournisseurs distincts "
            "partagent l'IBAN '{shared_iban}'. Cluster ID : {cluster_id}."
        ),
        citation="Forensic accounting ; ACFE",
    ),
}


def get_reason_code(rule_id: str) -> ReasonCode | None:
    return _REASON_CODES.get(rule_id)


def render_reason(finding: Finding) -> str:
    """Renvoie la phrase FR explicable pour un Finding.

    Si aucun reason code n'est défini pour le `rule_id`, retourne un fallback
    générique mais toujours lisible (pas un crash, c'est une exigence UX).
    """
    rc = _REASON_CODES.get(finding.rule_id)
    if rc:
        return rc.render(finding)
    return (
        f"Anomalie détectée par le détecteur '{finding.detector}' "
        f"(règle {finding.rule_id}, sévérité {finding.severity.value})."
    )


def list_supported_rules() -> list[str]:
    return sorted(_REASON_CODES.keys())
