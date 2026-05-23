"""Service `SepaAnalyzer` — orchestration ingest → match → assess → audit.

Pipeline en 4 étapes :

1. `DebitEventService.ingest()` — idempotent
2. `MandateMatcher.match()` — appariement déterministe
3. `RiskEngine.assess()` — exécute les règles SEPA v0
4. `AuditLog.append("DEBIT_ANALYZED")` + `DebitEventService.mark_matched()`

L'analyzer ne persiste pas le `RiskAssessmentResult` lui-même : c'est l'API
ou le caller qui décide où le sérialiser (en réponse JSON, en
RiskAssessment SQL, en evidence pack…). Ça garde l'analyzer composable.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import Engine, text

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.persistence import make_engine
from p2p_fraud.risk_core import RiskAssessmentResult, RiskDomain, RiskEngine
from p2p_fraud.sepa.debit_event import DebitEventInput, DebitEventRecord, DebitEventService
from p2p_fraud.sepa.mandate import MandateService
from p2p_fraud.sepa.matcher import MandateMatcher, MatchResult
from p2p_fraud.sepa.rules import SepaRiskContext, build_sepa_rules

log = logging.getLogger(__name__)

SEPA_ENGINE_VERSION = "sepa-v0.1.0"

DEFAULT_RECENT_DEBITS_WINDOW_DAYS = 14


def build_sepa_engine() -> RiskEngine[SepaRiskContext]:
    """Factory de l'engine SEPA assemblant les 6 règles v0."""
    return RiskEngine(
        build_sepa_rules(),
        engine_version=SEPA_ENGINE_VERSION,
        domain=RiskDomain.SEPA_DIRECT_DEBIT,
    )


@dataclass(frozen=True)
class AnalyzedDebit:
    """Verdict complet : événement ingéré + résultat du moteur + match."""

    event: DebitEventRecord
    match: MatchResult
    assessment: RiskAssessmentResult


class SepaAnalyzer:
    """Orchestrateur de bout en bout du flux SEPA."""

    def __init__(
        self,
        *,
        engine: Engine | None = None,
        audit_log: AuditLog | None = None,
        mandate_service: MandateService | None = None,
        debit_service: DebitEventService | None = None,
        risk_engine: RiskEngine[SepaRiskContext] | None = None,
        recent_window_days: int = DEFAULT_RECENT_DEBITS_WINDOW_DAYS,
        db_path: str = ":memory:",
    ) -> None:
        self._engine = engine or make_engine(db_path=db_path)
        self._audit = audit_log or AuditLog(engine=self._engine)
        self._mandates = mandate_service or MandateService(
            engine=self._engine, audit_log=self._audit
        )
        self._debits = debit_service or DebitEventService(
            engine=self._engine, audit_log=self._audit
        )
        self._matcher = MandateMatcher(self._mandates)
        self._risk = risk_engine or build_sepa_engine()
        self._recent_window_days = recent_window_days

    @property
    def mandates(self) -> MandateService:
        return self._mandates

    @property
    def debits(self) -> DebitEventService:
        return self._debits

    @property
    def audit(self) -> AuditLog:
        return self._audit

    def analyze(
        self,
        payload: DebitEventInput,
        *,
        actor: str,
        tenant_id: str | None = None,
    ) -> AnalyzedDebit:
        """Pipeline complet : ingest → match → assess → audit."""
        event = self._debits.ingest(payload, actor=actor, tenant_id=tenant_id)
        match = self._matcher.match(event, tenant_id=tenant_id)
        recent = self._load_recent_debits(
            tenant_id=tenant_id, fingerprint=event.debtor_iban_fingerprint
        )
        ctx = SepaRiskContext(
            event=event,
            match=match,
            recent_debits=tuple(d for d in recent if d.event_id != event.event_id),
            now=datetime.now(UTC),
        )
        assessment = self._risk.assess(ctx)

        # Mémorise le match pour traçabilité
        self._debits.mark_matched(
            event.event_id,
            mandate_id=match.mandate.mandate_id if match.mandate else None,
            tenant_id=tenant_id,
        )

        self._audit.append(
            actor=actor,
            kind="DEBIT_ANALYZED",
            payload={
                "event_id": event.event_id,
                "tenant_id": tenant_id,
                "engine_version": assessment.engine_version,
                "score": assessment.score,
                "level": assessment.level.value,
                "decision": assessment.decision.value,
                "n_signals": len(assessment.signals),
                "signal_codes": [s.code for s in assessment.signals],
                "matched_mandate_id": match.mandate.mandate_id if match.mandate else None,
                "matcher_warnings": [w.value for w in match.warnings],
            },
        )
        return AnalyzedDebit(event=event, match=match, assessment=assessment)

    # ─── Privé ───────────────────────────────────────────────────────────────

    def _load_recent_debits(
        self, *, tenant_id: str | None, fingerprint: str | None
    ) -> list[DebitEventRecord]:
        if not fingerprint:
            return []
        # SQLite ne supporte pas les comparaisons date < text de façon
        # fiable ; on rapatrie les derniers événements et le filtrage
        # temporel est appliqué par la règle UnusualFrequencyRule.
        sql = "SELECT * FROM debit_events WHERE debtor_iban_fingerprint = :fp "
        params: dict = {"fp": fingerprint}
        if tenant_id is not None:
            sql += "AND COALESCE(tenant_id,'') = COALESCE(:tid,'') "
            params["tid"] = tenant_id
        sql += "ORDER BY created_at DESC LIMIT 50"
        with self._engine.begin() as conn:
            rows = conn.execute(text(sql), params).mappings().all()
            return [self._debits._row_to_record(r) for r in rows]
