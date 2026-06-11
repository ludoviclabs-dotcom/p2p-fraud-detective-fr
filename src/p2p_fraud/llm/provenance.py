"""Source pack et validation de provenance des sorties IA (ADR-0007).

Principe : le modèle reçoit un *source pack* (faits numérotés produits par le
code déterministe) et doit citer les `source_ids` utilisés pour chaque
affirmation. Ce module vérifie EN CODE que :

1. chaque `source_id` cité existe réellement dans le source pack ;
2. chaque affirmation cite au moins une source.

Toute violation est remontée — le caller décide de rejeter la sortie ou de
marquer les affirmations fautives. On ne fait jamais confiance au modèle
pour la citation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from p2p_fraud.llm.schemas import GroundedClaim


@dataclass(frozen=True)
class SourceItem:
    """Un fait vérifiable fourni au modèle, identifié de façon stable."""

    source_id: str
    label: str
    value: Any

    def render(self) -> str:
        return f"[{self.source_id}] {self.label} : {self.value}"


@dataclass
class SourcePack:
    """Ensemble des faits que le modèle a le droit de citer."""

    items: list[SourceItem] = field(default_factory=list)

    def add(self, source_id: str, label: str, value: Any) -> None:
        if any(item.source_id == source_id for item in self.items):
            raise ValueError(f"source_id dupliqué : {source_id}")
        self.items.append(SourceItem(source_id=source_id, label=label, value=value))

    @property
    def ids(self) -> set[str]:
        return {item.source_id for item in self.items}

    def render(self) -> str:
        """Bloc texte injecté dans le prompt — une ligne par source."""
        return "\n".join(item.render() for item in self.items)


class ProvenanceError(ValueError):
    """La sortie IA cite des sources inexistantes ou omet de sourcer."""


@dataclass(frozen=True)
class ProvenanceReport:
    """Résultat de la validation de provenance d'une sortie IA."""

    valid: bool
    unknown_ids: dict[str, list[str]]  # texte du claim → ids cités mais inconnus
    unsourced_claims: list[str]  # claims sans aucune source

    def raise_if_invalid(self) -> None:
        if self.valid:
            return
        problems: list[str] = []
        if self.unknown_ids:
            problems.append(f"{len(self.unknown_ids)} claim(s) citant des sources inconnues")
        if self.unsourced_claims:
            problems.append(f"{len(self.unsourced_claims)} claim(s) sans source")
        raise ProvenanceError("Provenance invalide : " + " ; ".join(problems))


def validate_provenance(
    claims: list[GroundedClaim],
    source_pack: SourcePack,
) -> ProvenanceReport:
    """Vérifie que chaque claim cite uniquement des sources existantes.

    Retourne un rapport ; utiliser `raise_if_invalid()` pour un comportement
    fail-closed, ou inspecter les champs pour marquer les claims fautifs.
    """
    known = source_pack.ids
    unknown_ids: dict[str, list[str]] = {}
    unsourced: list[str] = []
    for claim in claims:
        if not claim.source_ids:
            unsourced.append(claim.text)
            continue
        bad = [sid for sid in claim.source_ids if sid not in known]
        if bad:
            unknown_ids[claim.text] = bad
    return ProvenanceReport(
        valid=not unknown_ids and not unsourced,
        unknown_ids=unknown_ids,
        unsourced_claims=unsourced,
    )
