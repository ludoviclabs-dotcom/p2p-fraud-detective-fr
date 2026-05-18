import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { getP2PDataset } from "@/data/get-dataset";
import { formatEuro } from "@/lib/p2p-demo-format";

export default async function ScorePage({ params }: { params: Promise<{ invoiceId: string }> }) {
  const { invoiceId } = await params;
  const finding = getP2PDataset().findings.find(
    (item) => item.invoiceId === invoiceId || item.id === invoiceId,
  );
  if (!finding) notFound();

  return (
    <div className="mx-auto max-w-4xl">
      <Link href="/rings" className="inline-flex items-center gap-2 text-sm font-semibold text-[#1F3A6E]">
        <ArrowLeft aria-hidden className="h-4 w-4" />
        Retour au graphe
      </Link>
      <section className="panel mt-6 rounded-md p-6">
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#1F3A6E]">
          Score placeholder
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-[#141927]">{finding.invoiceId}</h1>
        <dl className="mt-6 grid gap-4 md:grid-cols-3">
          <div>
            <dt className="text-xs uppercase tracking-[0.14em] text-[#5A6478]">Règle</dt>
            <dd className="mt-1 text-[#141927]">{finding.ruleId}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-[0.14em] text-[#5A6478]">Score</dt>
            <dd className="mono mt-1 text-[#141927]">{finding.riskScore}/100</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-[0.14em] text-[#5A6478]">Exposition</dt>
            <dd className="mono mt-1 text-[#141927]">{formatEuro(finding.exposureEur)}</dd>
          </div>
        </dl>
        <pre className="mt-6 overflow-auto rounded-md bg-[#0F1B33] p-4 text-xs leading-6 text-[#E9EDF5]">
          {JSON.stringify(finding.evidence, null, 2)}
        </pre>
      </section>
    </div>
  );
}
