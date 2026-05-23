"use client";

import Link from "next/link";
import { useState } from "react";
import { SeverityBadge } from "@/components/ui/badge";
import { ForensicPage } from "@/components/forensic-page";

type Signal = {
  code: string;
  title: string;
  message: string;
  severity: string;
  score: number;
  evidence: Record<string, unknown>;
};

type MatchOut = {
  matched: boolean;
  mandate_id: string | null;
  candidates_active: number;
  candidates_inactive: number;
  warnings: string[];
};

type AnalysisOut = {
  event_id: string;
  domain: string;
  score: number;
  level: string;
  decision: string;
  engine_version: string;
  signals: Signal[];
  match: MatchOut;
};

type FormState = {
  idempotency_key: string;
  creditor_ics: string;
  creditor_name_raw: string;
  rum: string;
  amount_cents: number;
  currency: string;
  debtor_iban: string;
};

const DEFAULT_FORM: FormState = {
  idempotency_key: "lab-001",
  creditor_ics: "FR18ZZZ002305",
  creditor_name_raw: "EDF SA",
  rum: "RUM-EDF-001",
  amount_cents: 8900,
  currency: "EUR",
  debtor_iban: "FR7630001007941234567890185",
};

type Preset = {
  id: string;
  label: string;
  caseId: string;
  hint: string;
  form: FormState;
};

const PRESETS: Preset[] = [
  {
    id: "no_mandate",
    label: "Aucun mandat — prélèvement non autorisé",
    caseId: "SEPA-NO-MANDATE",
    hint: "ICS inconnu, RUM forgée, aucun mandat actif",
    form: {
      ...DEFAULT_FORM,
      idempotency_key: "lab-no-mandate-001",
      creditor_ics: "FR99ZZZ999999",
      creditor_name_raw: "FOURNISSEUR INCONNU",
      rum: "RUM-UNKNOWN-001",
    },
  },
  {
    id: "amount_exceeds",
    label: "Mandat existant — dépassement de plafond",
    caseId: "SEPA-AMOUNT-OVER",
    hint: "Plafond 120€, débit 500€",
    form: {
      ...DEFAULT_FORM,
      idempotency_key: "lab-amount-001",
      amount_cents: 50000,
    },
  },
  {
    id: "unknown_rum",
    label: "Mandat actif présent mais RUM divergente",
    caseId: "SEPA-RUM-MISMATCH",
    hint: "IBAN+ICS connus, RUM différente du mandat",
    form: {
      ...DEFAULT_FORM,
      idempotency_key: "lab-rum-mismatch-001",
      rum: "RUM-DIFFERENT-001",
    },
  },
];

function formatEur(cents: number): string {
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR",
  }).format(cents / 100);
}

