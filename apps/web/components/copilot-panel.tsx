"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { askCopilot, listCopilotQuestions } from "@/lib/api-client";
import type { CopilotResult } from "@/lib/api-client";
import { ClaimList } from "@/components/grounded-claims";

/**
 * Copilote analyste (Phase 5, ADR-0007) — questions prédéfinies sur un cas.
 *
 * Pas de chat libre : le catalogue de questions vient du backend, le modèle
 * ne voit que le source pack du cas, et le bandeau « validation humaine
 * requise » est permanent.
 */
export function CopilotPanel({ caseId }: { caseId: string | null }) {
  const [questionId, setQuestionId] = useState("");

  const questionsQuery = useQuery({
    queryKey: ["copilot-questions"],
    queryFn: listCopilotQuestions,
    retry: false,
  });

  const askMutation = useMutation({
    mutationFn: () =>
      askCopilot({ question_id: questionId, case_id: caseId ?? "" }),
  });

  const questions = questionsQuery.data ?? [];

  return (
    <div className="fx-panel" style={{ marginTop: 16 }} data-testid="copilot-panel">
      <div className="fx-panel-head">
        <div>
          <h2>Copilote analyste</h2>
          <div className="sub">
            Questions prédéfinies · réponses sourcées sur le cas · aucune
            décision automatique
          </div>
        </div>
        <span className="glyph">¿</span>
      </div>
      <div className="fx-panel-body space-y-4">
        <div className="fx-notice">
          <span className="glyph">★</span>
          <div>
            <div className="nt">Validation humaine requise</div>
            <p className="nb">
              Le copilote assiste l&apos;instruction — il ne bloque aucun
              paiement et ne clôt aucun cas.
            </p>
          </div>
        </div>

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <select
            aria-label="Question prédéfinie du copilote"
            data-testid="copilot-question-select"
            value={questionId}
            onChange={(e) => setQuestionId(e.target.value)}
            style={{
              height: 38,
              minWidth: 320,
              background: "var(--bg)",
              border: "1px solid var(--border)",
              padding: "0 12px",
              fontFamily: "var(--font-mono)",
              fontSize: 12,
              color: "var(--fg)",
              outline: "none",
            }}
          >
            <option value="">— Choisir une question —</option>
            {questions.map((q) => (
              <option key={q.question_id} value={q.question_id}>
                {q.label_fr}
              </option>
            ))}
          </select>
          <button
            className="fx-btn"
            data-testid="copilot-ask-button"
            type="button"
            disabled={!caseId || !questionId || askMutation.isPending}
            onClick={() => askMutation.mutate()}
          >
            {askMutation.isPending ? "◷ Analyse…" : "¿ Poser la question"}
          </button>
          <span className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>
            {caseId ? `Cas : ${caseId}` : "Sélectionnez exactement un cas."}
          </span>
        </div>

        {askMutation.error || questionsQuery.error ? (
          <div className="fx-notice">
            <span className="glyph">⚠</span>
            <div>
              <div className="nt">Copilote indisponible</div>
              <p className="nb">
                Le backend FastAPI (et sa clé ANTHROPIC_API_KEY) doit être
                configuré pour activer le copilote.
              </p>
            </div>
          </div>
        ) : null}

        {askMutation.data ? <AnswerView result={askMutation.data} /> : null}
      </div>
    </div>
  );
}

function AnswerView({ result }: { result: CopilotResult }) {
  const answer = result.answer;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <div
        style={{
          background: "var(--bg-2)",
          border: "1px solid var(--border)",
          borderLeft: "3px solid var(--info)",
          padding: "12px 14px",
        }}
      >
        <p style={{ margin: 0, fontSize: 14, lineHeight: 1.65, color: "var(--fg)" }}>
          {answer.answer_short}
        </p>
      </div>

      <div>
        <div className="fx-eyebrow" style={{ marginBottom: 8 }}>Preuves</div>
        <ClaimList claims={answer.evidence} />
      </div>

      {answer.uncertainties.length ? (
        <div>
          <div className="fx-eyebrow" style={{ marginBottom: 8, color: "var(--warn)" }}>
            Incertitudes
          </div>
          <ul style={{ margin: 0, paddingLeft: 18 }} className="space-y-1">
            {answer.uncertainties.map((item) => (
              <li key={item} style={{ fontSize: 13, lineHeight: 1.6, color: "var(--muted)" }}>
                {item}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div>
        <div className="fx-eyebrow" style={{ marginBottom: 6 }}>Prochaine action proposée</div>
        <p className="fx-mono" style={{ margin: 0, fontSize: 12, lineHeight: 1.6, color: "var(--fg-2)" }}>
          → {answer.recommended_next_action}
        </p>
      </div>

      <div className="fx-mono" style={{ fontSize: 10, color: "var(--dim)" }}>
        Généré par {result.model} · prompt {result.prompt_version} · journalisé au
        ledger ai.generation
      </div>
    </div>
  );
}
