import Link from "next/link";
import { ArrowUpRight, BriefcaseBusiness } from "lucide-react";

import { getP2PDataset } from "@/data/get-dataset";
import { CaseWorkflowStatusBadge } from "@/components/case-workflow-status-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SeverityBadge } from "@/components/ui/badge";
import { formatEuro, formatNumber } from "@/lib/p2p-demo-format";
import { SEVERITY_ORDER } from "@/lib/p2p-demo-taxonomy";

export default function VendorsIndexPage() {
  const dataset = getP2PDataset();
  const vendors = [...dataset.vendors]
    .sort(
      (a, b) =>
        SEVERITY_ORDER[b.severity] - SEVERITY_ORDER[a.severity] ||
        b.exposureEur - a.exposureEur ||
        b.riskScore - a.riskScore,
    )
    .slice(0, 80);

  const criticalVendors = dataset.vendors.filter(
    (vendor) => vendor.severity === "critical",
  ).length;

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#5A6478]">
            Investigation
          </p>
          <h1 className="mt-2 text-3xl font-semibold text-[#141927]">
            Fournisseurs exposes
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-[#5A6478]">
            Index statique issu du dataset de demonstration. Chaque ligne ouvre une fiche
            fournisseur 360 connectee aux findings et au graphe.
          </p>
        </div>
        <Link
          href="/rings"
          className="inline-flex h-10 items-center gap-2 rounded-md bg-[#1F3A6E] px-4 text-sm font-semibold text-white"
        >
          Explorer le graphe
          <ArrowUpRight aria-hidden className="h-4 w-4" />
        </Link>
      </div>

      <section className="mt-6 grid gap-4 md:grid-cols-3">
        <Kpi label="Fournisseurs" value={formatNumber(dataset.metrics.vendorCount)} />
        <Kpi label="Critical" value={formatNumber(criticalVendors)} />
        <Kpi label="Exposition graphe" value={formatEuro(dataset.metrics.exposureEur)} />
      </section>

      <Card className="mt-6">
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle>Top fournisseurs a investiguer</CardTitle>
          <BriefcaseBusiness aria-hidden className="h-5 w-5 text-[#1F3A6E]" />
        </CardHeader>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-[#F6F7FB] text-[#5A6478]">
              <tr>
                <th className="px-4 py-3 text-left">Fournisseur</th>
                <th className="px-4 py-3 text-left">SIREN</th>
                <th className="px-4 py-3 text-left">Severite</th>
                <th className="px-4 py-3 text-left">Workflow</th>
                <th className="px-4 py-3 text-right">Score</th>
                <th className="px-4 py-3 text-right">Findings</th>
                <th className="px-4 py-3 text-right">Exposition</th>
              </tr>
            </thead>
            <tbody>
              {vendors.map((vendor) => (
                <tr key={vendor.id} className="border-t border-[#E6EBF2]">
                  <td className="px-4 py-3">
                    <Link
                      href={`/vendors/${vendor.vendorId}`}
                      className="font-semibold text-[#1F3A6E] hover:underline"
                    >
                      {vendor.name}
                    </Link>
                    <div className="mono mt-1 text-xs text-[#5A6478]">{vendor.vendorId}</div>
                  </td>
                  <td className="mono px-4 py-3 text-xs text-[#141927]">
                    {vendor.siren ?? "-"}
                  </td>
                  <td className="px-4 py-3">
                    <SeverityBadge value={vendor.severity} />
                  </td>
                  <td className="px-4 py-3">
                    <CaseWorkflowStatusBadge
                      caseIds={vendor.findingIds.map((id) => `case:${id}`)}
                      vendorId={vendor.vendorId}
                    />
                  </td>
                  <td className="mono px-4 py-3 text-right text-[#141927]">
                    {vendor.riskScore}/100
                  </td>
                  <td className="mono px-4 py-3 text-right text-[#141927]">
                    {vendor.findingIds.length}
                  </td>
                  <td className="mono px-4 py-3 text-right text-[#141927]">
                    {formatEuro(vendor.exposureEur)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardContent>
        <div className="text-xs font-semibold uppercase tracking-[0.14em] text-[#5A6478]">
          {label}
        </div>
        <div className="mt-2 text-2xl font-semibold text-[#141927]">{value}</div>
      </CardContent>
    </Card>
  );
}
