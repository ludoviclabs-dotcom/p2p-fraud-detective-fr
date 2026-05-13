"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { listAudit, type AuditEntryOut } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { formatDate } from "@/lib/utils";

const KIND_COLORS: Record<string, string> = {
  "case.created": "#1f3a6e",
  "case.assigned": "#3e7cb1",
  "case.commented": "#5a6478",
  "case.escalated": "#c97b1f",
  "case.closed": "#3e7c5a",
  "case.status_changed": "#e5a93a",
  "file.imported": "#a23e48",
};

export default function MasterHistoryPage() {
  const [search, setSearch] = useState("");

  // Pulls all audit log entries (first 500) — proxy pour master data events
  // tant qu'il n'y a pas d'endpoint dédié /api/v1/master-events.
  const query = useQuery({
    queryKey: ["master-history"],
    queryFn: () => listAudit(0, 500),
  });

  const entries = useMemo(() => {
    const all = query.data?.entries ?? [];
    if (!search) return all;
    const q = search.toLowerCase();
    return all.filter(
      (e) =>
        e.actor.toLowerCase().includes(q) ||
        e.kind.toLowerCase().includes(q) ||
        JSON.stringify(e.payload).toLowerCase().includes(q),
    );
  }, [query.data, search]);

  return (
    <div className="px-8 py-10">
      <div className="mb-1 text-xs uppercase tracking-wider text-[#5a6478]">
        Données
      </div>
      <h1 className="mb-1 text-3xl font-bold text-[#0f1b33] dark:text-white">
        Référentiel — historique
      </h1>
      <p className="mb-6 text-sm text-[#5a6478]">
        Timeline événementielle des mutations sur le référentiel fournisseurs
        et les cases. Source : audit log SHA-256 chaîné (P3 + P5-5 Ed25519).
      </p>

      <Card className="mb-4">
        <CardContent>
          <Input
            placeholder="Rechercher dans actor/kind/payload…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>
            🕓 Timeline {entries.length} événements
          </CardTitle>
        </CardHeader>
        <div className="p-4">
          {query.isLoading ? (
            <div className="text-sm text-[#5a6478]">Chargement…</div>
          ) : !entries.length ? (
            <div className="text-sm text-[#5a6478]">
              Aucun événement à afficher.
            </div>
          ) : (
            <Timeline entries={entries} />
          )}
        </div>
      </Card>
    </div>
  );
}

function Timeline({ entries }: { entries: AuditEntryOut[] }) {
  return (
    <ol className="relative ml-4 border-l-2 border-[#e1e5ee] pl-6">
      {entries.map((e) => (
        <li key={e.seq} className="mb-5 last:mb-0">
          <span
            className="absolute -left-[7px] mt-1 inline-block h-3 w-3 rounded-full border-2 border-white"
            style={{ background: KIND_COLORS[e.kind] ?? "#9aa3b2" }}
          />
          <div className="flex items-baseline justify-between gap-2">
            <span className="font-mono text-xs text-[#5a6478]">
              {formatDate(e.at)} · #{e.seq}
            </span>
            {e.signature ? (
              <span className="text-[10px] text-[#3e7c5a]">🔑 Ed25519</span>
            ) : null}
          </div>
          <div className="mt-0.5 font-mono text-xs text-[#1f3a6e]">{e.kind}</div>
          <div className="mt-0.5 text-sm">
            <span className="text-[#5a6478]">par</span>{" "}
            <span className="font-medium text-[#0f1b33]">{e.actor}</span>
            {e.payload?.case_id ? (
              <>
                {" "}
                <span className="text-[#5a6478]">— case</span>{" "}
                <span className="font-mono text-xs text-[#1f3a6e]">
                  {String(e.payload.case_id).slice(0, 16)}
                </span>
              </>
            ) : null}
          </div>
          {Object.keys(e.payload).length > 0 ? (
            <details className="mt-1">
              <summary className="cursor-pointer text-xs text-[#5a6478]">
                payload
              </summary>
              <pre className="mt-1 overflow-x-auto rounded bg-[#f4f6fa] p-2 text-[10px]">
                {JSON.stringify(e.payload, null, 2)}
              </pre>
            </details>
          ) : null}
        </li>
      ))}
    </ol>
  );
}
