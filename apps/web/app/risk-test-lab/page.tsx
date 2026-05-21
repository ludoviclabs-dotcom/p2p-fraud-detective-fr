"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { RISK_SCENARIOS } from "@/data/risk-scenarios";
import { scoreTransaction } from "@/lib/risk/scoreEngine";
import type { EvidencePack, P2PTransaction, RiskScenario, RiskScoreResult } from "@/types/risk";
import { Badge, SeverityBadge } from "@/components/ui/badge";
import { formatEur } from "@/lib/utils";
import { ForensicPage } from "@/components/forensic-page";

const FIRST_SCENARIO = RISK_SCENARIOS[0];

export default function RiskTestLabPage() {
  const [scenarioId, setScenarioId] = useState(FIRST_SCENARIO.id);
  const [jsonInput, setJsonInput] = useState(
    JSON.stringify(FIRST_SCENARIO.transaction, null, 2),
  );
  const [result, setResult] = useState<RiskScoreResult | null>(
    scoreTransaction(FIRST_SCENARIO.transaction),
  );
  const [evidencePack, setEvidencePack] = useState<EvidencePack | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<"score" | "case" | "evidence" | null>(null);

  const scenario = useMemo(
    () => RISK_SCENARIOS.find((item) => item.id === scenarioId) ?? FIRST_SCENARIO,
    [scenarioId],
  );

  function loadScenario(next: RiskScenario) {
    setScenarioId(next.id);
    setJsonInput(JSON.stringify(next.transaction, null, 2));
    setResult(scoreTransaction(next.transaction));
    setEvidencePack(null);
    setError(null);
  }

  function parseTransaction(): P2PTransaction | null {
    try {
      const value = JSON.parse(jsonInput) as P2PTransaction;
      setError(null);
      return value;
    } catch (parseError) {
      setError(parseError instanceof Error ? parseError.message : "JSON invalide");
      return null;
    }
  }

  async function runScore() {
    const transaction = parseTransaction();
    if (!transaction) return;
    setPending("score");
    try {
      const response = await fetch("/api/risk/score", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transaction }),
      });
      if (!response.ok) throw new Error(await response.text());
      setResult((await response.json()) as RiskScoreResult);
      setEvidencePack(null);
      setError(null);
    } catch (apiError) {
      setResult(scoreTransaction(transaction));
      setError(
        `Mode local utilisé: ${
          apiError instanceof Error ? apiError.message : "API indisponible"
        }`,
      );
    } finally {
      setPending(null);
    }
  }

  async function createCase() {
    const transaction = parseTransaction();
    if (!transaction) return;
    setPending("case");
    try {
      const response = await fetch("/api/risk/cases", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ caseId: transaction.caseId ?? scenario.caseId, transaction }),
      });
      if (!response.ok) throw new Error(await response.text());
      const payload = (await response.json()) as { href: string };
      window.location.href = payload.href;
    } catch (caseError) {
      setError(caseError instanceof Error ? caseError.message : "Création case impossible");
    } finally {
      setPending(null);
    }
  }

  async function exportEvidence() {
    const transaction = parseTransaction();
    if (!transaction) return;
    setPending("evidence");
    try {
      const response = await fetch("/api/evidence/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          caseId: transaction.caseId ?? scenario.caseId,
          transaction,
          analystNotes: "Export généré depuis le Risk Test Lab.",
        }),
      });
      if (!response.ok) throw new Error(await response.text());
      const payload = (await response.json()) as { evidencePack: EvidencePack };
      setEvidencePack(payload.evidencePack);
      setError(null);
    } catch (evidenceError) {
      setError(evidenceError instanceof Error ? evidenceError.message : "Export impossible");
    } finally {
      setPending(null);
    }
  }

  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Console de test</div>
          <h1 style={{ marginTop: 9 }}>
            Risk <span className="italic">Test Lab</span>
          </h1>
          <p className="sub">
            Testez le moteur avec un scénario, modifiez le JSON, appelez l&apos;API,
            créez un case et générez un evidence pack. Tout reste synthétique.
          </p>
        </div>
        <div className="fx-head-actions">
          <Link href="/risk-docs" className="fx-btn-ghost">
            Documentation &amp; glossaire
          </Link>
          <Link href="/p2p-scenarios" className="fx-btn">
            Scénarios guidés ↗
          </Link>
        </div>
      </div>

      <section className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="space-y-5">
          <div className="fx-panel">
            <div className="fx-panel-head">
              <h2>Choisir un scénario</h2>
              <span className="glyph">◇</span>
            </div>
            <div className="fx-panel-body space-y-2">
              {RISK_SCENARIOS.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => loadScenario(item)}
                  style={{
                    display: "block",
                    width: "100%",
                    textAlign: "left",
                    background: scenario.id === item.id ? "var(--panel-2)" : "var(--bg-2)",
                    border: `1px solid ${scenario.id === item.id ? "var(--risk)" : "var(--border)"}`,
                    borderLeft: scenario.id === item.id ? "2px solid var(--risk)" : "2px solid transparent",
                    padding: "10px 12px",
                    cursor: "pointer",
                    transition: "all .15s",
                  }}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="fx-mono" style={{ fontSize: 12, color: "var(--fg)", fontWeight: 500 }}>
                        {item.title}
                      </div>
                      <div className="fx-mono" style={{ fontSize: 11, color: "var(--muted)", marginTop: 3 }}>
                        {item.caseId} · {formatEur(item.transaction.amount)} · {item.transaction.rail}
                      </div>
                    </div>
                    <Badge>Demo</Badge>
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="fx-panel">
            <div className="fx-panel-head">
              <h2>Actions de test</h2>
              <span className="glyph">□</span>
            </div>
            <div className="fx-panel-body grid gap-3 sm:grid-cols-2">
              <button type="button" className="fx-btn sm" onClick={runScore} disabled={pending !== null}>
                {pending === "score" ? "⏳ Scoring…" : "▶ Scorer via API"}
              </button>
              <button type="button" className="fx-btn-ghost sm" onClick={createCase} disabled={pending !== null}>
                ▲ Créer Fraud Case 360
              </button>
              <button type="button" className="fx-btn-ghost sm" onClick={exportEvidence} disabled={pending !== null}>
                {pending === "evidence" ? "⏳ Export…" : "↓ Générer evidence pack"}
              </button>
              <button
                type="button"
                className="fx-btn-ghost sm"
                onClick={() => loadScenario(scenario)}
                disabled={pending !== null}
              >
                ↻ Réinitialiser JSON
              </button>
            </div>
          </div>
        </div>

        <div className="space-y-5">
          <div className="fx-panel">
            <div className="fx-panel-head">
              <div>
                <h2>
                  <label htmlFor="risk-lab-transaction-json">Transaction JSON éditable</label>
                </h2>
                <div className="sub">POST /api/risk/score</div>
              </div>
              <Badge severity="neutral">POST</Badge>
            </div>
            <div className="fx-panel-body">
              <textarea
                id="risk-lab-transaction-json"
                value={jsonInput}
                onChange={(event) => setJsonInput(event.target.value)}
                rows={18}
                spellCheck={false}
                aria-describedby={error ? "risk-lab-json-error" : "risk-lab-json-help"}
                style={{
                  width: "100%",
                  background: "var(--bg)",
                  border: "1px solid var(--border)",
                  padding: "14px",
                  fontFamily: "var(--font-mono)",
                  fontSize: 12,
                  lineHeight: 1.6,
                  color: "var(--fg)",
                  outline: "none",
                  resize: "vertical",
                }}
              />
              <p id="risk-lab-json-help" className="fx-mono" style={{ marginTop: 8, fontSize: 11, color: "var(--muted)" }}>
                Utilisez uniquement des données synthétiques. Le JSON est envoyé à /api/risk/score.
              </p>
              {error ? (
                <div
                  id="risk-lab-json-error"
                  role="alert"
                  style={{
                    marginTop: 10,
                    background: "var(--risk-soft)",
                    border: "1px solid var(--risk)",
                    borderLeft: "2px solid var(--risk)",
                    padding: "10px 12px",
                  }}
                >
                  <span className="fx-mono" style={{ fontSize: 12, color: "var(--risk)" }}>{error}</span>
                </div>
              ) : null}
            </div>
          </div>

          {result ? <ScoreResultPanel result={result} /> : null}
          {evidencePack ? <EvidenceResultPanel evidencePack={evidencePack} /> : null}
        </div>
      </section>
    </ForensicPage>
  );
}

