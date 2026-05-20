"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { listFindings, type FindingOut } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { SeverityBadge } from "@/components/ui/badge";
import { formatDate, formatEur } from "@/lib/utils";

export default function FindingsPage() {
  const [severity, setSeverity] = useState("");
  const [ruleId, setRuleId] = useState("");
  const [search, setSearch] = useState("");

  const query = useQuery({
    queryKey: ["findings", severity, ruleId],
    queryFn: () =>
      listFindings({
        severity: severity || undefined,
        rule_id: ruleId || undefined,
        limit: 500,
      }),
  });

  const rows = useMemo(() => {
    const all = query.data ?? [];
    if (!search) return all;
    const q = search.toLowerCase();
    return all.filter(
      (f) =>
        f.signal.toLowerCase().includes(q) ||
        f.invoice_id.toLowerCase().includes(q) ||
        (f.evidence?.vendor_id as string | undefined)
          ?.toLowerCase()
          .includes(q),
    );
  }, [query.data, search]);

  return (
    <div className="px-8 py-10">
      <div className="mb-1 text-xs uppercase tracking-wider text-[#5a6478]">
        Détection
      </div>
      <h1 className="mb-1 text-3xl font-bold text-[#0f1b33] dark:text-white">
        Findings
      </h1>
      <p className="mb-6 text-sm text-[#5a6478]">
        Vue paginée des findings agrégés depuis les cases. Filtres rule_id /
        severity + recherche signal/vendor.
      </p>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>Filtres</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-3">
          <div>
            <label htmlFor="findings-severity-filter" className="mb-1 block text-xs text-[#5a6478]">Sévérité</label>
            <select
              id="findings-severity-filter"
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              className="h-10 w-full rounded-md border border-[#e1e5ee] bg-white px-3 text-sm"
            >
              <option value="">Toutes</option>
              <option value="critical">CRITICAL</option>
              <option value="high">HIGH</option>
              <option value="medium">MEDIUM</option>
              <option value="low">LOW</option>
            </select>
          </div>
          <div>
            <label htmlFor="findings-rule-filter" className="mb-1 block text-xs text-[#5a6478]">Rule ID</label>
            <Input
              id="findings-rule-filter"
              placeholder="ex. SANCTION_MATCH"
              value={ruleId}
              onChange={(e) => setRuleId(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="findings-free-search" className="mb-1 block text-xs text-[#5a6478]">
              Recherche libre
            </label>
            <Input
              id="findings-free-search"
              placeholder="signal, invoice_id, vendor_id"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <div className="overflow-x-auto">
          {query.isLoading ? (
            <div className="p-4 text-sm text-[#5a6478]">Chargement…</div>
          ) : query.error ? (
            <div className="p-4 text-sm text-[#a23e48]">
              API indisponible : {(query.error as Error).message}
            </div>
          ) : (
            <FindingsTable rows={rows} />
          )}
        </div>
        <CardContent className="text-xs text-[#5a6478]">
          {rows.length} finding(s) affichés
        </CardContent>
      </Card>
    </div>
  );
}

function FindingsTable({ rows }: { rows: FindingOut[] }) {
  if (!rows.length) {
    return <div className="p-4 text-sm text-[#5a6478]">Aucun finding.</div>;
  }
  return (
    <table className="w-full text-sm">
      <thead className="bg-[#f4f6fa] text-[#5a6478]">
        <tr>
          <th className="px-3 py-2 text-left">Invoice ID</th>
          <th className="px-3 py-2 text-left">Rule</th>
          <th className="px-3 py-2 text-left">Sévérité</th>
          <th className="px-3 py-2 text-left">Signal</th>
          <th className="px-3 py-2 text-left">Vendor</th>
          <th className="px-3 py-2 text-right">Exposition</th>
          <th className="px-3 py-2 text-left">Détecté</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((f) => {
          const vendorId = f.evidence?.vendor_id as string | undefined;
          const exposure = f.evidence?.exposure_eur as number | undefined;
          return (
            <tr
              key={`${f.invoice_id}-${f.rule_id}`}
              className="border-t border-[#e1e5ee] hover:bg-[#f9fafc]"
            >
              <td className="px-3 py-2 font-mono text-xs">{f.invoice_id}</td>
              <td className="px-3 py-2 font-mono text-xs">{f.rule_id}</td>
              <td className="px-3 py-2">
                <SeverityBadge value={f.severity} />
              </td>
              <td className="px-3 py-2">{f.signal}</td>
              <td className="px-3 py-2">
                {vendorId ? (
                  <a
                    href={`/vendors/${encodeURIComponent(vendorId)}`}
                    className="font-mono text-xs text-[#1f3a6e] hover:underline"
                  >
                    {vendorId}
                  </a>
                ) : (
                  <span className="text-xs text-[#9aa3b2]">—</span>
                )}
              </td>
              <td className="px-3 py-2 text-right">{formatEur(exposure)}</td>
              <td className="px-3 py-2 text-xs text-[#5a6478]">
                {formatDate(f.detected_at)}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
