"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import Link from "next/link";
import { listFindings, type FindingOut } from "@/lib/api-client";
import { Input } from "@/components/ui/input";
import { SeverityBadge } from "@/components/ui/badge";
import { formatDate, formatEur } from "@/lib/utils";
import { ForensicPage } from "@/components/forensic-page";

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
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Détection</div>
          <h1 style={{ marginTop: 9 }}>
            Findings
          </h1>
          <p className="sub">
            Vue paginée des findings agrégés depuis les cases. Filtres rule_id / severity +
            recherche signal/vendor.
          </p>
        </div>
      </div>

      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <h2>Filtres</h2>
          <span className="glyph">◇</span>
        </div>
        <div className="fx-panel-body">
          <div className="grid gap-3 md:grid-cols-3">
            <div>
              <label
                htmlFor="findings-severity-filter"
                className="fx-eyebrow"
                style={{ display: "block", marginBottom: 6 }}
              >
                Sévérité
              </label>
              <select
                id="findings-severity-filter"
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
                style={{
                  height: 38,
                  width: "100%",
                  background: "var(--bg)",
                  border: "1px solid var(--border)",
                  padding: "0 12px",
                  fontFamily: "var(--font-mono)",
                  fontSize: 12,
                  color: "var(--fg)",
                  outline: "none",
                }}
              >
                <option value="">Toutes</option>
                <option value="critical">CRITICAL</option>
                <option value="high">HIGH</option>
                <option value="medium">MEDIUM</option>
                <option value="low">LOW</option>
              </select>
            </div>
            <div>
              <label
                htmlFor="findings-rule-filter"
                className="fx-eyebrow"
                style={{ display: "block", marginBottom: 6 }}
              >
                Rule ID
              </label>
              <Input
                id="findings-rule-filter"
                placeholder="ex. SANCTION_MATCH"
                value={ruleId}
                onChange={(e) => setRuleId(e.target.value)}
              />
            </div>
            <div>
              <label
                htmlFor="findings-free-search"
                className="fx-eyebrow"
                style={{ display: "block", marginBottom: 6 }}
              >
                Recherche libre
              </label>
              <Input
                id="findings-free-search"
                placeholder="signal, invoice_id, vendor_id"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="fx-panel">
        <div className="fx-table-wrap">
          {query.isLoading ? (
            <div className="fx-panel-body">
              <div className="fx-skel" style={{ height: 200 }} />
            </div>
          ) : query.error ? (
            <div className="fx-panel-body">
              <div className="fx-notice">
                <span className="glyph">⚠</span>
                <div>
                  <div className="nt">API indisponible</div>
                  <p className="nb">{(query.error as Error).message}</p>
                </div>
              </div>
            </div>
          ) : (
            <FindingsTable rows={rows} />
          )}
        </div>
        <div
          className="fx-panel-body"
          style={{ borderTop: "1px solid var(--border)" }}
        >
          <span className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>
            {rows.length} finding(s) affichés
          </span>
        </div>
      </div>
    </ForensicPage>
  );
}

function FindingsTable({ rows }: { rows: FindingOut[] }) {
  if (!rows.length) {
    return (
      <div className="fx-panel-body">
        <span className="fx-mono" style={{ fontSize: 12, color: "var(--muted)" }}>
          Aucun finding.
        </span>
      </div>
    );
  }
  return (
    <table className="fx-table">
      <thead>
        <tr>
          <th>Invoice ID</th>
          <th>Rule</th>
          <th>Sévérité</th>
          <th>Signal</th>
          <th>Vendor</th>
          <th className="num">Exposition</th>
          <th>Détecté</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((f) => {
          const vendorId = f.evidence?.vendor_id as string | undefined;
          const exposure = f.evidence?.exposure_eur as number | undefined;
          return (
            <tr key={`${f.invoice_id}-${f.rule_id}`}>
              <td className="key">{f.invoice_id}</td>
              <td className="key">{f.rule_id}</td>
              <td>
                <SeverityBadge value={f.severity} />
              </td>
              <td>{f.signal}</td>
              <td>
                {vendorId ? (
                  <Link
                    href={`/vendors/${encodeURIComponent(vendorId)}`}
                    className="fx-link"
                  >
                    {vendorId}
                  </Link>
                ) : (
                  <span style={{ color: "var(--dim)" }}>—</span>
                )}
              </td>
              <td className="num">{formatEur(exposure)}</td>
              <td>
                <span className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>
                  {formatDate(f.detected_at)}
                </span>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
