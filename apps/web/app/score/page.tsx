import Link from "next/link";
import { ArrowUpRight, GitBranch, ShieldAlert } from "lucide-react";

import { getP2PDataset } from "@/data/get-dataset";
import { CaseWorkflowStatusBadge } from "@/components/case-workflow-status-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SeverityBadge } from "@/components/ui/badge";
import { formatEuro, formatNumber } from "@/lib/p2p-demo-format";
import { getSignalLabel, SEVERITY_ORDER } from "@/lib/p2p-demo-taxonomy";

export default function ScoreIndexPage() {
  const dataset = getP2PDataset();
  const findings = [...dataset.findings]
    .sort(
      (a, b) =>
        SEVERITY_ORDER[b.severity] - SEVERITY_ORDER[a.severity] ||
        b.riskScore - a.riskScore ||
        b.exposureEur - a.exposureEur,
    )
    .slice(0, 80);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#5A6478]">
            Detection
          </p>
          <h1 className="mt-2 text-3xl font-semibold text-[#141927]">
            Explorateur de score
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-[#5A6478]">
            File statique des invoices les plus risquees. Chaque score ouvre le contexte
            preuve, fournisseur et graphe associe.
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
        <Kpi label="Findings" value={formatNumber(dataset.metrics.findingCount)} />
        <Kpi label="Critical" value={formatNumber(dataset.metrics.criticalFindings)} />
        <Kpi label="Exposition" value={formatEuro(dataset.metrics.exposureEur)} />
      </section>

      <Card className="mt-6">
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle>Scores prioritaires</CardTitle>
          <ShieldAlert aria-hidden className="h-5 w-5 text-[#A23E48]" />
        </CardHeader>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-[#F6F7FB] text-[#5A6478]">
              <tr>
                <th className="px-4 py-3 text-left">Invoice</th>
                <th className="px-4 py-3 text-left">Fournisseur</th>
                <th className="px-4 py-3 text-left">Signal</th>
                <th className="px-4 py-3 text-left">Severite</th>
                <th className="px-4 py-3 text-left">Workflow</th>
                <th className="px-4 py-3 text-right">Score</th>
                <th className="px-4 py-3 text-right">Exposition</th>
              </tr>
            </thead>
            <tbody>
              {findings.map((finding) => (
                <tr key={finding.id} className="border-t border-[#E6EBF2]">
                  <td className="px-4 py-3">
                    <Link
                      href={`/score/${finding.invoiceId}`}
                      className="mono text-xs font-semibold text-[#1F3A6E]"
                    >
                      {finding.invoiceId}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/vendors/${finding.vendorId}`}
                      className="font-medium text-[#141927] hover:text-[#1F3A6E]"
                    >
                      {finding.vendorName}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-[#141927]">
                    {getSignalLabel(finding.signal)}
                  </td>
                  <td className="px-4 py-3">
                    <SeverityBadge value={finding.severity} />
                  </td>
                  <td className="px-4 py-3">
                    <CaseWorkflowStatusBadge caseIds={[`case:${finding.id}`]} />
                  </td>
                  <td className="mono px-4 py-3 text-right text-[#141927]">
                    {finding.riskScore}/100
                  </td>
                  <td className="mono px-4 py-3 text-right text-[#141927]">
                    {formatEuro(finding.exposureEur)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card className="mt-6">
        <CardContent className="flex flex-col gap-3 text-sm text-[#5A6478] sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <GitBranch aria-hidden className="h-4 w-4 text-[#1F3A6E]" />
            Le score detaille reste relie au graphe d'investigation.
          </div>
          <Link href="/rings" className="font-semibold text-[#1F3A6E]">
            Voir les anneaux
          </Link>
        </CardContent>
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
