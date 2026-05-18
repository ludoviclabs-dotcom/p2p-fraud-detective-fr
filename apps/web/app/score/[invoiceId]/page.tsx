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

import { getFinding, getFindingContext, getFindingVendor } from "@/data/get-dataset";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SeverityBadge } from "@/components/ui/badge";
import { formatEuro, formatNumber } from "@/lib/p2p-demo-format";
import { getSignalLabel } from "@/lib/p2p-demo-taxonomy";

export default async function ScoreDetailPage({
  params,
}: {
  params: Promise<{ invoiceId: string }>;
}) {
  const { invoiceId } = await params;
  const finding = getFinding(invoiceId);
  if (!finding) notFound();

  const vendor = getFindingVendor(finding);
  const context = getFindingContext(finding.id);
  const ibanNodes = context.nodes.filter((node) => node.kind === "iban");
  const vendorNodes = context.nodes.filter((node) => node.kind === "vendor");

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      <Link
        href="/rings"
        className="inline-flex items-center gap-2 text-sm font-semibold text-[#1F3A6E]"
      >
        <ArrowLeft aria-hidden className="h-4 w-4" />
        Retour au graphe
      </Link>

      <section className="mt-6 rounded-md border border-[#D8DEE9] bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#5A6478]">
              Score investigation
            </p>
            <h1 className="mt-2 text-3xl font-semibold text-[#141927]">
              {finding.invoiceId}
            </h1>
            <p className="mt-2 text-sm text-[#5A6478]">
              {getSignalLabel(finding.signal)} - {finding.ruleId}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <SeverityBadge value={finding.severity} />
            <span className="mono rounded-md bg-[#F6F7FB] px-3 py-2 text-sm text-[#141927]">
              {finding.riskScore}/100
            </span>
          </div>
        </div>
      </section>

      <section className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          icon={<BadgeEuro aria-hidden className="h-5 w-5" />}
          label="Exposition"
          value={formatEuro(finding.exposureEur)}
        />
        <KpiCard
          icon={<FileSearch aria-hidden className="h-5 w-5" />}
          label="Rule"
          value={finding.ruleId}
        />
        <KpiCard
          icon={<Network aria-hidden className="h-5 w-5" />}
          label="Noeuds lies"
          value={formatNumber(context.nodes.length)}
        />
        <KpiCard
          icon={<ShieldAlert aria-hidden className="h-5 w-5" />}
          label="Findings connexes"
          value={formatNumber(context.relatedFindings.length)}
        />
      </section>

      <section className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-5">
          <Card>
            <CardHeader>
              <CardTitle>Preuve exploitable</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid gap-4 md:grid-cols-2">
                {Object.entries(finding.evidence).map(([key, value]) => (
                  <div key={key} className="rounded-md border border-[#E6EBF2] bg-[#F6F7FB] p-4">
                    <dt className="mono text-xs uppercase tracking-[0.12em] text-[#5A6478]">
                      {key}
                    </dt>
                    <dd className="mt-2 text-sm font-medium text-[#141927]">
                      {renderEvidenceValue(value)}
                    </dd>
                  </div>
                ))}
              </dl>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Findings connexes dans le graphe</CardTitle>
            </CardHeader>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-[#F6F7FB] text-[#5A6478]">
                  <tr>
                    <th className="px-4 py-3 text-left">Invoice</th>
                    <th className="px-4 py-3 text-left">Signal</th>
                    <th className="px-4 py-3 text-left">Severite</th>
                    <th className="px-4 py-3 text-right">Exposition</th>
                  </tr>
                </thead>
                <tbody>
                  {context.relatedFindings.slice(0, 10).map((item) => (
                    <tr key={item.id} className="border-t border-[#E6EBF2]">
                      <td className="px-4 py-3">
                        <Link
                          href={`/score/${item.invoiceId}`}
                          className="mono text-xs font-semibold text-[#1F3A6E]"
                        >
                          {item.invoiceId}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-[#141927]">
                        {getSignalLabel(item.signal)}
                      </td>
                      <td className="px-4 py-3">
                        <SeverityBadge value={item.severity} />
                      </td>
                      <td className="mono px-4 py-3 text-right text-[#141927]">
                        {formatEuro(item.exposureEur)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>

        <aside className="space-y-5">
          <Card>
            <CardHeader>
              <CardTitle>Fournisseur</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <div className="font-semibold text-[#141927]">{finding.vendorName}</div>
                <div className="mono mt-1 text-xs text-[#5A6478]">{finding.vendorId}</div>
              </div>
              {vendor ? (
                <>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="rounded-md bg-[#F6F7FB] p-3">
                      <div className="text-xs text-[#5A6478]">SIREN</div>
                      <div className="mono mt-1 text-[#141927]">{vendor.siren ?? "-"}</div>
                    </div>
                    <div className="rounded-md bg-[#F6F7FB] p-3">
                      <div className="text-xs text-[#5A6478]">Score</div>
                      <div className="mono mt-1 text-[#141927]">{vendor.riskScore}/100</div>
                    </div>
                  </div>
                  <Link
                    href={`/vendors/${vendor.vendorId}`}
                    className="inline-flex items-center gap-2 rounded-md bg-[#1F3A6E] px-3 py-2 text-sm font-semibold text-white"
                  >
                    Ouvrir la fiche
                    <ArrowUpRight aria-hidden className="h-4 w-4" />
                  </Link>
                </>
              ) : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Contexte graphe</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <GraphNodeList
                title="IBAN masques"
                items={ibanNodes.map((node) => node.maskedValue ?? node.label)}
              />
              <GraphNodeList
                title="Fournisseurs relies"
                items={vendorNodes.map((node) => node.label)}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Prochaine action</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm leading-6 text-[#5A6478]">
              <p>
                Valider la piece source, verifier l'IBAN masque, puis rattacher la
                conclusion a la fiche fournisseur avant export audit.
              </p>
              <Link
                href="/exports"
                className="inline-flex items-center gap-2 font-semibold text-[#1F3A6E]"
              >
                Preparer l'export
                <ArrowUpRight aria-hidden className="h-4 w-4" />
              </Link>
            </CardContent>
          </Card>
        </aside>
      </section>
    </div>
  );
}

function renderEvidenceValue(value: unknown): string {
  if (Array.isArray(value)) return value.join(", ");
  if (value && typeof value === "object") return JSON.stringify(value);
  return String(value ?? "-");
}

function GraphNodeList({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <div className="text-xs font-semibold uppercase tracking-[0.12em] text-[#5A6478]">
        {title}
      </div>
      {items.length ? (
        <div className="mt-2 space-y-2">
          {items.slice(0, 8).map((item) => (
            <div
              key={item}
              className="mono rounded-md bg-[#F6F7FB] px-3 py-2 text-xs text-[#141927]"
            >
              {item}
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-2 text-[#5A6478]">Aucun noeud direct.</p>
      )}
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
        <div className="grid h-10 w-10 place-items-center rounded-md bg-[#EAF1FF] text-[#1F3A6E]">
          {icon}
        </div>
        <div className="mt-4 text-xs font-semibold uppercase tracking-[0.14em] text-[#5A6478]">
          {label}
        </div>
        <div className="mt-2 break-words text-xl font-semibold text-[#141927]">{value}</div>
      </CardContent>
    </Card>
  );
}
