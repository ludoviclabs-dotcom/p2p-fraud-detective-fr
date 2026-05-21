"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { listCases } from "@/lib/api-client";
import { ForensicPage } from "@/components/forensic-page";

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
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Pilotage</div>
          <h1 style={{ marginTop: 9 }}>
            Collaboration <span className="italic">multi-user</span>
          </h1>
          <p className="sub">
            Multi-user · @mentions · SLA configurable · OIDC Microsoft Entra ID / Auth0 /
            Keycloak (Phase 4 P4-3).
          </p>
        </div>
      </div>

      <div className="mb-5 grid gap-4 md:grid-cols-3">
        <div className="fx-panel">
          <div className="fx-panel-head">
            <h2>Authentification OIDC</h2>
            <span className="glyph">□</span>
          </div>
          <div className="fx-panel-body space-y-3">
            <p style={{ fontSize: 13, lineHeight: 1.6, color: "var(--fg-2)" }}>
              Discovery + PKCE + JWKS cache 1h. Compatible Microsoft Entra ID, Auth0, Keycloak.
            </p>
            <p style={{ fontSize: 13, lineHeight: 1.6, color: "var(--fg-2)" }}>
              <strong style={{ color: "var(--fg)" }}>Proxy Next.js</strong> :{" "}
              <code
                style={{
                  background: "var(--panel-2)",
                  border: "1px solid var(--border)",
                  padding: "1px 5px",
                  fontFamily: "var(--font-mono)",
                  fontSize: 10,
                }}
              >
                /api/auth/*
              </code>{" "}
              → FastAPI{" "}
              <code
                style={{
                  background: "var(--panel-2)",
                  border: "1px solid var(--border)",
                  padding: "1px 5px",
                  fontFamily: "var(--font-mono)",
                  fontSize: 10,
                }}
              >
                /oidc/*
              </code>
            </p>
            <p className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>
              Variables d&apos;env requises côté FastAPI :{" "}
              <span style={{ color: "var(--fg-2)" }}>OIDC_ISSUER</span>,{" "}
              <span style={{ color: "var(--fg-2)" }}>OIDC_CLIENT_ID</span>,{" "}
              <span style={{ color: "var(--fg-2)" }}>OIDC_REDIRECT_URI</span>.
            </p>
          </div>
        </div>

        <div className="fx-panel">
          <div className="fx-panel-head">
            <h2>@mentions</h2>
            <span className="glyph">◷</span>
          </div>
          <div className="fx-panel-body space-y-3">
            <p style={{ fontSize: 13, lineHeight: 1.6, color: "var(--fg-2)" }}>
              Dans les commentaires de cases, les @mentions parsées automatiquement
              déclenchent une notification (Slack/Teams si configuré).
            </p>
            <p className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>
              MentionStore : SQLite/PostgreSQL, audit trail chaque mention.
            </p>
          </div>
        </div>

        <div className="fx-panel">
          <div className="fx-panel-head">
            <h2>SLA configurable</h2>
            <span className="glyph">◷</span>
          </div>
          <div className="fx-table-wrap">
            <table className="fx-table">
              <tbody>
                <tr>
                  <td className="key">Critical</td>
                  <td className="num">24 h</td>
                </tr>
                <tr>
                  <td className="key">High</td>
                  <td className="num">3 j</td>
                </tr>
                <tr>
                  <td className="key">Medium</td>
                  <td className="num">7 j</td>
                </tr>
                <tr>
                  <td className="key">Low</td>
                  <td className="num">14 j</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="fx-panel">
        <div className="fx-panel-head">
          <h2>Cas par assigné (live)</h2>
          <span className="glyph">▣</span>
        </div>
        {cases.isLoading ? (
          <div className="fx-panel-body">
            <span className="fx-mono" style={{ fontSize: 12, color: "var(--muted)" }}>
              Chargement…
            </span>
          </div>
        ) : !assignees.size ? (
          <div className="fx-panel-body">
            <span className="fx-mono" style={{ fontSize: 12, color: "var(--muted)" }}>
              Aucun case assigné. Utiliser bulk assign depuis{" "}
              <Link href="/cases" className="fx-link">
                /cases
              </Link>
              .
            </span>
          </div>
        ) : (
          <div className="fx-table-wrap">
            <table className="fx-table">
              <thead>
                <tr>
                  <th>Utilisateur</th>
                  <th className="num">Cases assignés</th>
                </tr>
              </thead>
              <tbody>
                {Array.from(assignees.entries())
                  .sort((a, b) => b[1] - a[1])
                  .map(([user, n]) => (
                    <tr key={user}>
                      <td className="key fx-mono" style={{ fontSize: 12 }}>
                        {user}
                      </td>
                      <td className="num" style={{ fontFamily: "var(--font-display)", fontSize: 20 }}>
                        {n}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </ForensicPage>
  );
}