export default function RiskLabSepaPage() {
  const [activePreset, setActivePreset] = useState<string>("no_mandate");
  const [form, setForm] = useState<FormState>(PRESETS[0].form);
  const [result, setResult] = useState<AnalysisOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const applyPreset = (preset: Preset) => {
    setActivePreset(preset.id);
    setForm(preset.form);
    setResult(null);
    setError(null);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPending(true);
    setError(null);
    setResult(null);
    try {
      const response = await fetch("/api/v1/risk/assess", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          risk_domain: "SEPA_DIRECT_DEBIT",
          event: {
            source: "lab",
            idempotency_key: form.idempotency_key,
            creditor_ics: form.creditor_ics,
            creditor_name_raw: form.creditor_name_raw,
            rum: form.rum || null,
            amount_cents: Number(form.amount_cents),
            currency: form.currency,
            debtor_iban: form.debtor_iban,
          },
        }),
      });
      if (!response.ok) {
        const body = await response.text();
        throw new Error(`HTTP ${response.status} — ${body}`);
      }
      const data = (await response.json()) as AnalysisOut;
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setPending(false);
    }
  };

  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Console SEPA</div>
          <h1 style={{ marginTop: 9 }}>
            Risk Lab <span className="italic">SEPA Mandate</span>
          </h1>
          <p className="sub">
            Testez le moteur SEPA Mandate Guard avec un scénario synthétique.
            L&apos;événement est envoyé à <code>POST /api/v1/risk/assess</code>{" "}
            avec <code>risk_domain=SEPA_DIRECT_DEBIT</code>. Le moteur retourne
            un score 0-100, un niveau, une décision recommandée et la liste
            des reason codes déclenchés.
          </p>
        </div>
        <div className="fx-head-actions">
          <Link href="/risk-test-lab" className="fx-btn-ghost">
            Risk Lab P2P ↗
          </Link>
          <Link href="/methodology" className="fx-btn-ghost">
            Méthodologie &amp; reason codes
          </Link>
        </div>
      </div>

      <section className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="space-y-5">
          {/* Sélection de scénario */}
          <div className="fx-panel">
            <div className="fx-panel-head">
              <h2>Choisir un scénario</h2>
              <span className="glyph">◇</span>
            </div>
            <div className="fx-panel-body space-y-2">
              {PRESETS.map((preset) => {
                const isActive = preset.id === activePreset;
                return (
                  <button
                    key={preset.id}
                    type="button"
                    onClick={() => applyPreset(preset)}
                    style={{
                      display: "block",
                      width: "100%",
                      textAlign: "left",
                      background: isActive ? "var(--panel-2)" : "var(--bg-2)",
                      border: `1px solid ${isActive ? "var(--risk)" : "var(--border)"}`,
                      borderLeft: isActive
                        ? "2px solid var(--risk)"
                        : "2px solid transparent",
                      padding: "10px 12px",
                      cursor: "pointer",
                      transition: "all .15s",
                    }}
                  >
                    <div
                      className="fx-mono"
                      style={{
                        fontSize: 12,
                        color: "var(--fg)",
                        fontWeight: 500,
                      }}
                    >
                      {preset.label}
                    </div>
                    <div
                      className="fx-mono"
                      style={{
                        fontSize: 11,
                        color: "var(--muted)",
                        marginTop: 3,
                      }}
                    >
                      {preset.caseId} · {preset.hint}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Formulaire */}
          <div className="fx-panel">
            <div className="fx-panel-head">
              <div>
                <h2>Paramètres de l&apos;événement</h2>
                <div className="sub">POST /api/v1/risk/assess</div>
              </div>
              <span className="glyph">□</span>
            </div>
            <form onSubmit={submit} className="fx-panel-body space-y-3">
              <Field
                label="Idempotency key"
                value={form.idempotency_key}
                onChange={(v) =>
                  setForm((f) => ({ ...f, idempotency_key: v }))
                }
                required
              />
              <Field
                label="Créancier — ICS"
                value={form.creditor_ics}
                onChange={(v) => setForm((f) => ({ ...f, creditor_ics: v }))}
                required
              />
              <Field
                label="Créancier — nom brut"
                value={form.creditor_name_raw}
                onChange={(v) =>
                  setForm((f) => ({ ...f, creditor_name_raw: v }))
                }
              />
              <Field
                label="RUM (Référence Unique de Mandat)"
                value={form.rum}
                onChange={(v) => setForm((f) => ({ ...f, rum: v }))}
              />
              <div className="grid grid-cols-2 gap-3">
                <Field
                  label="Montant (cents)"
                  type="number"
                  value={String(form.amount_cents)}
                  onChange={(v) =>
                    setForm((f) => ({ ...f, amount_cents: Number(v) }))
                  }
                  required
                  hint={formatEur(form.amount_cents)}
                />
                <Field
                  label="Devise"
                  value={form.currency}
                  onChange={(v) => setForm((f) => ({ ...f, currency: v }))}
                  required
                />
              </div>
              <Field
                label="IBAN débiteur (sera fingerprinté)"
                value={form.debtor_iban}
                onChange={(v) => setForm((f) => ({ ...f, debtor_iban: v }))}
                required
              />
              <div style={{ display: "flex", gap: 10, paddingTop: 6 }}>
                <button
                  type="submit"
                  className="fx-btn sm"
                  disabled={pending}
                >
                  {pending ? "⏳ Analyse en cours…" : "▶ Analyser ce prélèvement"}
                </button>
                <button
                  type="button"
                  className="fx-btn-ghost sm"
                  onClick={() => applyPreset(PRESETS.find((p) => p.id === activePreset) ?? PRESETS[0])}
                  disabled={pending}
                >
                  ↻ Réinitialiser
                </button>
              </div>
              {error ? (
                <div className="fx-notice" style={{ borderLeftColor: "var(--risk)" }}>
                  <span className="glyph" style={{ color: "var(--risk)" }}>
                    !
                  </span>
                  <div>
                    <div className="nt" style={{ color: "var(--risk)" }}>
                      Erreur
                    </div>
                    <div className="nb">{error}</div>
                  </div>
                </div>
              ) : null}
            </form>
          </div>
        </div>

        {/* Résultat */}
        <div className="space-y-5">
          {result ? (
            <>
              <VerdictPanel result={result} />
              <SignalsPanel signals={result.signals} />
              <JsonPanel result={result} />
            </>
          ) : (
            <div className="fx-panel">
              <div className="fx-panel-head">
                <h2>Verdict du moteur</h2>
                <span className="glyph">○</span>
              </div>
              <div className="fx-panel-body">
                <p
                  className="fx-mono"
                  style={{ fontSize: 12, color: "var(--muted)" }}
                >
                  Sélectionnez un scénario et lancez l&apos;analyse pour voir
                  apparaître le score, le niveau, la décision et les reason
                  codes ici.
                </p>
              </div>
            </div>
          )}
        </div>
      </section>
    </ForensicPage>
  );
}

// ─── Sub-components ─────────────────────────────────────────────────────────

function Field({
  label,
  value,
  onChange,
  type = "text",
  required = false,
  hint,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  required?: boolean;
  hint?: string;
}) {
  return (
    <label style={{ display: "block" }}>
      <span
        className="fx-mono"
        style={{
          display: "block",
          fontSize: 10,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          color: "var(--muted)",
          marginBottom: 4,
        }}
      >
        {label}
      </span>
      <input
        type={type}
        value={value}
        required={required}
        onChange={(e) => onChange(e.target.value)}
        style={{
          width: "100%",
          background: "var(--bg)",
          border: "1px solid var(--border)",
          padding: "9px 12px",
          fontFamily: "var(--font-mono)",
          fontSize: 12,
          color: "var(--fg)",
          outline: "none",
        }}
      />
      {hint ? (
        <span
          className="fx-mono"
          style={{
            display: "block",
            fontSize: 10,
            color: "var(--muted)",
            marginTop: 3,
          }}
        >
          ≈ {hint}
        </span>
      ) : null}
    </label>
  );
}

function VerdictPanel({ result }: { result: AnalysisOut }) {
  return (
    <div className="fx-panel">
      <div className="fx-panel-head">
        <div>
          <div className="fx-eyebrow">✓ Résultat moteur</div>
          <h2 style={{ marginTop: 3 }}>Verdict</h2>
        </div>
        <SeverityBadge value={result.level} />
      </div>
      <div className="fx-panel-body space-y-4">
        <div className="grid gap-3 sm:grid-cols-4">
          <Stat
            label="Score"
            value={`${result.score}/100`}
            tone={toneForLevel(result.level)}
          />
          <Stat
            label="Décision"
            value={result.decision.replace(/_/g, " ")}
            tone={toneForLevel(result.level)}
          />
          <Stat
            label="Niveau"
            value={result.level}
            tone={toneForLevel(result.level)}
          />
          <Stat label="Moteur" value={result.engine_version} tone="info" />
        </div>
        <ProgressBar score={result.score} />
        <div
          style={{
            background: "var(--bg-2)",
            border: "1px solid var(--border)",
            padding: "10px 12px",
          }}
        >
          <div
            className="fx-mono"
            style={{ fontSize: 11, color: "var(--muted)" }}
          >
            event_id ·{" "}
            <span style={{ color: "var(--fg)" }}>{result.event_id}</span>
          </div>
          <div
            className="fx-mono"
            style={{ fontSize: 11, color: "var(--muted)", marginTop: 4 }}
          >
            match ·{" "}
            {result.match.matched ? (
              <span style={{ color: "var(--verified)" }}>
                mandat actif {result.match.mandate_id}
              </span>
            ) : (
              <span style={{ color: "var(--risk)" }}>aucun mandat actif</span>
            )}{" "}
            · candidats inactifs {result.match.candidates_inactive}
          </div>
          {result.match.warnings.length > 0 ? (
            <div
              className="fx-mono"
              style={{ fontSize: 11, color: "var(--warn)", marginTop: 4 }}
            >
              warnings · {result.match.warnings.join(", ")}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function SignalsPanel({ signals }: { signals: Signal[] }) {
  return (
    <div className="fx-panel">
      <div className="fx-panel-head">
        <h2>Reason codes ({signals.length})</h2>
        <span className="glyph">▲</span>
      </div>
      <div className="fx-panel-body space-y-2">
        {signals.length === 0 ? (
          <p
            className="fx-mono"
            style={{ fontSize: 11, color: "var(--muted)" }}
          >
            Aucun signal déclenché — décision ALLOW.
          </p>
        ) : (
          signals.map((s) => (
            <div
              key={s.code}
              style={{
                background: "var(--bg-2)",
                border: "1px solid var(--border)",
                borderLeft: `2px solid ${severityColor(s.severity)}`,
                padding: "12px 14px",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: 8,
                  marginBottom: 6,
                }}
              >
                <code
                  className="fx-mono"
                  style={{ fontSize: 11, color: "var(--info)" }}
                >
                  {s.code}
                </code>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <SeverityBadge value={s.severity} />
                  <span
                    className="fx-mono"
                    style={{ fontSize: 11, color: "var(--muted)" }}
                  >
                    +{s.score} pts
                  </span>
                </div>
              </div>
              <div
                style={{ fontSize: 13, color: "var(--fg)", fontWeight: 500 }}
              >
                {s.title}
              </div>
              <div
                style={{
                  fontSize: 12,
                  color: "var(--muted)",
                  marginTop: 4,
                  lineHeight: 1.5,
                }}
              >
                {s.message}
              </div>
              <details style={{ marginTop: 8 }}>
                <summary
                  className="fx-mono"
                  style={{
                    fontSize: 10,
                    color: "var(--muted)",
                    cursor: "pointer",
                    letterSpacing: "0.08em",
                    textTransform: "uppercase",
                  }}
                >
                  evidence
                </summary>
                <pre
                  className="fx-mono"
                  style={{
                    fontSize: 11,
                    background: "var(--bg)",
                    border: "1px solid var(--border)",
                    padding: "8px 10px",
                    marginTop: 6,
                    color: "var(--fg)",
                    overflow: "auto",
                  }}
                >
                  {JSON.stringify(s.evidence, null, 2)}
                </pre>
              </details>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function JsonPanel({ result }: { result: AnalysisOut }) {
  return (
    <div className="fx-panel">
      <div className="fx-panel-head">
        <h2>JSON brut</h2>
        <span className="glyph">⌘</span>
      </div>
      <div className="fx-panel-body">
        <pre
          className="fx-mono"
          style={{
            fontSize: 11,
            background: "var(--bg)",
            border: "1px solid var(--border)",
            padding: "12px 14px",
            color: "var(--fg)",
            overflow: "auto",
            lineHeight: 1.6,
          }}
        >
          {JSON.stringify(result, null, 2)}
        </pre>
      </div>
    </div>
  );
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: "risk" | "warn" | "ok" | "info";
}) {
  return (
    <div className={`fx-stat ${tone}`}>
      <div className="fx-stat-top">
        <div className="lbl">{label}</div>
      </div>
      <div className="val">{value}</div>
    </div>
  );
}

function ProgressBar({ score }: { score: number }) {
  const pct = Math.max(0, Math.min(100, score));
  return (
    <div>
      <div
        className="fx-mono"
        style={{
          fontSize: 10,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          color: "var(--muted)",
          marginBottom: 4,
        }}
      >
        Score consolidé
      </div>
      <div className="fx-bar">
        <i style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function toneForLevel(level: string): "risk" | "warn" | "ok" | "info" {
  const l = level.toUpperCase();
  if (l === "CRITICAL") return "risk";
  if (l === "HIGH") return "warn";
  if (l === "LOW") return "ok";
  return "info";
}

function severityColor(severity: string): string {
  const s = severity.toLowerCase();
  if (s === "critical") return "var(--risk)";
  if (s === "high") return "var(--warn)";
  if (s === "medium") return "var(--warn)";
  if (s === "low") return "var(--verified)";
  return "var(--border-strong)";
}