function ScoreResultPanel({ result }: { result: RiskScoreResult }) {
  return (
    <div className="fx-panel">
      <div className="fx-panel-head">
        <div>
          <div className="fx-eyebrow">✓ Résultat moteur</div>
          <h2 style={{ marginTop: 3 }}>Score &amp; décision</h2>
        </div>
        <SeverityBadge value={result.level} />
      </div>
      <div className="fx-panel-body space-y-4">
        <div className="grid gap-3 sm:grid-cols-4">
          <FactBox label="Score" value={`${result.score}/100`} />
          <FactBox label="Décision" value={result.decision} />
          <FactBox label="Typologie" value={result.typology} />
          <FactBox label="Version" value={result.modelVersion} />
        </div>
        <div className="grid gap-2">
          {result.reasonCodes.slice(0, 10).map((reasonCode) => (
            <div
              key={`${reasonCode.detector}-${reasonCode.code}`}
              style={{ background: "var(--bg-2)", border: "1px solid var(--border)", padding: "10px 12px" }}
            >
              <div className="flex items-center justify-between gap-3">
                <code className="fx-mono" style={{ fontSize: 11, color: "var(--info)" }}>
                  {reasonCode.code}
                </code>
                <span className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>
                  +{reasonCode.weight}
                </span>
              </div>
              <p style={{ marginTop: 4, fontSize: 13, color: "var(--fg-2)" }}>
                {reasonCode.label}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function EvidenceResultPanel({ evidencePack }: { evidencePack: EvidencePack }) {
  return (
    <div className="fx-panel">
      <div className="fx-panel-head">
        <h2>Evidence pack généré</h2>
        <span className="glyph">§</span>
      </div>
      <div className="fx-panel-body">
        <pre
          className="fx-mono"
          style={{
            maxHeight: 320,
            overflow: "auto",
            background: "var(--bg)",
            border: "1px solid var(--border)",
            padding: "14px",
            fontSize: 11,
            lineHeight: 1.6,
            color: "var(--fg-2)",
          }}
        >
          {JSON.stringify(evidencePack, null, 2)}
        </pre>
      </div>
    </div>
  );
}

function FactBox({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ background: "var(--bg-2)", border: "1px solid var(--border)", padding: "10px 12px" }}>
      <div className="fx-eyebrow">{label}</div>
      <div className="fx-mono" style={{ fontSize: 13, color: "var(--fg)", marginTop: 4, fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
        {value}
      </div>
    </div>
  );
}
