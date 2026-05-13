"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useParams } from "next/navigation";
import {
  AreaChart,
  Area,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  getVendorSummary,
  getVendorTimeline,
  listFindings,
} from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SeverityBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LlmNarrativeStream } from "@/components/llm-narrative-stream";
import { formatDate, formatEur } from "@/lib/utils";

const TABS = ["profile", "timeline", "findings"] as const;
type TabKey = (typeof TABS)[number];

export default function VendorDetailPage() {
  const params = useParams<{ id: string }>();
  const vendorId = params?.id ?? "";
  const [tab, setTab] = useState<TabKey>("profile");

  const summary = useQuery({
    queryKey: ["vendor", vendorId],
    queryFn: () => getVendorSummary(vendorId),
    enabled: !!vendorId,
  });
  const timeline = useQuery({
    queryKey: ["vendor-timeline", vendorId],
    queryFn: () => getVendorTimeline(vendorId, 30),
    enabled: !!vendorId,
  });
  const findings = useQuery({
    queryKey: ["vendor-findings", vendorId],
    queryFn: () => listFindings({ limit: 100 }),
    enabled: !!vendorId && tab === "findings",
  });

  // Construire la série exposition 30j depuis la timeline
  const expSeries = (() => {
    const events = timeline.data ?? [];
    const byDay = new Map<string, number>();
    for (const e of events) {
      const day = e.at.slice(0, 10);
      byDay.set(day, (byDay.get(day) ?? 0) + (e.amount_eur ?? 0));
    }
    const today = new Date();
    const points: { date: string; value: number }[] = [];
    for (let i = 29; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(d.getDate() - i);
      const iso = d.toISOString().slice(0, 10);
      points.push({ date: iso.slice(5), value: byDay.get(iso) ?? 0 });
    }
    return points;
  })();
  const exp30dTotal = expSeries.reduce((s, p) => s + p.value, 0);

  // Filter findings by vendor
  const vendorFindings = (findings.data ?? []).filter(
    (f) => (f.evidence?.vendor_id as string | undefined) === vendorId,
  );

  return (
    <div className="px-8 py-10">
      <div className="mb-1 text-xs uppercase tracking-wider text-[#5a6478]">
        Investigation
      </div>
      <h1 className="mb-1 text-3xl font-bold text-[#0f1b33] dark:text-white">
        Fiche fournisseur 360°
      </h1>
      <p className="mb-6 font-mono text-sm text-[#5a6478]">{vendorId}</p>

      {summary.isLoading ? (
        <div className="text-sm text-[#5a6478]">Chargement…</div>
      ) : summary.error ? (
        <div className="rounded border border-[#a23e48] bg-[#fdecee] p-4 text-sm text-[#a23e48]">
          API indisponible : {(summary.error as Error).message}
        </div>
      ) : (
        <>
          <div className="mb-4 grid gap-3 md:grid-cols-4">
            <Card>
              <CardContent>
                <div className="text-xs uppercase tracking-wider text-[#5a6478]">
                  Nom
                </div>
                <div className="text-lg font-semibold text-[#0f1b33]">
                  {summary.data?.vendor_name ?? "—"}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent>
                <div className="text-xs uppercase tracking-wider text-[#5a6478]">
                  SIREN
                </div>
                <div className="font-mono text-lg text-[#0f1b33]">
                  {summary.data?.siren ?? "—"}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent>
                <div className="text-xs uppercase tracking-wider text-[#5a6478]">
                  Paiements
                </div>
                <div className="text-lg font-semibold text-[#0f1b33]">
                  {formatEur(summary.data?.total_paid_eur)}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent>
                <div className="text-xs uppercase tracking-wider text-[#5a6478]">
                  Cases
                </div>
                <div className="text-lg font-semibold text-[#0f1b33]">
                  {summary.data?.n_invoices ?? 0}
                </div>
              </CardContent>
            </Card>
          </div>

          {summary.data?.is_sanctioned ? (
            <div className="mb-4 rounded border border-[#a23e48] bg-[#fdecee] p-3 text-sm text-[#a23e48]">
              🚨 Fournisseur SANCTIONNÉ — paiement à bloquer (LCB-FT).
            </div>
          ) : summary.data?.is_pep ? (
            <div className="mb-4 rounded border border-[#c97b1f] bg-[#fff8ec] p-3 text-sm text-[#c97b1f]">
              ⚠️ Lien PEP détecté — vigilance renforcée (Sapin 2).
            </div>
          ) : null}

          {/* Sparkline trend 30j */}
          {exp30dTotal > 0 ? (
            <Card className="mb-4">
              <CardHeader>
                <CardTitle>
                  📈 Exposition 30 derniers jours : {formatEur(exp30dTotal)}
                </CardTitle>
              </CardHeader>
              <CardContent className="h-32">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={expSeries}>
                    <defs>
                      <linearGradient id="g-vendor" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#1f3a6e" stopOpacity={0.4} />
                        <stop offset="100%" stopColor="#1f3a6e" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 10 }} />
                    <Tooltip
                      formatter={(v) => formatEur(Number(v))}
                      labelStyle={{ color: "#0f1b33", fontSize: 12 }}
                    />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="#1f3a6e"
                      strokeWidth={2}
                      fill="url(#g-vendor)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          ) : null}

          {/* Tabs */}
          <div className="mb-4 flex gap-1 border-b border-[#e1e5ee]">
            {TABS.map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`px-4 py-2 text-sm font-medium transition-colors ${
                  tab === t
                    ? "border-b-2 border-[#1f3a6e] text-[#0f1b33]"
                    : "text-[#5a6478] hover:text-[#0f1b33]"
                }`}
              >
                {t === "profile"
                  ? "Profil"
                  : t === "timeline"
                    ? "Timeline 30j"
                    : "Findings"}
              </button>
            ))}
          </div>

          {tab === "profile" ? (
            <Card>
              <CardContent>
                <dl className="grid grid-cols-2 gap-3 text-sm">
                  {summary.data &&
                    Object.entries(summary.data).map(([k, v]) => (
                      <div key={k}>
                        <dt className="font-mono text-xs text-[#5a6478]">
                          {k}
                        </dt>
                        <dd className="text-[#0f1b33]">
                          {String(v ?? "—")}
                        </dd>
                      </div>
                    ))}
                </dl>
                <div className="mt-4">
                  <LlmNarrativeStream
                    vendorId={vendorId}
                    vendorName={summary.data?.vendor_name}
                    siren={summary.data?.siren}
                    totalPaidEur={summary.data?.total_paid_eur}
                    nInvoices={summary.data?.n_invoices ?? 0}
                    isSanctioned={summary.data?.is_sanctioned ?? false}
                    isPep={summary.data?.is_pep ?? false}
                  />
                </div>
              </CardContent>
            </Card>
          ) : tab === "timeline" ? (
            <Card>
              <div className="overflow-x-auto">
                {timeline.isLoading ? (
                  <div className="p-4 text-sm text-[#5a6478]">Chargement…</div>
                ) : !timeline.data?.length ? (
                  <div className="p-4 text-sm text-[#5a6478]">
                    Aucun événement sur 30 jours.
                  </div>
                ) : (
                  <table className="w-full text-sm">
                    <thead className="bg-[#f4f6fa] text-[#5a6478]">
                      <tr>
                        <th className="px-3 py-2 text-left">Date</th>
                        <th className="px-3 py-2 text-left">Type</th>
                        <th className="px-3 py-2 text-left">Label</th>
                        <th className="px-3 py-2 text-left">Sévérité</th>
                        <th className="px-3 py-2 text-right">Montant</th>
                      </tr>
                    </thead>
                    <tbody>
                      {timeline.data.map((e, i) => (
                        <tr
                          key={`${e.at}-${i}`}
                          className="border-t border-[#e1e5ee]"
                        >
                          <td className="px-3 py-2 text-xs text-[#5a6478]">
                            {formatDate(e.at)}
                          </td>
                          <td className="px-3 py-2 font-mono text-xs">
                            {e.kind}
                          </td>
                          <td className="px-3 py-2">{e.label}</td>
                          <td className="px-3 py-2">
                            {e.severity ? (
                              <SeverityBadge value={e.severity} />
                            ) : (
                              "—"
                            )}
                          </td>
                          <td className="px-3 py-2 text-right">
                            {formatEur(e.amount_eur ?? null)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </Card>
          ) : (
            <Card>
              <div className="overflow-x-auto">
                {findings.isLoading ? (
                  <div className="p-4 text-sm text-[#5a6478]">Chargement…</div>
                ) : !vendorFindings.length ? (
                  <div className="p-4 text-sm text-[#5a6478]">
                    Aucun finding pour ce fournisseur.
                  </div>
                ) : (
                  <table className="w-full text-sm">
                    <thead className="bg-[#f4f6fa] text-[#5a6478]">
                      <tr>
                        <th className="px-3 py-2 text-left">Invoice ID</th>
                        <th className="px-3 py-2 text-left">Rule</th>
                        <th className="px-3 py-2 text-left">Sévérité</th>
                        <th className="px-3 py-2 text-left">Signal</th>
                        <th className="px-3 py-2 text-right">Exposition</th>
                      </tr>
                    </thead>
                    <tbody>
                      {vendorFindings.map((f) => {
                        const exp = f.evidence?.exposure_eur as
                          | number
                          | undefined;
                        return (
                          <tr
                            key={`${f.invoice_id}-${f.rule_id}`}
                            className="border-t border-[#e1e5ee]"
                          >
                            <td className="px-3 py-2 font-mono text-xs">
                              {f.invoice_id}
                            </td>
                            <td className="px-3 py-2 font-mono text-xs">
                              {f.rule_id}
                            </td>
                            <td className="px-3 py-2">
                              <SeverityBadge value={f.severity} />
                            </td>
                            <td className="px-3 py-2">{f.signal}</td>
                            <td className="px-3 py-2 text-right">
                              {formatEur(exp)}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
