import Link from "next/link";
import { notFound } from "next/navigation";
import type { ReactNode } from "react";
import {
  ArrowLeft,
  ArrowUpRight,
  BadgeEuro,
  FileSearch,
  Network,
  ShieldAlert,
} from "lucide-react";

import { getP2PDataset, getVendor, getVendorFindings } from "@/data/get-dataset";
import { CaseWorkflowPanel } from "@/components/case-workflow-panel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SeverityBadge } from "@/components/ui/badge";
import { formatEuro, formatNumber } from "@/lib/p2p-demo-format";
import { getSignalLabel, SEVERITY_ORDER } from "@/lib/p2p-demo-taxonomy";

export default async function VendorDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const vendor = getVendor(id);
  if (!vendor) notFound();

  const dataset = getP2PDataset();
  const findings = getVendorFindings(id);
  const signalCounts = findings.reduce<Record<string, number>>((counts, finding) => {
    counts[finding.signal] = (counts[finding.signal] ?? 0) + 1;
    return counts;
  }, {});

  const ibanConnections = dataset.edges
    .filter((edge) => edge.kind === "uses_iban" && edge.source === vendor.id)
    .map((edge) => {
      const node = dataset.nodes.find((item) => item.id === edge.target);
      return node ? { edge, node } : null;
    })
    .filter((item): item is NonNullable<typeof item> => Boolean(item))
    .sort((a, b) => b.edge.findingIds.length - a.edge.findingIds.length);

  const topFindings = findings.slice(0, 12);
  const leadFinding = topFindings[0];
  const findingTotal = findings.length;
  const criticalOrHigh = findings.filter(
    (finding) => SEVERITY_ORDER[finding.severity] >= SEVERITY_ORDER.high,
  ).length;

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-wrap gap-3">
        <Link
          href="/rings"
          className="inline-flex items-center gap-2 text-sm font-semibold text-[#1F3A6E]"
        >
          <ArrowLeft aria-hidden className="h-4 w-4" />
          Retour au graphe
        </Link>
        <Link
          href="/vendors"
          className="inline-flex items-center gap-2 text-sm font-semibold text-[#5A6478]"
        >
          Liste fournisseurs
        </Link>
      </div>

      <section className="mt-6 rounded-md border border-[#D8DEE9] bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#5A6478]">
              Fiche fournisseur 360
            </p>
            <h1 className="mt-2 text-3xl font-semibold text-[#141927]">{vendor.name}</h1>
            <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-[#5A6478]">
              <span className="mono">{vendor.vendorId}</span>
              {vendor.siren ? <span>SIREN {vendor.siren}</span> : null}
              {vendor.apeCode ? <span>APE {vendor.apeCode}</span> : null}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <SeverityBadge value={vendor.severity} />
            <span className="mono rounded-md bg-[#F6F7FB] px-3 py-2 text-sm text-[#141927]">
              Score {vendor.riskScore}/100
            </span>
          </div>
        </div>
      </section>

      <section className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          icon={<BadgeEuro aria-hidden className="h-5 w-5" />}
          label="Exposition"
          value={formatEuro(vendor.exposureEur)}
        />
        <KpiCard
          icon={<FileSearch aria-hidden className="h-5 w-5" />}
          label="Findings"
          value={formatNumber(findingTotal)}
        />
        <KpiCard
          icon={<ShieldAlert aria-hidden className="h-5 w-5" />}
          label="Critical / high"
          value={formatNumber(criticalOrHigh)}
        />
        <KpiCard
          icon={<Network aria-hidden className="h-5 w-5" />}
          label="IBAN connectes"
          value={formatNumber(ibanConnections.length)}
        />
      </section>

      <section className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <Card>
          <CardHeader>
            <CardTitle>Findings relies au fournisseur</CardTitle>
          </CardHeader>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-[#F6F7FB] text-[#5A6478]">
                <tr>
                  <th className="px-4 py-3 text-left">Invoice</th>
                  <th className="px-4 py-3 text-left">Signal</th>
                  <th className="px-4 py-3 text-left">Severite</th>
                  <th className="px-4 py-3 text-right">Score</th>
                  <th className="px-4 py-3 text-right">Exposition</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {topFindings.map((finding) => (
                  <tr key={finding.id} className="border-t border-[#E6EBF2]">
                    <td className="mono px-4 py-3 text-xs text-[#141927]">
                      {finding.invoiceId}
                    </td>
                    <td className="px-4 py-3 text-[#141927]">
                      {getSignalLabel(finding.signal)}
                    </td>
                    <td className="px-4 py-3">
                      <SeverityBadge value={finding.severity} />
                    </td>
                    <td className="mono px-4 py-3 text-right text-[#141927]">
                      {finding.riskScore}/100
                    </td>
                    <td className="mono px-4 py-3 text-right text-[#141927]">
                      {formatEuro(finding.exposureEur)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Link
                        href={`/score/${finding.invoiceId}`}
                        className="inline-flex items-center gap-1 font-semibold text-[#1F3A6E]"
                      >
                        Ouvrir
                        <ArrowUpRight aria-hidden className="h-3.5 w-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        <aside className="space-y-5">
          {leadFinding ? (
            <CaseWorkflowPanel
              compact
              context={{
                id: `case:${leadFinding.id}`,
                findingId: leadFinding.id,
                invoiceId: leadFinding.invoiceId,
                vendorId: vendor.vendorId,
                vendorName: vendor.name,
                signal: leadFinding.signal,
                severity: leadFinding.severity,
                exposureEur: leadFinding.exposureEur,
                riskScore: leadFinding.riskScore,
              }}
            />
          ) : null}

          <Card>
            <CardHeader>
              <CardTitle>Breakdown signaux</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {Object.entries(signalCounts)
                .sort((a, b) => b[1] - a[1])
                .map(([signal, count]) => (
                  <div key={signal}>
                    <div className="flex items-center justify-between gap-3 text-sm">
                      <span className="font-medium text-[#141927]">{getSignalLabel(signal)}</span>
                      <span className="mono text-[#5A6478]">{count}</span>
                    </div>
                    <div className="mt-2 h-2 rounded-full bg-[#EEF3FB]">
                      <div
                        className="h-2 rounded-full bg-[#1F3A6E]"
                        style={{ width: `${Math.max((count / Math.max(findingTotal, 1)) * 100, 8)}%` }}
                      />
                    </div>
                  </div>
                ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Connexions IBAN</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {ibanConnections.length ? (
                ibanConnections.slice(0, 8).map(({ edge, node }) => (
                  <div
                    key={`${edge.source}-${edge.target}`}
                    className="rounded-md border border-[#E6EBF2] bg-[#F6F7FB] p-3"
                  >
                    <div className="mono text-xs text-[#141927]">
                      {node.maskedValue ?? node.label}
                    </div>
                    <div className="mt-1 text-xs text-[#5A6478]">
                      {edge.findingIds.length} finding(s) associe(s)
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-[#5A6478]">Aucune connexion IBAN directe.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Decision audit</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm leading-6 text-[#5A6478]">
              <p>
                Priorite a la revue des invoices critical/high, puis validation du RIB et
                recherche de fournisseurs partageant les memes coordonnees bancaires.
              </p>
              <Link
                href="/rings"
                className="inline-flex items-center gap-2 rounded-md bg-[#1F3A6E] px-3 py-2 font-semibold text-white"
              >
                Revenir au graphe
                <ArrowUpRight aria-hidden className="h-4 w-4" />
              </Link>
            </CardContent>
          </Card>
        </aside>
      </section>
    </div>
  );
}

function KpiCard({
  icon,
  label,
  value,
}: {
  icon: ReactNode;
  label: string;
  value: string;
}) {
  return (
    <Card>
      <CardContent>
        <div className="flex items-center justify-between gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-md bg-[#EAF1FF] text-[#1F3A6E]">
            {icon}
          </div>
        </div>
        <div className="mt-4 text-xs font-semibold uppercase tracking-[0.14em] text-[#5A6478]">
          {label}
        </div>
        <div className="mt-2 text-2xl font-semibold text-[#141927]">{value}</div>
      </CardContent>
    </Card>
  );
}
