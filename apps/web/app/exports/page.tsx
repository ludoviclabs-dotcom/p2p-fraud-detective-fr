import Link from "next/link";
import { ArrowRight, ArrowUpRight } from "lucide-react";

import { CaseWorkflowExport } from "@/components/case-workflow-export";
import { getP2PDataset } from "@/data/get-dataset";
import { SEVERITY_ORDER } from "@/lib/p2p-demo-taxonomy";

export default function ExportsPage() {
  const dataset = getP2PDataset();
  const suggestedCases = [...dataset.findings]
    .sort(
      (a, b) =>
        SEVERITY_ORDER[b.severity] - SEVERITY_ORDER[a.severity] ||
        b.riskScore - a.riskScore ||
        b.exposureEur - a.exposureEur,
    )
    .slice(0, 40)
    .map((finding) => ({
      id: `case:${finding.id}`,
      findingId: finding.id,
      invoiceId: finding.invoiceId,
      vendorId: finding.vendorId,
      vendorName: finding.vendorName,
      ruleId: finding.ruleId,
      signal: finding.signal,
      severity: finding.severity,
      exposureEur: finding.exposureEur,
      riskScore: finding.riskScore,
    }));

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#5a6478]">
            Audit trail
          </p>
          <h1 className="mt-2 text-3xl font-semibold text-[#141927]">
            Registre et exports
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-[#5a6478]">
            Qualification locale des cas P2P : statut, decision, responsable, note
            d'investigation et export CSV/JSON. La V1 reste statique et compatible
            Vercel ; une API FastAPI pourra reprendre ce contrat plus tard.
          </p>
        </div>
        <Link
          href="/score"
          className="inline-flex h-10 items-center gap-2 rounded-md bg-[#1f3a6e] px-4 text-sm font-semibold text-white"
        >
          Ouvrir les scores
          <ArrowUpRight aria-hidden className="h-4 w-4" />
        </Link>
      </div>

      <section className="mt-6 grid gap-3 md:grid-cols-4">
        {[
          ["1", "Dashboard", "/dashboard"],
          ["2", "Graphe rings", "/rings"],
          ["3", "Score detaille", "/score"],
          ["4", "Export audit", "/exports"],
        ].map(([step, label, href]) => (
          <Link
            key={step}
            href={href}
            className="flex min-h-20 items-center justify-between gap-3 rounded-md border border-[#e6ebf2] bg-white px-4 py-3 text-sm font-semibold text-[#141927] shadow-sm"
          >
            <span className="flex items-center gap-3">
              <span className="mono grid h-7 w-7 place-items-center rounded bg-[#eaf1ff] text-xs text-[#1f3a6e]">
                {step}
              </span>
              {label}
            </span>
            <ArrowRight aria-hidden className="h-4 w-4 text-[#1f3a6e]" />
          </Link>
        ))}
      </section>

      <div className="mt-6">
        <CaseWorkflowExport suggestedCases={suggestedCases} />
      </div>
    </div>
  );
}
