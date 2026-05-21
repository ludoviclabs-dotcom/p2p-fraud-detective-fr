"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import {
  CASE_WORKFLOW_STORAGE_KEY,
  exportCaseWorkflowCsv,
  getCaseDecisionLabel,
  getCaseStatusLabel,
  readStoredCaseWorkflowRecords,
  type CaseWorkflowContext,
  type CaseWorkflowRecord,
} from "@/lib/case-workflow";
import { SeverityBadge } from "@/components/ui/badge";
import { formatEuro } from "@/lib/p2p-demo-format";
import { getSignalLabel } from "@/lib/p2p-demo-taxonomy";

function downloadText(filename: string, content: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}

export function CaseWorkflowExport({
  suggestedCases,
}: {
  suggestedCases: CaseWorkflowContext[];
}) {
  const [records, setRecords] = useState<CaseWorkflowRecord[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [decisionFilter, setDecisionFilter] = useState("all");

  const refresh = () => setRecords(readStoredCaseWorkflowRecords());

  useEffect(() => {
    refresh();
    window.addEventListener("p2p-case-workflow-updated", refresh);
    window.addEventListener("storage", refresh);
    return () => {
      window.removeEventListener("p2p-case-workflow-updated", refresh);
      window.removeEventListener("storage", refresh);
    };
  }, []);

  const filteredRecords = useMemo(() => {
    const needle = search.trim().toLowerCase();

    return records.filter((record) => {
      const matchesSearch =
        !needle ||
        record.invoiceId.toLowerCase().includes(needle) ||
        record.vendorId.toLowerCase().includes(needle) ||
        record.vendorName.toLowerCase().includes(needle) ||
        record.assignee.toLowerCase().includes(needle) ||
        record.note.toLowerCase().includes(needle);
      const matchesStatus = statusFilter === "all" || record.status === statusFilter;
      const matchesDecision =
        decisionFilter === "all" || record.decision === decisionFilter;

      return matchesSearch && matchesStatus && matchesDecision;
    });
  }, [decisionFilter, records, search, statusFilter]);

  const qualifiedIds = useMemo(
    () => new Set(records.map((record) => record.id)),
    [records],
  );

  const metrics = useMemo(() => {
    const exposure = filteredRecords.reduce(
      (sum, record) => sum + record.exposureEur,
      0,
    );
    const escalated = filteredRecords.filter(
      (record) => record.status === "escalated",
    ).length;
    const cleared = filteredRecords.filter(
      (record) => record.status === "cleared",
    ).length;
    return { exposure, escalated, cleared };
  }, [filteredRecords]);

  const exportCsv = () => {
    downloadText(
      `p2p_case_workflow_${new Date().toISOString().slice(0, 10)}.csv`,
      exportCaseWorkflowCsv(filteredRecords),
      "text/csv;charset=utf-8",
    );
  };

  const exportJson = () => {
    downloadText(
      `p2p_case_workflow_${new Date().toISOString().slice(0, 10)}.json`,
      JSON.stringify(filteredRecords, null, 2),
      "application/json;charset=utf-8",
    );
  };

  const resetDemo = () => {
    if (!window.confirm("Vider le registre local de qualification audit ?")) return;
    window.localStorage.removeItem(CASE_WORKFLOW_STORAGE_KEY);
    setRecords([]);
    window.dispatchEvent(new Event("p2p-case-workflow-updated"));
  };

  const selectStyle: React.CSSProperties = {
    height: 36,
    background: "var(--bg)",
    border: "1px solid var(--border)",
    padding: "0 10px",
    fontFamily: "var(--font-mono)",
    fontSize: 11,
    color: "var(--fg)",
    outline: "none",
  };

  return (
    <div className="space-y-5">
      {/* KPI strip */}
      <section className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Cas affiches" value={String(filteredRecords.length)} />
        <MetricCard label="Escalades" value={String(metrics.escalated)} />
        <MetricCard label="Clotures" value={String(metrics.cleared)} />
        <MetricCard label="Exposition" value={formatEuro(metrics.exposure)} />
      </section>

      {/* Workflow registry */}
      <div className="fx-panel">
        <div className="fx-panel-head">
          <div>
            <h2>Registre workflow</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={refresh} className="fx-btn-ghost sm">
              ↻ Actualiser
            </button>
            <button
              type="button"
              disabled={!filteredRecords.length}
              onClick={exportJson}
              className="fx-btn-ghost sm"
            >
              JSON
            </button>
            <button
              type="button"
              disabled={!filteredRecords.length}
              onClick={exportCsv}
              className="fx-btn sm"
            >
              ↓ CSV audit
            </button>
            <button
              type="button"
              disabled={!records.length}
              onClick={resetDemo}
              className="fx-btn-ghost sm"
              style={{ color: "var(--risk)", borderColor: "var(--risk-dim)" }}
            >
              ✕ Reset demo
            </button>
          </div>
        </div>

        {records.length ? (
          <div>
            {/* Filters */}
            <div
              className="grid gap-3 md:grid-cols-[minmax(0,1fr)_180px_220px]"
              style={{
                padding: "14px 20px",
                borderBottom: "1px solid var(--border)",
              }}
            >
              <input
                aria-label="Filtrer les cases exportables"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Filtrer invoice, fournisseur, responsable, note..."
                className="fx-input"
              />
              <select
                aria-label="Filtrer par statut de case"
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
                style={selectStyle}
              >
                <option value="all">Tous statuts</option>
                <option value="new">Nouveau</option>
                <option value="reviewing">En revue</option>
                <option value="needs_evidence">Piece requise</option>
                <option value="escalated">Escalade</option>
                <option value="cleared">Cloture</option>
              </select>
              <select
                aria-label="Filtrer par decision"
                value={decisionFilter}
                onChange={(event) => setDecisionFilter(event.target.value)}
                style={selectStyle}
              >
                <option value="all">Toutes decisions</option>
                <option value="pending">Decision en attente</option>
                <option value="monitor">Surveiller</option>
                <option value="request_documents">Demander des pieces</option>
                <option value="block_payment">Bloquer paiement</option>
                <option value="close_false_positive">Clore faux positif</option>
              </select>
            </div>

            {filteredRecords.length ? (
              <div className="fx-table-wrap">
                <table className="fx-table">
                  <thead>
                    <tr>
                      <th>Invoice</th>
                      <th>Fournisseur</th>
                      <th>Statut</th>
                      <th>Decision</th>
                      <th>Responsable</th>
                      <th>Source</th>
                      <th className="num">Exposition</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredRecords.map((record) => (
                      <tr key={record.id}>
                        <td className="key">
                          <Link href={`/score/${record.invoiceId}`} className="fx-link">
                            {record.invoiceId}
                          </Link>
                          <div style={{ marginTop: 4 }}>
                            <SeverityBadge value={record.severity} />
                          </div>
                        </td>
                        <td>
                          <Link
                            href={`/vendors/${record.vendorId}`}
                            className="fx-link"
                          >
                            {record.vendorName}
                          </Link>
                          <div
                            className="fx-mono"
                            style={{ marginTop: 3, fontSize: 10, color: "var(--muted)" }}
                          >
                            {getSignalLabel(record.signal)}
                          </div>
                        </td>
                        <td>{getCaseStatusLabel(record.status)}</td>
                        <td>{getCaseDecisionLabel(record.decision)}</td>
                        <td style={{ color: "var(--muted)" }}>
                          {record.assignee || "—"}
                        </td>
                        <td
                          className="fx-mono"
                          style={{ fontSize: 10, color: "var(--muted)" }}
                        >
                          {record.backendCaseId ? `FastAPI ${record.backendCaseId}` : "Local"}
                        </td>
                        <td className="num">{formatEuro(record.exposureEur)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="fx-panel-body">
                <span className="fx-mono" style={{ fontSize: 12, color: "var(--muted)" }}>
                  Aucun cas ne correspond aux filtres.
                </span>
              </div>
            )}
          </div>
        ) : (
          <div className="fx-panel-body space-y-3">
            <div
              className="fx-mono"
              style={{ fontSize: 13, color: "var(--fg)", display: "flex", alignItems: "center", gap: 8 }}
            >
              <span style={{ color: "var(--muted)" }}>◫</span>
              Aucun cas qualifie dans ce navigateur.
            </div>
            <p className="fx-mono" style={{ fontSize: 11, color: "var(--muted)", lineHeight: 1.65 }}>
              Ouvrir une fiche score ou fournisseur, renseigner la qualification audit,
              puis revenir ici pour exporter le registre.
            </p>
          </div>
        )}
      </div>

      {/* Priority cases to qualify */}
      <div className="fx-panel">
        <div className="fx-panel-head">
          <h2>Cas prioritaires a qualifier</h2>
          <span className="glyph">▲</span>
        </div>
        <div className="fx-table-wrap">
          <table className="fx-table">
            <thead>
              <tr>
                <th>Invoice</th>
                <th>Signal</th>
                <th>Severite</th>
                <th className="num">Score</th>
                <th className="num">Action</th>
              </tr>
            </thead>
            <tbody>
              {suggestedCases.slice(0, 20).map((item) => (
                <tr key={item.id}>
                  <td className="key">
                    <Link href={`/score/${item.invoiceId}`} className="fx-link">
                      {item.invoiceId}
                    </Link>
                    <div
                      className="fx-mono"
                      style={{ marginTop: 3, fontSize: 10, color: "var(--muted)" }}
                    >
                      {item.vendorName}
                    </div>
                  </td>
                  <td>{getSignalLabel(item.signal)}</td>
                  <td>
                    <SeverityBadge value={item.severity} />
                  </td>
                  <td className="num">{item.riskScore}/100</td>
                  <td className="num">
                    <Link href={`/score/${item.invoiceId}`} className="fx-link">
                      {qualifiedIds.has(item.id) ? "Revoir →" : "Qualifier →"}
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="fx-stat info">
      <div className="lbl">{label}</div>
      <div className="val">{value}</div>
    </div>
  );
}
