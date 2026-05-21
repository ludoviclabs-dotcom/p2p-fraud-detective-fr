"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { RISK_SCENARIOS } from "@/data/risk-scenarios";
import { scoreTransaction } from "@/lib/risk/scoreEngine";
import type { RiskScenario, RiskScoreResult } from "@/types/risk";
import { Badge, SeverityBadge } from "@/components/ui/badge";
import { formatEur } from "@/lib/utils";
import { ForensicPage } from "@/components/forensic-page";

type ScenarioFeed = {
  source: "huggingface" | "local";
  scenarios: RiskScenario[];
  message: string;
};

export default function P2PScenariosPage() {
  const [feed, setFeed] = useState<ScenarioFeed>({
    source: "local",
    scenarios: RISK_SCENARIOS,
    message: "Scénarios locaux chargés.",
  });
  const [selectedId, setSelectedId] = useState(RISK_SCENARIOS[0]?.id ?? "");
  const [results, setResults] = useState<Record<string, RiskScoreResult>>({});
  const [pendingId, setPendingId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/risk/scenarios")
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((payload: ScenarioFeed) => {
        if (!cancelled && Array.isArray(payload.scenarios) && payload.scenarios.length) {
          setFeed(payload);
          setSelectedId(payload.scenarios[0].id);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setFeed({
            source: "local",
            scenarios: RISK_SCENARIOS,
            message: "Source locale de démo utilisée: API scénarios indisponible.",
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const selected = useMemo(
    () => feed.scenarios.find((item) => item.id === selectedId) ?? feed.scenarios[0],
    [feed.scenarios, selectedId],
  );
  const selectedResult = selected ? results[selected.id] : undefined;
  const sourceLabel =
    feed.source === "huggingface"
      ? "Hugging Face"
      : feed.message.toLowerCase().includes("hf_synthetic")
        ? "Fallback local non configuré"
        : "Fallback local";

  async function analyze(scenario: RiskScenario) {
    setPendingId(scenario.id);
    try {
      const response = await fetch("/api/risk/score", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transaction: scenario.transaction }),
      });
      if (!response.ok) throw new Error(await response.text());
      const result = (await response.json()) as RiskScoreResult;
      setResults((previous) => ({ ...previous, [scenario.id]: result }));
      setSelectedId(scenario.id);
    } catch {
      setResults((previous) => ({
        ...previous,
        [scenario.id]: scoreTransaction(scenario.transaction),
      }));
      setSelectedId(scenario.id);
    } finally {
      setPendingId(null);
    }
  }

  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Paiements P2P · SEPA · Procure-to-Pay</div>
          <h1 style={{ marginTop: 9 }}>
            Scénarios P2P <span className="italic">explicables</span>
          </h1>
          <p className="sub">
            Six parcours synthétiques pour démontrer le cycle détecter, scorer,
            expliquer, investiguer, documenter et exporter.
          </p>
        </div>
        <div className="fx-head-actions">
          <Link href="/risk-test-lab" className="fx-btn">
            Test Lab ↗
          </Link>
          <Link href="/risk-docs" className="fx-btn-ghost">
            Docs &amp; glossaire
          </Link>
          <Link href="/detection-studio" className="fx-btn-ghost">
            Detection Studio
          </Link>
        </div>
      </div>

      <div className="fx-notice" style={{ marginBottom: 20 }}>
        <span className="glyph">▣</span>
        <div className="min-w-0 flex-1">
          <div className="nt">{feed.message}</div>
          <p className="nb">Données synthétiques, décision finale humaine.</p>
        </div>
        <div style={{ flexShrink: 0 }}>
          <Badge severity={feed.source === "huggingface" ? "low" : "neutral"}>
            {sourceLabel}
          </Badge>
        </div>
      </div>

      <section className="grid gap-4 md:grid-cols-3" style={{ marginBottom: 20 }}>
        <PathCard
          title="1. Scénarios guidés"
          body="Sélectionner une fraude synthétique, lancer l'analyse et voir score, reason codes et action recommandée."
          glyph="◇"
          href="/p2p-scenarios"
        />
        <PathCard
          title="2. Test Lab API"
          body="Modifier le JSON, appeler /api/risk/score, créer un case et générer un evidence pack."
          glyph="□"
          href="/risk-test-lab"
        />
        <PathCard
          title="3. Documentation"
          body="Lire le glossaire, les endpoints, les typologies, les limites et le fonctionnement du moteur."
          glyph="§"
          href="/risk-docs"
        />
      </section>

      <div
        style={{
          background: "var(--panel)",
          border: "1px solid var(--border)",
          padding: "14px 16px",
          marginBottom: 20,
        }}
      >
        <div className="grid gap-3 md:grid-cols-4">
          {[
            ["Tester", "Lancer l'analyse sur un scénario.", "/p2p-scenarios"],
            ["Modifier", "Ouvrir le JSON éditable.", "/risk-test-lab"],
            ["Documenter", "Lire glossaire et limites.", "/risk-docs"],
            ["Exporter", "Générer l'evidence pack.", "/risk-test-lab"],
          ].map(([title, body, href]) => (
            <Link
              key={`${title}-${href}`}
              href={href}
              style={{ display: "block", background: "var(--bg-2)", border: "1px solid var(--border)", padding: "10px 12px", textDecoration: "none" }}
            >
              <div className="fx-mono" style={{ fontSize: 12, color: "var(--fg)", fontWeight: 500 }}>
                {title}
              </div>
              <div className="fx-mono" style={{ fontSize: 11, color: "var(--muted)", marginTop: 4, lineHeight: 1.5 }}>
                {body}
              </div>
            </Link>
          ))}
        </div>
      </div>

      <section className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="space-y-3">
          {feed.scenarios.map((scenario) => {
            const result = results[scenario.id];
            const active = selected?.id === scenario.id;
            return (
              <button
                key={scenario.id}
                type="button"
                onClick={() => setSelectedId(scenario.id)}
                style={{
                  display: "block",
                  width: "100%",
                  textAlign: "left",
                  background: active ? "var(--panel-2)" : "var(--panel)",
                  border: `1px solid ${active ? "var(--risk)" : "var(--border)"}`,
                  borderLeft: active ? "2px solid var(--risk)" : "2px solid transparent",
                  padding: "14px 16px",
                  cursor: "pointer",
                  transition: "all .15s",
                }}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="fx-mono" style={{ fontSize: 13, color: "var(--fg)", fontWeight: 500 }}>
                      {scenario.title}
                    </div>
                    <p className="fx-mono" style={{ fontSize: 11, color: "var(--muted)", marginTop: 4, lineHeight: 1.5 }}>
                      {scenario.description}
                    </p>
                  </div>
                  {result ? <SeverityBadge value={result.level} /> : <Badge>Demo</Badge>}
                </div>
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <span className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>{scenario.caseId}</span>
                  <span className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>{formatEur(scenario.transaction.amount)}</span>
                  <span className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>{scenario.transaction.rail}</span>
                </div>
              </button>
            );
          })}
        </div>

        {selected ? (
          <div className="fx-panel">
            <div className="fx-panel-head">
              <div>
                <div className="fx-eyebrow">Analyse scénario</div>
                <h2 style={{ marginTop: 4 }}>{selected.title}</h2>
              </div>
              {selectedResult ? <SeverityBadge value={selectedResult.level} /> : null}
            </div>
            <div className="fx-panel-body space-y-4">
              <p style={{ fontSize: 13, lineHeight: 1.7, color: "var(--fg-2)" }}>{selected.businessContext}</p>

              <div className="grid gap-3 sm:grid-cols-3">
                <FactBox label="Montant" value={formatEur(selected.transaction.amount)} />
                <FactBox label="Rail" value={selected.transaction.rail} />
                <FactBox label="Case" value={selected.caseId} />
              </div>

              <details style={{ background: "var(--bg-2)", border: "1px solid var(--border)", padding: 14 }}>
                <summary
                  style={{ cursor: "pointer" }}
                  className="fx-eyebrow"
                >
                  § Voir les données synthétiques JSON
                </summary>
                <pre
                  className="fx-mono"
                  style={{
                    marginTop: 12,
                    maxHeight: 224,
                    overflow: "auto",
                    fontSize: 11,
                    lineHeight: 1.6,
                    color: "var(--fg-2)",
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {JSON.stringify(selected.transaction, null, 2)}
                </pre>
              </details>

              <button
                type="button"
                className="fx-btn sm"
                onClick={() => analyze(selected)}
                disabled={pendingId === selected.id}
              >
                {pendingId === selected.id ? "⏳ Analyse en cours…" : "▶ Lancer l'analyse"}
              </button>

              {selectedResult ? (
                <div className="space-y-4" aria-live="polite" data-testid="p2p-scenario-result">
                  <div className="grid gap-3 sm:grid-cols-4">
                    <FactBox label="Score" value={`${selectedResult.score}/100`} />
                    <FactBox label="Niveau" value={selectedResult.level} />
                    <FactBox label="Décision" value={selectedResult.decision} />
                    <FactBox label="Typologie" value={selectedResult.typology} />
                  </div>

                  <div>
                    <div className="fx-eyebrow" style={{ marginBottom: 8 }}>⚠ Reason codes</div>
                    <div className="grid gap-2">
                      {selectedResult.reasonCodes.map((reasonCode) => (
                        <div
                          key={`${reasonCode.detector}-${reasonCode.code}`}
                          style={{ background: "var(--panel-2)", border: "1px solid var(--border)", padding: "10px 12px" }}
                        >
                          <div className="flex items-center justify-between gap-2">
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

                  <div>
                    <div className="fx-eyebrow" style={{ marginBottom: 8 }}>Scores par détecteur</div>
                    <div className="grid gap-2 sm:grid-cols-2">
                      {selectedResult.detectorScores.map((detector) => (
                        <div
                          key={detector.detector}
                          style={{ background: "var(--bg-2)", border: "1px solid var(--border)", padding: "10px 12px" }}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="fx-mono" style={{ fontSize: 12, color: "var(--fg)" }}>
                              {detector.label}
                            </span>
                            <span className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>
                              {detector.score}/{detector.maxScore}
                            </span>
                          </div>
                          <p className="fx-mono" style={{ marginTop: 4, fontSize: 11, color: "var(--muted)", lineHeight: 1.5 }}>
                            {detector.explanation}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="fx-card-accent">
                    <div className="fx-eyebrow" style={{ marginBottom: 6 }}>Action recommandée</div>
                    <p style={{ fontSize: 13, lineHeight: 1.6, color: "var(--fg-2)", marginTop: 4 }}>
                      {selectedResult.recommendedActions[0]}
                    </p>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Link
                      href={`/fraud-case-360/${encodeURIComponent(selected.caseId)}`}
                      className="fx-btn sm"
                    >
                      Ouvrir Fraud Case 360 ↗
                    </Link>
                    <Link href="/risk-test-lab" className="fx-btn-ghost sm">
                      Modifier / exporter dans le Test Lab
                    </Link>
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        ) : null}
      </section>
    </ForensicPage>
  );
}

function PathCard({
  title,
  body,
  glyph,
  href,
}: {
  title: string;
  body: string;
  glyph: string;
  href: string;
}) {
  return (
    <Link href={href} className="fx-card" style={{ display: "block", textDecoration: "none" }}>
      <span className="fx-mono" style={{ fontSize: 16, color: "var(--risk)" }}>{glyph}</span>
      <div className="fx-mono" style={{ fontSize: 13, color: "var(--fg)", marginTop: 10, fontWeight: 500 }}>{title}</div>
      <p style={{ fontSize: 13, lineHeight: 1.6, color: "var(--muted)", marginTop: 6 }}>{body}</p>
    </Link>
  );
}

function FactBox({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ background: "var(--bg-2)", border: "1px solid var(--border)", padding: "10px 12px" }}>
      <div className="fx-eyebrow">{label}</div>
      <div className="fx-mono" style={{ fontSize: 13, color: "var(--fg)", marginTop: 4, fontWeight: 500, wordBreak: "break-all" }}>
        {value}
      </div>
    </div>
  );
}
