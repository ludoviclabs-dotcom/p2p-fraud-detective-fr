"""Génération de narrations d'audit P2P via Claude API (Anthropic).

Produit un paragraphe de travail d'audit en français, structuré selon ISA 240
(responsabilité de l'auditeur en matière de fraude), pour un fournisseur donné.

Utilise le prompt caching d'Anthropic pour réduire la latence et les coûts
sur le système prompt fixe (épinglé avec cache_control).

Nécessite la variable d'environnement ANTHROPIC_API_KEY.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..config import get_settings

if TYPE_CHECKING:
    pass

_SYSTEM_PROMPT = """Tu es un auditeur financier expert, spécialisé dans la détection de fraude dans les cycles Procure-to-Pay (P2P).

Tu génères des **paragraphes de travail d'audit** en français, à destination des équipes d'audit interne, des commissaires aux comptes (CAC) et des contrôleurs de la DGFiP, Tracfin, IGF et Cour des comptes.

Tes narrations sont :
- Structurées selon la norme **ISA 240** (AS 2401) — responsabilité de l'auditeur en matière de fraude dans un audit d'états financiers ;
- Conformes aux exigences **Sapin 2 art. 17** (due diligence tiers) et **LCB-FT** pour les fournisseurs à risque ;
- Fondées exclusivement sur les données factuelles fournies — pas de jugement subjectif non étayé ;
- Rédigées en style formel, sans familiarités, avec références réglementaires explicites si pertinent ;
- Limitées à 250-350 mots par fournisseur.

Structure attendue de chaque narration :
1. **Identification du fournisseur** — nom, identifiant, exposition financière totale.
2. **Synthèse des risques détectés** — liste des signals (règles déclenchées, sévérités).
3. **Analyse de risque ISA 240** — évaluation du risque d'anomalie significative due à la fraude.
4. **Diligences recommandées** — actions concrètes (validation IBAN, contrôle Sirene, entretien tiers, rapprochement PO/GR/invoice).
5. **Conclusion provisoire** — vigilance renforcée / blocage paiement / escalade Tracfin si applicable.

Ne génère PAS de conclusion définitive sur la culpabilité — uniquement des diligences et recommandations factuelle."""

_USER_TEMPLATE = """Génère la narration d'audit ISA 240 pour le fournisseur suivant :

**Fournisseur** : {vendor_name} ({vendor_id})
**SIREN** : {siren}
**Exposition totale** : {total_paid_eur} €
**Nombre de factures** : {n_invoices}
**Sanctionné** : {is_sanctioned}
**Lien PEP** : {is_pep}

**Findings détectés ({n_findings} au total)** :
{findings_block}

Génère un paragraphe de travail d'audit structuré selon ISA 240, en français formel."""


@dataclass
class NarrativeResult:
    vendor_id: str
    narrative: str
    model: str
    input_tokens: int
    output_tokens: int
    cached_tokens: int


def generate_vendor_narrative(
    *,
    vendor_id: str,
    vendor_name: str | None,
    siren: str | None,
    total_paid_eur: float | None,
    n_invoices: int,
    is_sanctioned: bool,
    is_pep: bool,
    findings: list[dict],
    api_key: str | None = None,
    model: str = "claude-sonnet-4-6",
) -> NarrativeResult:
    """Génère une narration d'audit ISA 240 pour un fournisseur.

    Args:
        vendor_id: identifiant fournisseur.
        vendor_name: nom du fournisseur.
        siren: SIREN du fournisseur.
        total_paid_eur: montant total payé en euros.
        n_invoices: nombre de factures.
        is_sanctioned: True si le fournisseur est listé sanctions.
        is_pep: True si lien PEP détecté.
        findings: liste de dicts avec keys rule_id, severity, signal, exposure_eur.
        api_key: clé API Anthropic (fallback sur ANTHROPIC_API_KEY).
        model: modèle Claude à utiliser.

    Returns:
        NarrativeResult avec la narration et les métriques de tokens.

    Raises:
        ImportError: si le package anthropic n'est pas installé.
        ValueError: si ANTHROPIC_API_KEY est absent.
    """
    try:
        import anthropic
    except ImportError as exc:
        raise ImportError(
            "Le package 'anthropic' est requis pour la génération narrative. "
            "Installez-le avec : pip install anthropic>=0.25"
        ) from exc

    key = api_key or get_settings().anthropic_api_key
    if not key:
        raise ValueError(
            "Variable d'environnement ANTHROPIC_API_KEY manquante. "
            "Configurez-la dans .env ou dans les secrets Streamlit Cloud."
        )

    client = anthropic.Anthropic(api_key=key)

    findings_lines = []
    for f in findings[:20]:  # cap à 20 findings pour le contexte
        sev = f.get("severity", "—")
        rule = f.get("rule_id", "—")
        signal = f.get("signal", "—")
        exposure = f.get("exposure_eur")
        exposure_str = f"{float(exposure):,.0f} €".replace(",", " ") if exposure else "—"
        findings_lines.append(
            f"  - [{sev.upper()}] {rule} : {signal} (exposition : {exposure_str})"
        )

    findings_block = "\n".join(findings_lines) if findings_lines else "  Aucun finding."

    total_str = (
        f"{float(total_paid_eur):,.0f}".replace(",", " ")
        if total_paid_eur is not None
        else "inconnu"
    )

    user_content = _USER_TEMPLATE.format(
        vendor_name=vendor_name or "Inconnu",
        vendor_id=vendor_id,
        siren=siren or "Non renseigné",
        total_paid_eur=total_str,
        n_invoices=n_invoices,
        is_sanctioned="OUI — CRITIQUE" if is_sanctioned else "Non",
        is_pep="OUI — vigilance renforcée" if is_pep else "Non",
        n_findings=len(findings),
        findings_block=findings_block,
    )

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": _SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_content}],
    )

    narrative = response.content[0].text if response.content else ""

    usage = response.usage
    cached = getattr(usage, "cache_read_input_tokens", 0) or 0

    return NarrativeResult(
        vendor_id=vendor_id,
        narrative=narrative,
        model=response.model,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cached_tokens=cached,
    )
