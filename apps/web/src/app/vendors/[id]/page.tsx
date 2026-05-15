import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { getP2PDataset, getVendor } from "@/data/get-dataset";
import { formatEuro } from "@/lib/format";

export default async function VendorPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const vendor = getVendor(id);
  if (!vendor) notFound();

  const findings = getP2PDataset().findings.filter((finding) =>
    vendor.findingIds.includes(finding.id),
  );

  return (
    <div className="mx-auto max-w-5xl">
      <Link href="/rings" className="inline-flex items-center gap-2 text-sm font-semibold text-[#1F3A6E]">
        <ArrowLeft aria-hidden className="h-4 w-4" />
        Retour au graphe
      </Link>
      <section className="panel mt-6 rounded-md p-6">
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#1F3A6E]">
          Fiche fournisseur
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-[#141927]">{vendor.name}</h1>
        <dl className="mt-6 grid gap-4 md:grid-cols-4">
          <div>
            <dt className="text-xs uppercase tracking-[0.14em] text-[#5A6478]">SIREN</dt>
            <dd className="mono mt-1 text-[#141927]">{vendor.siren ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-[0.14em] text-[#5A6478]">APE</dt>
            <dd className="mono mt-1 text-[#141927]">{vendor.apeCode ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-[0.14em] text-[#5A6478]">Score</dt>
            <dd className="mono mt-1 text-[#141927]">{vendor.riskScore}/100</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-[0.14em] text-[#5A6478]">Exposition</dt>
            <dd className="mono mt-1 text-[#141927]">{formatEuro(vendor.exposureEur)}</dd>
          </div>
        </dl>
      </section>

      <section className="panel mt-6 rounded-md p-6">
        <h2 className="text-xl font-semibold text-[#141927]">Findings liés</h2>
        <div className="mt-4 divide-y divide-[#D8DEE9]">
          {findings.map((finding) => (
            <article key={finding.id} className="py-4">
              <div className="flex flex-col justify-between gap-2 md:flex-row">
                <div>
                  <p className="font-semibold text-[#141927]">{finding.ruleId}</p>
                  <p className="mono mt-1 text-sm text-[#5A6478]">{finding.invoiceId}</p>
                </div>
                <p className="mono text-sm text-[#141927]">{formatEuro(finding.exposureEur)}</p>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
