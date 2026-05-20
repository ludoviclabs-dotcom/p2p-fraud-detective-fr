"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { listCases, type CaseOutV1 } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { SeverityBadge } from "@/components/ui/badge";
import { Scale, AlertTriangle } from "lucide-react";
import { formatEur } from "@/lib/utils";

export default function SanctionsPage() {
  const [search, setSearch] = useState("");

  const query = useQuery({
    queryKey: ["sanctions-cases"],
    queryFn: () => listCases({ limit: 500 }),
  });

  const sanctionsCases = useMemo(() => {
    return (query.data ?? []).filter((c) => {
      const t = (c.title || "").toLowerCase();
      return (
        t.includes("sanction") ||
        t.includes("pep") ||
        t.includes("ofac") ||
        t.includes("aml")
      );
    });
  }, [query.data]);

  const filteredCases = useMemo(() => {
    if (!search) return sanctionsCases;
    const q = search.toLowerCase();
    return sanctionsCases.filter(
      (c) =>
        c.vendor_id?.toLowerCase().includes(q) ||
        c.title.toLowerCase().includes(q) ||
        c.case_id.toLowerCase().includes(q),
    );
  }, [sanctionsCases, search]);

  const n_critical = sanctionsCases.filter((c) => c.severity === "critical").length;
  const n_pep = sanctionsCases.filter((c) =>
    (c.title || "").toLowerCase().includes("pep"),
  ).length;
  const n_listed = sanctionsCases.filter((c) =>
    (c.title || "").toLowerCase().includes("sanction"),
  ).length;
  const totalExposure = sanctionsCases.reduce(
    (s, c) => s + (c.exposure_eur ?? 0),
    0,
  );

  return (
    <div className="px-8 py-10">
      <div className="mb-1 text-xs uppercase tracking-wider text-[#5a6478]">
        Contrôles statistiques
      </div>
      <h1 className="mb-1 text-3xl font-bold text-[#0f1b33] dark:text-white">
        Sanctions & PEP
      </h1>
      <p className="mb-6 text-sm text-[#5a6478]">
        Croisement des fournisseurs avec OpenSanctions (UE consolidée, OFAC SDN,
        Trésor FR) + listes PEP. Source live activable via `ENRICHMENT_MODE=live`
        + `YENTE_BASE_URL` (cf. P5-1).
      </p>

      <div className="mb-4 grid gap-3 md:grid-cols-4">
        <Card>
          <CardContent>
            <div className="text-xs uppercase tracking-wider text-[#5a6478]">
              Cas sanctions/PEP
            </div>
            <div className="flex items-center gap-2 text-2xl font-semibold text-[#0f1b33]">
              <Scale size={18} /> {sanctionsCases.length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div className="text-xs uppercase tracking-wider text-[#5a6478]">
              CRITICAL
            </div>
            <div className="flex items-center gap-2 text-2xl font-semibold text-[#a23e48]">
              <AlertTriangle size={18} /> {n_critical}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div className="text-xs uppercase tracking-wider text-[#5a6478]">
              Liens PEP
            </div>
            <div className="text-2xl font-semibold text-[#c97b1f]">{n_pep}</div>
            <div className="text-xs text-[#5a6478]">{n_listed} listés sanctions</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div className="text-xs uppercase tracking-wider text-[#5a6478]">
              Exposition flagée
            </div>
            <div className="text-2xl font-semibold text-[#0f1b33]">
              {formatEur(totalExposure)}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="mb-4">
        <CardContent>
          <Input
            aria-label="Rechercher un fournisseur, une case ou un titre sanctions PEP"
            placeholder="Rechercher vendor / case / titre…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </CardContent>
      </Card>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>🚨 Cas flagués sanctions / PEP</CardTitle>
        </CardHeader>
        <div className="overflow-x-auto">
          {query.isLoading ? (
            <div className="p-4 text-sm text-[#5a6478]">Chargement…</div>
          ) : !filteredCases.length ? (
            <div className="p-4 text-sm text-[#5a6478]">
              Aucun cas sanctions/PEP. Lancer le détecteur côté Streamlit
              (page Sanctions &amp; PEP legacy) pour alimenter cette vue.
            </div>
          ) : (
            <CasesTable rows={filteredCases} />
          )}
        </div>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>📡 Sources actives</CardTitle>
        </CardHeader>
        <CardContent className="text-sm">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#e1e5ee] text-left text-xs text-[#5a6478]">
                <th className="py-2">Source</th>
                <th className="py-2">URL</th>
                <th className="py-2">Licence</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-[#e1e5ee]">
                <td className="py-2 font-medium">OpenSanctions Yente</td>
                <td className="py-2 font-mono text-xs">
                  api.opensanctions.org/match/sanctions
                </td>
                <td className="py-2 text-xs">CC-BY 4.0</td>
              </tr>
              <tr className="border-b border-[#e1e5ee]">
                <td className="py-2 font-medium">UE consolidée</td>
                <td className="py-2 font-mono text-xs">via Yente</td>
                <td className="py-2 text-xs">EU Open Data</td>
              </tr>
              <tr className="border-b border-[#e1e5ee]">
                <td className="py-2 font-medium">OFAC SDN</td>
                <td className="py-2 font-mono text-xs">via Yente</td>
                <td className="py-2 text-xs">US Public Domain</td>
              </tr>
              <tr>
                <td className="py-2 font-medium">Snapshot local CSV</td>
                <td className="py-2 font-mono text-xs">
                  data/sanctions/snapshot_*.csv
                </td>
                <td className="py-2 text-xs">fallback démo</td>
              </tr>
            </tbody>
          </table>
          <a
            href="https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/blob/main/docs/sources_de_donnees.md"
            target="_blank"
            rel="noreferrer"
            className="mt-3 inline-flex h-8 items-center gap-1 rounded-md border border-[#e1e5ee] bg-white px-3 text-xs font-medium text-[#5a6478] transition-colors hover:border-[#1f3a6e] hover:text-[#1f3a6e]"
          >
            📚 Voir docs/sources_de_donnees.md
          </a>
        </CardContent>
      </Card>
    </div>
  );
}

function CasesTable({ rows }: { rows: CaseOutV1[] }) {
  return (
    <table className="w-full text-sm">
      <thead className="bg-[#f4f6fa] text-[#5a6478]">
        <tr>
          <th className="px-3 py-2 text-left">Vendor</th>
          <th className="px-3 py-2 text-left">Titre</th>
          <th className="px-3 py-2 text-left">Sévérité</th>
          <th className="px-3 py-2 text-right">Exposition</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((c) => (
          <tr key={c.case_id} className="border-t border-[#e1e5ee]">
            <td className="px-3 py-2">
              {c.vendor_id ? (
                <a
                  href={`/vendors/${encodeURIComponent(c.vendor_id)}`}
                  className="font-mono text-xs text-[#1f3a6e] hover:underline"
                >
                  {c.vendor_id}
                </a>
              ) : (
                <span className="text-xs text-[#9aa3b2]">—</span>
              )}
            </td>
            <td className="px-3 py-2">{c.title}</td>
            <td className="px-3 py-2">
              <SeverityBadge value={c.severity} />
            </td>
            <td className="px-3 py-2 text-right">{formatEur(c.exposure_eur)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
