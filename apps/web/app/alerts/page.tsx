"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { listAudit, type AuditEntryOut } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SeverityBadge } from "@/components/ui/badge";
import { Bell, Activity } from "lucide-react";
import { formatDate } from "@/lib/utils";

// Polling 5 secondes — équivalent fonctionnel d'un SSE pour la démo
// (vrai SSE Server-Sent Events à brancher en Phase 5b quand backend
// expose /api/v1/alerts/stream).
const REFETCH_MS = 5_000;

const SEVERITY_BG: Record<string, string> = {
  critical: "border-l-4 border-l-[#a23e48]",
  high: "border-l-4 border-l-[#c97b1f]",
  medium: "border-l-4 border-l-[#e5a93a]",
  low: "border-l-4 border-l-[#3e7c5a]",
};

export default function AlertsPage() {
  const query = useQuery({
    queryKey: ["alerts-feed"],
    queryFn: () => listAudit(0, 50),
    refetchInterval: REFETCH_MS,
    refetchIntervalInBackground: false,
  });

  const events = query.data?.entries ?? [];

  // Stats sur les 50 derniers events renvoyes par l'API ou le mode demo.
  const stats = useMemo(() => {
    const byKind = new Map<string, number>();
    let critical = 0;
    for (const e of events) {
      byKind.set(e.kind, (byKind.get(e.kind) ?? 0) + 1);
      const sev = (e.payload?.severity as string) ?? "";
      if (sev === "critical") critical++;
    }
    return {
      total: events.length,
      kinds: byKind,
      critical,
      signed: events.filter((e) => e.signature).length,
    };
  }, [events]);

  return (
    <div className="px-8 py-10">
      <div className="mb-1 flex items-center justify-between">
        <div className="text-xs uppercase tracking-wider text-[#5a6478]">
          Pilotage
        </div>
        <div className="flex items-center gap-1 text-xs text-[#5a6478]">
          <span
            className={`h-2 w-2 rounded-full ${
              query.isFetching ? "bg-[#3e7c5a] animate-pulse" : "bg-[#9aa3b2]"
            }`}
          />
          {query.isFetching ? "Refresh en cours..." : `Demo/API · ${REFETCH_MS / 1000}s`}
        </div>
      </div>
      <h1 className="mb-1 text-3xl font-bold text-[#0f1b33] dark:text-white">
        Alertes &amp; monitoring
      </h1>
      <p className="mb-6 text-sm text-[#5a6478]">
        Flux d'événements depuis l'audit log. Le deploiement public peut servir
        des donnees demo; les sources live doivent etre confirmees par le statut API.
      </p>

      <div className="mb-4 grid gap-3 md:grid-cols-4">
        <Card>
          <CardContent>
            <div className="text-xs uppercase tracking-wider text-[#5a6478]">
              Total events (50 derniers)
            </div>
            <div className="flex items-center gap-2 text-2xl font-semibold text-[#0f1b33]">
              <Activity size={18} /> {stats.total}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div className="text-xs uppercase tracking-wider text-[#5a6478]">
              Critiques
            </div>
            <div className="flex items-center gap-2 text-2xl font-semibold text-[#a23e48]">
              <Bell size={18} /> {stats.critical}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div className="text-xs uppercase tracking-wider text-[#5a6478]">
              Signatures Ed25519
            </div>
            <div className="text-2xl font-semibold text-[#3e7c5a]">
              {stats.signed} / {stats.total}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div className="text-xs uppercase tracking-wider text-[#5a6478]">
              Types distincts
            </div>
            <div className="text-2xl font-semibold text-[#0f1b33]">
              {stats.kinds.size}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>📡 Configuration canaux d'alerte (statut)</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#e1e5ee] text-left text-xs text-[#5a6478]">
                <th className="py-2">Canal</th>
                <th className="py-2">Statut</th>
                <th className="py-2">Cible</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-[#e1e5ee]">
                <td className="py-2 font-medium">Slack Webhook</td>
                <td className="py-2 text-xs">
                  Configurable via{" "}
                  <code className="rounded bg-[#f4f6fa] px-1 py-0.5">
                    SLACK_WEBHOOK_URL
                  </code>
                </td>
                <td className="py-2 text-xs text-[#5a6478]">canal #fraud-alerts</td>
              </tr>
              <tr className="border-b border-[#e1e5ee]">
                <td className="py-2 font-medium">Microsoft Teams</td>
                <td className="py-2 text-xs">
                  Configurable via{" "}
                  <code className="rounded bg-[#f4f6fa] px-1 py-0.5">
                    TEAMS_WEBHOOK_URL
                  </code>
                </td>
                <td className="py-2 text-xs text-[#5a6478]">
                  Incoming Webhook connector
                </td>
              </tr>
              <tr className="border-b border-[#e1e5ee]">
                <td className="py-2 font-medium">Webhook B2B CloudEvents</td>
                <td className="py-2 text-xs">
                  HMAC-SHA256 signé via{" "}
                  <code className="rounded bg-[#f4f6fa] px-1 py-0.5">
                    WEBHOOK_URL
                  </code>
                </td>
                <td className="py-2 text-xs text-[#5a6478]">
                  SIEM/ERP/SOC (P5-3)
                </td>
              </tr>
            </tbody>
          </table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>🔔 Flux d'événements</CardTitle>
        </CardHeader>
        <div className="p-4">
          {query.isLoading ? (
            <div className="text-sm text-[#5a6478]">Connexion au flux…</div>
          ) : !events.length ? (
            <div className="text-sm text-[#5a6478]">Aucun événement.</div>
          ) : (
            <EventFeed events={events} />
          )}
        </div>
      </Card>
    </div>
  );
}

function EventFeed({ events }: { events: AuditEntryOut[] }) {
  return (
    <ul className="space-y-2">
      {events.map((e) => {
        const sev = (e.payload?.severity as string) ?? "";
        const sevClass = SEVERITY_BG[sev] ?? "border-l-4 border-l-[#9aa3b2]";
        return (
          <li
            key={e.seq}
            className={`flex items-start justify-between gap-3 rounded bg-[#f9fafc] px-3 py-2 ${sevClass}`}
          >
            <div className="flex-1">
              <div className="flex items-baseline gap-2">
                <span className="font-mono text-xs text-[#1f3a6e]">{e.kind}</span>
                {sev ? <SeverityBadge value={sev} /> : null}
              </div>
              <div className="mt-0.5 text-xs text-[#5a6478]">
                par <strong className="text-[#0f1b33]">{e.actor}</strong>
                {e.payload?.case_id ? (
                  <>
                    {" "}
                    · case{" "}
                    <span className="font-mono text-[#1f3a6e]">
                      {String(e.payload.case_id).slice(0, 16)}
                    </span>
                  </>
                ) : null}
              </div>
            </div>
            <div className="flex flex-col items-end text-xs text-[#5a6478]">
              <span>{formatDate(e.at)}</span>
              {e.signature ? (
                <span className="text-[#3e7c5a]">🔑 Ed25519</span>
              ) : null}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
