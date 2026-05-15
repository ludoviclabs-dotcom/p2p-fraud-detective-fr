import Link from "next/link";
import { ArrowRight, CircleAlert, Euro, Landmark, Network } from "lucide-react";

import { getP2PDataset } from "@/data/get-dataset";
import { formatDate, formatEuro, formatNumber } from "@/lib/format";

const cards = [
  { key: "exposureEur", label: "Exposition graphe", icon: Euro, format: formatEuro },
  { key: "findingCount", label: "Findings graph", icon: CircleAlert, format: formatNumber },
  { key: "vendorCount", label: "Fournisseurs liés", icon: Landmark, format: formatNumber },
  { key: "sharedIbanRings", label: "Anneaux IBAN", icon: Network, format: formatNumber },
] as const;

export default function DashboardPage() {
  const dataset = getP2PDataset();
  const topVendors = dataset.vendors.slice(0, 6);

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-8">
      <header className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#1F3A6E]">
            Cockpit Vercel
          </p>
          <h1 className="mt-2 text-4xl font-semibold tracking-tight text-[#141927]">
            Graphe P2P prêt pour démonstration commerciale.
          </h1>
          <p className="mt-4 max-w-3xl text-base leading-7 text-[#5A6478]">
            Une surface Next.js légère qui expose le signal le plus visuel du moteur Python :
            fournisseurs, IBAN masqués et findings reliés dans une topologie d&apos;investigation.
          </p>
        </div>
        <Link
          href="/rings"
          className="inline-flex items-center justify-center gap-2 rounded-md bg-[#1F3A6E] px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-[#0F1B33]"
        >
          Ouvrir le graphe
          <ArrowRight aria-hidden className="h-4 w-4" />
        </Link>
      </header>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => {
          const Icon = card.icon;
          const value = dataset.metrics[card.key];
          return (
            <article key={card.key} className="panel rounded-md p-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-[0.14em] text-[#5A6478]">
                  {card.label}
                </span>
                <Icon aria-hidden className="h-5 w-5 text-[#E5A93A]" />
              </div>
              <p className="mono mt-4 text-3xl font-semibold text-[#0F1B33]">
                {card.format(value)}
              </p>
            </article>
          );
        })}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
        <article className="panel rounded-md p-6">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold text-[#141927]">Top fournisseurs exposés</h2>
              <p className="mt-1 text-sm text-[#5A6478]">
                Tri par score puis exposition, depuis l&apos;export statique.
              </p>
            </div>
            <Network aria-hidden className="h-5 w-5 text-[#1F3A6E]" />
          </div>

          <div className="mt-5 overflow-hidden rounded-md border border-[#D8DEE9]">
            <table className="w-full border-collapse text-left text-sm">
              <thead className="bg-[#EEF2F7] text-xs uppercase tracking-[0.12em] text-[#5A6478]">
                <tr>
                  <th className="px-4 py-3 font-semibold">Fournisseur</th>
                  <th className="px-4 py-3 font-semibold">Sévérité</th>
                  <th className="px-4 py-3 font-semibold">Score</th>
                  <th className="px-4 py-3 font-semibold">Exposition</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#D8DEE9] bg-white">
                {topVendors.map((vendor) => (
                  <tr key={vendor.id}>
                    <td className="px-4 py-3 font-medium text-[#141927]">
                      <Link href={`/vendors/${vendor.vendorId}`} className="hover:text-[#1F3A6E]">
                        {vendor.name}
                      </Link>
                    </td>
                    <td className="px-4 py-3 capitalize text-[#5A6478]">{vendor.severity}</td>
                    <td className="mono px-4 py-3 text-[#141927]">{vendor.riskScore}/100</td>
                    <td className="mono px-4 py-3 text-[#141927]">
                      {formatEuro(vendor.exposureEur)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>

        <article className="panel rounded-md p-6">
          <h2 className="text-xl font-semibold text-[#141927]">État du dataset</h2>
          <dl className="mt-5 space-y-4 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-[#5A6478]">Généré le</dt>
              <dd className="mono text-right text-[#141927]">{formatDate(dataset.generatedAt)}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-[#5A6478]">Factures source</dt>
              <dd className="mono text-[#141927]">{formatNumber(dataset.metrics.invoiceCount)}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-[#5A6478]">Nœuds IBAN</dt>
              <dd className="mono text-[#141927]">
                {formatNumber(dataset.metrics.ibanNodeCount)}
              </dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-[#5A6478]">Liens graphe</dt>
              <dd className="mono text-[#141927]">{formatNumber(dataset.metrics.edgeCount)}</dd>
            </div>
          </dl>
        </article>
      </section>
    </div>
  );
}
