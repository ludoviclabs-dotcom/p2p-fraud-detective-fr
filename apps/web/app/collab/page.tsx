"use client";

import { useQuery } from "@tanstack/react-query";
import { listCases } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, AtSign, Lock } from "lucide-react";

export default function CollabPage() {
  const cases = useQuery({
    queryKey: ["collab-cases"],
    queryFn: () => listCases({ limit: 200 }),
  });

  const assignees = new Map<string, number>();
  for (const c of cases.data ?? []) {
    if (c.assignee) {
      assignees.set(c.assignee, (assignees.get(c.assignee) ?? 0) + 1);
    }
  }

  return (
    <div className="px-8 py-10">
      <div className="mb-1 text-xs uppercase tracking-wider text-[#5a6478]">
        Pilotage
      </div>
      <h1 className="mb-1 text-3xl font-bold text-[#0f1b33] dark:text-white">
        Collaboration multi-user
      </h1>
      <p className="mb-6 text-sm text-[#5a6478]">
        Multi-user · @mentions · SLA configurable · OIDC Microsoft Entra ID /
        Auth0 / Keycloak (Phase 4 P4-3).
      </p>

      <div className="mb-4 grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Lock size={16} /> Authentification OIDC
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>
              Discovery + PKCE + JWKS cache 1h. Compatible Microsoft Entra ID,
              Auth0, Keycloak.
            </p>
            <p>
              <strong>Proxy Next.js</strong> :{" "}
              <code className="rounded bg-[#f4f6fa] px-1 py-0.5 text-xs">
                /api/auth/*
              </code>{" "}
              → FastAPI{" "}
              <code className="rounded bg-[#f4f6fa] px-1 py-0.5 text-xs">
                /oidc/*
              </code>
            </p>
            <p className="text-xs text-[#5a6478]">
              Variables d'env requises côté FastAPI :{" "}
              <code>OIDC_ISSUER</code>, <code>OIDC_CLIENT_ID</code>,{" "}
              <code>OIDC_REDIRECT_URI</code>.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <AtSign size={16} /> @mentions
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>
              Dans les commentaires de cases, les @mentions parsées
              automatiquement déclenchent une notification (Slack/Teams si
              configuré).
            </p>
            <p className="text-xs text-[#5a6478]">
              MentionStore : SQLite/PostgreSQL, audit trail chaque mention.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Users size={16} /> SLA configurable
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <table className="w-full text-xs">
              <tbody>
                <tr className="border-b border-[#e1e5ee]">
                  <td className="py-1 font-medium">Critical</td>
                  <td className="py-1 text-right">24 h</td>
                </tr>
                <tr className="border-b border-[#e1e5ee]">
                  <td className="py-1 font-medium">High</td>
                  <td className="py-1 text-right">3 j</td>
                </tr>
                <tr className="border-b border-[#e1e5ee]">
                  <td className="py-1 font-medium">Medium</td>
                  <td className="py-1 text-right">7 j</td>
                </tr>
                <tr>
                  <td className="py-1 font-medium">Low</td>
                  <td className="py-1 text-right">14 j</td>
                </tr>
              </tbody>
            </table>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>👥 Cas par assigné</CardTitle>
        </CardHeader>
        <CardContent>
          {cases.isLoading ? (
            <div className="text-sm text-[#5a6478]">Chargement…</div>
          ) : !assignees.size ? (
            <div className="text-sm text-[#5a6478]">
              Aucun case assigné. Utiliser bulk assign depuis{" "}
              <a className="text-[#1f3a6e] hover:underline" href="/cases">
                /cases
              </a>
              .
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#e1e5ee] text-left text-xs text-[#5a6478]">
                  <th className="py-2">Utilisateur</th>
                  <th className="py-2 text-right">Cases assignés</th>
                </tr>
              </thead>
              <tbody>
                {Array.from(assignees.entries())
                  .sort((a, b) => b[1] - a[1])
                  .map(([user, n]) => (
                    <tr key={user} className="border-b border-[#e1e5ee]">
                      <td className="py-2 font-mono text-xs">{user}</td>
                      <td className="py-2 text-right font-semibold">{n}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
