"use client";

import { useState } from "react";
import Link from "next/link";
import { Badge, SeverityBadge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";

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

const PRESETS: Record<string, Partial<FormState>> = {
  no_mandate: {
    label: "Aucun mandat — prélèvement non autorisé",
    idempotency_key: "lab-no-mandate-001",
    creditor_ics: "FR99ZZZ999999",
    creditor_name_raw: "FOURNISSEUR INCONNU",
    rum: "RUM-UNKNOWN-001",
    amount_cents: 8900,
    debtor_iban: "FR7630001007941234567890185",
  },
  amount_exceeds: {
    label: "Mandat existant — dépassement de plafond",
    idempotency_key: "lab-amount-001",
    creditor_ics: "FR18ZZZ002305",
    creditor_name_raw: "EDF SA",
    rum: "RUM-EDF-001",
    amount_cents: 50000,
    debtor_iban: "FR7630001007941234567890185",
  },
  unknown_rum: {
    label: "Mandat actif présent mais RUM divergente",
    idempotency_key: "lab-rum-mismatch-001",
    creditor_ics: "FR18ZZZ002305",
    creditor_name_raw: "EDF SA",
    rum: "RUM-DIFFERENT-001",
    amount_cents: 8900,
    debtor_iban: "FR7630001007941234567890185",
  },
};

type FormState = {
  label?: string;
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

function levelClass(level: string): string {
  return `fx-tag ${level.toLowerCase()}`;
}

function decisionLabel(decision: string): string {
  return decision.replace(/_/g, " ");
}

export default function RiskLabSepaPage() {
  const [form, setForm] = useState<FormState>(DEFAULT_FORM);
  const [result, setResult] = useState<AnalysisOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

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

  const applyPreset = (key: keyof typeof PRESETS) => {
    const p = PRESETS[key];
    setForm({ ...DEFAULT_FORM, ...p });
    setResult(null);
    setError(null);
  };

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <header className="space-y-2">
        <p className="text-sm text-slate-500">
          <Link href="/" className="hover:underline">
            Accueil
          </Link>{" "}
          / Risk Lab SEPA
        </p>
        <h1 className="text-2xl font-semibold">Risk Lab — SEPA Mandate Guard</h1>
        <p className="text-sm text-slate-600">
          Teste un scénario de prélèvement SEPA synthétique. L'événement est
          envoyé à <code>POST /api/v1/risk/assess</code> avec{" "}
          <code>risk_domain=SEPA_DIRECT_DEBIT</code>. Le moteur retourne un
          score 0-100, un niveau, une décision recommandée et la liste des
          signaux déclenchés.
        </p>
      </header>

      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase text-slate-500">
          Scénarios pré-remplis
        </h2>
        <div className="flex flex-wrap gap-2">
          {Object.entries(PRESETS).map(([key, p]) => (
            <button
              key={key}
              type="button"
              onClick={() => applyPreset(key as keyof typeof PRESETS)}
              className="rounded border border-slate-300 bg-white px-3 py-1.5 text-xs hover:bg-slate-50"
            >
              {p.label}
            </button>
          ))}
        </div>
      </section>

      <form
        onSubmit={submit}
        className="grid grid-cols-1 gap-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm md:grid-cols-2"
      >
        <Field label="Idempotency key">
          <input
            value={form.idempotency_key}
            onChange={(e) =>
              setForm((f) => ({ ...f, idempotency_key: e.target.value }))
            }
            required
          />
        </Field>
        <Field label="Créancier — ICS">
          <input
            value={form.creditor_ics}
            onChange={(e) =>
              setForm((f) => ({ ...f, creditor_ics: e.target.value }))
            }
            required
          />
        </Field>
        <Field label="Créancier — nom brut">
          <input
            value={form.creditor_name_raw}
            onChange={(e) =>
              setForm((f) => ({ ...f, creditor_name_raw: e.target.value }))
            }
          />
        </Field>
        <Field label="RUM">
          <input
            value={form.rum}
            onChange={(e) => setForm((f) => ({ ...f, rum: e.target.value }))}
          />
        </Field>
        <Field label="Montant (cents)">
          <input
            type="number"
            min={1}
            value={form.amount_cents}
            onChange={(e) =>
              setForm((f) => ({ ...f, amount_cents: Number(e.target.value) }))
            }
            required
          />
        </Field>
        <Field label="Devise">
          <input
            value={form.currency}
            onChange={(e) =>
              setForm((f) => ({ ...f, currency: e.target.value }))
            }
            required
          />
        </Field>
        <Field label="IBAN débiteur (sera fingerprinté)">
          <input
            value={form.debtor_iban}
            onChange={(e) =>
              setForm((f) => ({ ...f, debtor_iban: e.target.value }))
            }
            required
          />
        </Field>
        <div className="md:col-span-2 flex justify-end">
          <button
            type="submit"
            disabled={pending}
            className="rounded bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
          >
            {pending ? "Analyse en cours…" : "Analyser ce prélèvement"}
          </button>
        </div>
      </form>

      {error && (
        <div className="rounded border border-red-300 bg-red-50 p-3 text-sm text-red-800">
          <strong>Erreur :</strong> {error}
        </div>
      )}

      {result && (
        <section className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Verdict</CardTitle>
            </CardHeader>
            <div className="space-y-2 p-4">
              <div className="flex flex-wrap items-center gap-3">
                <span className={levelClass(result.level)}>{result.level}</span>
                <strong className="text-lg">
                  Décision : {decisionLabel(result.decision)}
                </strong>
                <span className="text-sm text-slate-500">
                  Score {result.score}/100 · moteur {result.engine_version}
                </span>
              </div>
              <p className="text-sm text-slate-600">
                Event ID : <code>{result.event_id}</code>
              </p>
              <p className="text-sm text-slate-600">
                Match :{" "}
                {result.match.matched ? (
                  <Badge severity="low">mandat actif trouvé</Badge>
                ) : (
                  <Badge severity="critical">aucun mandat actif</Badge>
                )}{" "}
                · candidats inactifs : {result.match.candidates_inactive}{" "}
                {result.match.warnings.length > 0 && (
                  <span className="text-xs text-amber-600">
                    {" · "}warnings : {result.match.warnings.join(", ")}
                  </span>
                )}
              </p>
            </div>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Signaux ({result.signals.length})</CardTitle>
            </CardHeader>
            <div className="divide-y divide-slate-100">
              {result.signals.length === 0 && (
                <div className="p-4 text-sm text-slate-500">
                  Aucun signal — décision ALLOW.
                </div>
              )}
              {result.signals.map((s) => (
                <div key={s.code} className="space-y-1 p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <SeverityBadge value={s.severity} />
                    <code className="text-sm font-semibold">{s.code}</code>
                    <span className="text-xs text-slate-500">
                      +{s.score} pts
                    </span>
                  </div>
                  <h3 className="font-medium">{s.title}</h3>
                  <p className="text-sm text-slate-700">{s.message}</p>
                  <details className="text-xs text-slate-500">
                    <summary className="cursor-pointer">evidence</summary>
                    <pre className="mt-1 overflow-auto rounded bg-slate-50 p-2">
                      {JSON.stringify(s.evidence, null, 2)}
                    </pre>
                  </details>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>JSON brut</CardTitle>
            </CardHeader>
            <div className="p-4">
              <pre className="overflow-auto rounded bg-slate-50 p-3 text-xs">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          </Card>
        </section>
      )}
    </main>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <span className="[&_input]:w-full [&_input]:rounded [&_input]:border [&_input]:border-slate-300 [&_input]:bg-white [&_input]:px-2 [&_input]:py-1.5 [&_input]:text-sm">
        {children}
      </span>
    </label>
  );
}
