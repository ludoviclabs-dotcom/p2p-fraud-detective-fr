"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { listCases } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { SeverityBadge } from "@/components/ui/badge";
import { formatEur } from "@/lib/utils";

type VendorRow = {
  vendor_id: string;
  total_exposure: number;
  n_cases: number;
  max_severity: string;
};

const SEVERITY_RANK: Record<string, number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1,
};

export default function VendorsIndexPage() {
  const [search, setSearch] = useState("");

  const cases = useQuery({
    queryKey: ["all-cases"],
    queryFn: () => listCases({ limit: 1000 }),
  });

  const vendors = useMemo<VendorRow[]>(() => {
    const acc = new Map<string, VendorRow>();
    for (const c of cases.data ?? []) {
      if (!c.vendor_id) continue;
      const row = acc.get(c.vendor_id) ?? {
        vendor_id: c.vendor_id,
        total_exposure: 0,
        n_cases: 0,
        max_severity: "low",
      };
      row.total_exposure += c.exposure_eur ?? 0;
      row.n_cases += 1;
      if ((SEVERITY_RANK[c.severity] ?? 0) > (SEVERITY_RANK[row.max_severity] ?? 0)) {
        row.max_severity = c.severity;
      }
      acc.set(c.vendor_id, row);
    }
    let rows = Array.from(acc.values()).sort(
      (a, b) => b.total_exposure - a.total_exposure,
    );
    if (search) {
      const q = search.toLowerCase();
      rows = rows.filter((r) => r.vendor_id.toLowerCase().includes(q));
    }
    return rows;
  }, [cases.data, search]);

  return (
    <div className="px-8 py-10">
      <div className="mb-1 text-xs uppercase tracking-wider text-[#5a6478]">
        Investigation
      </div>
      <h1 className="mb-1 text-3xl font-bold text-[#0f1b33] dark:text-white">
        Fournisseurs (index)
      </h1>
      <p className="mb-6 text-sm text-[#5a6478]">
        Vue agrégée par vendor_id. Cliquer pour ouvrir la fiche 360°.
      </p>

      <Card className="mb-4">
        <CardContent>
          <Input
            placeholder="Rechercher un vendor_id…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{vendors.length} fournisseur(s)</CardTitle>
        </CardHeader>
        <div className="overflow-x-auto">
          {cases.isLoading ? (
            <div className="p-4 text-sm text-[#5a6478]">Chargement…</div>
          ) : !vendors.length ? (
            <div className="p-4 text-sm text-[#5a6478]">
              Aucun vendor à afficher.
            </div>
          ) : (
            <VendorsTable rows={vendors} />
          )}
        </div>
      </Card>
    </div>
  );
}

function VendorsTable({ rows }: { rows: VendorRow[] }) {
  return (
    <table className="w-full text-sm">
      <thead className="bg-[#f4f6fa] text-[#5a6478]">
        <tr>
          <th className="px-3 py-2 text-left">Vendor ID</th>
          <th className="px-3 py-2 text-right">Exposition</th>
          <th className="px-3 py-2 text-right">Cases</th>
          <th className="px-3 py-2 text-left">Sévérité max</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.vendor_id} className="border-t border-[#e1e5ee]">
            <td className="px-3 py-2">
              <a
                href={`/vendors/${encodeURIComponent(row.vendor_id)}`}
                className="font-mono text-xs text-[#1f3a6e] hover:underline"
              >
                {row.vendor_id}
              </a>
            </td>
            <td className="px-3 py-2 text-right">{formatEur(row.total_exposure)}</td>
            <td className="px-3 py-2 text-right">{row.n_cases}</td>
            <td className="px-3 py-2">
              <SeverityBadge value={row.max_severity} />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
