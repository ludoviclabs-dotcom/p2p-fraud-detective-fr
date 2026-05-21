"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { listAudit, type AuditEntryOut } from "@/lib/api-client";
import { Input } from "@/components/ui/input";
import { formatDate } from "@/lib/utils";
import { ForensicPage } from "@/components/forensic-page";

const KIND_TONE: Record<string, string> = {
  "case.created": "info",
  "case.assigned": "info",
  "case.commented": "",
  "case.escalated": "warn",
  "case.closed": "ok",
  "case.status_changed": "warn",
  "file.imported": "risk",
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
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Données</div>
          <h1 style={{ marginTop: 9 }}>
            Référentiel — <span className="italic">historique</span>
          </h1>
          <p className="sub">
            Timeline événementielle des mutations sur le référentiel fournisseurs
            et les cases. Source : audit log SHA-256 chaîné (P3 + P5-5
            Ed25519).
          </p>
        </div>
      </div>

      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <h2>Recherche</h2>
        </div>
        <div className="fx-panel-body">
          <Input
            aria-label="Rechercher dans actor, kind ou payload"
            placeholder="Rechercher dans actor/kind/payload…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="fx-panel">
        <div className="fx-panel-head">
          <div>
            <h2>Timeline</h2>
            <div className="sub">{entries.length} événements</div>
          </div>
          <span className="glyph">◷</span>
        </div>
        <div className="fx-panel-body">
          {query.isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((k) => (
                <div key={k} className="fx-skel" style={{ height: 64 }} />
              ))}
            </div>
          ) : !entries.length ? (
            <div className="fx-notice">
              <span className="glyph">⚠</span>
              <div>
                <div className="nt">Aucun événement</div>
                <p className="nb">Aucun événement à afficher.</p>
              </div>
            </div>
          ) : (
            <Timeline entries={entries} />
          )}
        </div>
      </div>
    </ForensicPage>
  );
}

function Timeline({ entries }: { entries: AuditEntryOut[] }) {
  return (
    <div
      style={{
        borderLeft: "1px solid var(--border)",
        paddingLeft: 20,
        marginLeft: 8,
      }}
    >
      {entries.map((e) => {
        const tone = KIND_TONE[e.kind] ?? "";
        const dotColor =
          tone === "risk"
            ? "var(--risk)"
            : tone === "warn"
              ? "var(--warn)"
              : tone === "ok"
                ? "var(--verified)"
                : tone === "info"
                  ? "var(--info)"
                  : "var(--dim)";
        return (
          <div
            key={e.seq}
            style={{
              position: "relative",
              marginBottom: 20,
              paddingTop: 2,
            }}
          >
            {/* timeline dot */}
            <span
              style={{
                position: "absolute",
                left: -26,
                top: 4,
                width: 10,
                height: 10,
                background: dotColor,
                border: "1px solid var(--bg)",
                display: "inline-block",
              }}
            />
            <div
              style={{
                display: "flex",
                alignItems: "baseline",
                justifyContent: "space-between",
                gap: 8,
              }}
            >
              <span
                className="fx-mono"
                style={{ fontSize: 10, color: "var(--muted)" }}
              >
                {formatDate(e.at)} · #{e.seq}
              </span>
              {e.signature ? (
                <span
                  className="fx-mono"
                  style={{ fontSize: 10, color: "var(--verified)" }}
                >
                  ✓ Ed25519
                </span>
              ) : null}
            </div>
            <div
              className="fx-mono"
              style={{ fontSize: 11, color: dotColor, marginTop: 2 }}
            >
              {e.kind}
            </div>
            <div style={{ fontSize: 13, color: "var(--fg-2)", marginTop: 2 }}>
              <span style={{ color: "var(--muted)" }}>par</span>{" "}
              <span style={{ color: "var(--fg)" }}>{e.actor}</span>
              {e.payload?.case_id ? (
                <>
                  {" "}
                  <span style={{ color: "var(--muted)" }}>— case</span>{" "}
                  <span
                    className="fx-mono"
                    style={{ fontSize: 11, color: "var(--info)" }}
                  >
                    {String(e.payload.case_id).slice(0, 16)}
                  </span>
                </>
              ) : null}
            </div>
            {Object.keys(e.payload).length > 0 ? (
              <details style={{ marginTop: 4 }}>
                <summary
                  className="fx-mono"
                  style={{
                    cursor: "pointer",
                    fontSize: 10,
                    color: "var(--muted)",
                    letterSpacing: "0.06em",
                  }}
                >
                  payload
                </summary>
                <pre
                  style={{
                    marginTop: 6,
                    overflowX: "auto",
                    background: "var(--panel-2)",
                    border: "1px solid var(--border)",
                    padding: "8px 12px",
                    fontFamily: "var(--font-mono)",
                    fontSize: 10,
                    color: "var(--fg-2)",
                    lineHeight: 1.6,
                  }}
                >
                  {JSON.stringify(e.payload, null, 2)}
                </pre>
              </details>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
