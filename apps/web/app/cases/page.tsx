"use client";

import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import {
  bulkAssignCases,
  bulkCloseCases,
  listCases,
  type CaseOutV1,
} from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SeverityBadge } from "@/components/ui/badge";
import { formatEur, formatDate } from "@/lib/utils";
import { ForensicPage } from "@/components/forensic-page";
import { RISK_SCENARIOS } from "@/data/risk-scenarios";
import { case360Href } from "@/lib/risk/case-links";

const STATUS_LABELS: Record<string, string> = {
  new: "Nouveau",
  triaged: "Trié",
  in_progress: "En cours",
  investigating: "En cours",
  escalated: "Escaladé",
  closed_confirmed: "Clos — confirmé",
  closed_rejected: "Clos — rejeté",
  closed_false_positive: "Clos — faux positif",
};

export default function CasesPage() {
  const qc = useQueryClient();
  const [severityFilter, setSeverityFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [bulkAssignee, setBulkAssignee] = useState("");
  const [bulkReason, setBulkReason] = useState("");

  const casesQuery = useQuery({
    queryKey: ["cases", severityFilter, statusFilter],
    queryFn: () =>
      listCases({
        severity: severityFilter || undefined,
        status: statusFilter || undefined,
        limit: 500,
      }),
  });

  const assignMutation = useMutation({
    mutationFn: (assignee: string) =>
      bulkAssignCases({
        case_ids: Array.from(selected),
        assignee,
        actor: "ui-user",
      }),
    onSuccess: () => {
      setSelected(new Set());
      qc.invalidateQueries({ queryKey: ["cases"] });
    },
  });

  const closeMutation = useMutation({
    mutationFn: (reason: string) =>
      bulkCloseCases({
        case_ids: Array.from(selected),
        status: "false_positive",
        reason,
        actor: "ui-user",
      }),
    onSuccess: () => {
      setSelected(new Set());
      setBulkReason("");
      qc.invalidateQueries({ queryKey: ["cases"] });
    },
  });

  const rows = useMemo(
    () =>
      (casesQuery.data ?? []).slice().sort((a, b) => {
        const ea = a.exposure_eur ?? 0;
        const eb = b.exposure_eur ?? 0;
        return eb - ea;
      }),
    [casesQuery.data],
  );

  const toggle = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    setSelected((prev) =>
      prev.size === rows.length ? new Set() : new Set(rows.map((r) => r.case_id)),
    );
  };

  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Pilotage</div>
          <h1 style={{ marginTop: 9 }}>
            File d&apos;<span className="italic">investigation</span>
          </h1>
          <p className="sub">
            Case management + audit log immutable. Sélection multiple + actions groupées.
          </p>
        </div>
      </div>

      {/* Filtres */}
      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <h2>Filtres</h2>
          <span className="glyph">◇</span>
        </div>
        <div className="fx-panel-body">
          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <div className="fx-eyebrow" style={{ marginBottom: 8 }}>Sévérité</div>
              <select
                id="cases-severity-filter"
                data-testid="cases-severity-filter"
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                style={{
                  height: 38,
                  width: "100%",
                  background: "var(--bg)",
                  border: "1px solid var(--border)",
                  color: "var(--fg)",
                  fontFamily: "var(--font-mono)",
                  fontSize: 12,
                  padding: "0 12px",
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
              <div className="fx-eyebrow" style={{ marginBottom: 8 }}>Statut</div>
              <select
                id="cases-status-filter"
                data-testid="cases-status-filter"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                style={{
                  height: 38,
                  width: "100%",
                  background: "var(--bg)",
                  border: "1px solid var(--border)",
                  color: "var(--fg)",
                  fontFamily: "var(--font-mono)",
                  fontSize: 12,
                  padding: "0 12px",
                  outline: "none",
                }}
              >
                <option value="">Tous</option>
                <option value="new">Nouveau</option>
                <option value="triaged">Trié</option>
                <option value="in_progress">En cours</option>
                <option value="escalated">Escaladé</option>
                <option value="closed_confirmed">Clos — confirmé</option>
                <option value="closed_rejected">Clos — rejeté</option>
                <option value="closed_false_positive">Clos — faux positif</option>
              </select>
            </div>
            <div className="flex items-end">
              <span
                className="fx-mono"
                style={{ fontSize: 12, color: "var(--muted)" }}
              >
                {rows.length} case(s) — {selected.size} sélectionné(s)
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <div>
            <h2>Dossiers 360 synthétiques</h2>
            <div className="sub">Scénarios reliés au moteur de risque et à l’export Evidence Pack.</div>
          </div>
          <span className="glyph">◎</span>
        </div>
        <div className="fx-panel-body">
          <div className="grid gap-3 md:grid-cols-3">
            {RISK_SCENARIOS.slice(0, 6).map((scenario) => (
              <Link
                key={scenario.caseId}
                href={case360Href(scenario.caseId)}
                className="fx-card"
                style={{ textDecoration: "none", minHeight: 104 }}
              >
                <div className="fx-eyebrow">{scenario.caseId}</div>
                <div className="fx-mono" style={{ marginTop: 8, fontSize: 12, color: "var(--fg)", fontWeight: 600 }}>
                  {scenario.shortTitle}
                </div>
                <p className="fx-mono" style={{ marginTop: 6, fontSize: 11, lineHeight: 1.45, color: "var(--muted)" }}>
                  {scenario.expectedTypology}
                </p>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Bulk ops */}
      {selected.size >= 2 ? (
        <div data-testid="cases-bulk-panel" className="fx-card-accent" style={{ marginBottom: 16 }}>
          <div className="fx-eyebrow">▣ Actions groupées sur {selected.size} cases</div>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <div className="flex gap-2">
              <Input
                aria-label="Assigner les cases sélectionnées à une adresse email"
                placeholder="Assigner à (email)"
                value={bulkAssignee}
                onChange={(e) => setBulkAssignee(e.target.value)}
              />
              <Button
                onClick={() => bulkAssignee && assignMutation.mutate(bulkAssignee)}
                disabled={!bulkAssignee || assignMutation.isPending}
              >
                Assigner
              </Button>
            </div>
            <div className="flex gap-2">
              <Input
                aria-label="Motif de clôture faux positif pour les cases sélectionnées"
                placeholder="Motif clôture (faux positif)"
                value={bulkReason}
                onChange={(e) => setBulkReason(e.target.value)}
              />
              <Button
                variant="danger"
                onClick={() =>
                  bulkReason.trim().length >= 3 &&
                  closeMutation.mutate(bulkReason.trim())
                }
                disabled={
                  bulkReason.trim().length < 3 || closeMutation.isPending
                }
              >
                Clôturer
              </Button>
            </div>
            {assignMutation.isSuccess ? (
              <div
                className="fx-mono"
                style={{ fontSize: 12, color: "var(--verified)" }}
              >
                ✓ Assignation OK : {assignMutation.data.n_ok} · {assignMutation.data.n_errors} erreurs
              </div>
            ) : null}
            {closeMutation.isSuccess ? (
              <div
                className="fx-mono"
                style={{ fontSize: 12, color: "var(--verified)" }}
              >
                ✓ Clôture OK : {closeMutation.data.n_ok} · {closeMutation.data.n_errors} erreurs
              </div>
            ) : null}
          </div>
        </div>
      ) : null}

      {/* Table */}
      <div className="fx-panel">
        <div className="fx-panel-head">
          <h2>Cases</h2>
          <span className="glyph">▣</span>
        </div>
        {casesQuery.isLoading ? (
          <div className="fx-panel-body">
            <span className="fx-mono" style={{ fontSize: 12, color: "var(--muted)" }}>
              Chargement…
            </span>
          </div>
        ) : casesQuery.error ? (
          <div className="fx-panel-body">
            <div className="fx-notice">
              <span className="glyph">⚠</span>
              <div>
                <div className="nt">API indisponible</div>
                <p className="nb">{(casesQuery.error as Error).message}</p>
              </div>
            </div>
          </div>
        ) : (
          <CasesTable
            rows={rows}
            selected={selected}
            toggle={toggle}
            toggleAll={toggleAll}
          />
        )}
      </div>
    </ForensicPage>
  );
}

function CasesTable({
  rows,
  selected,
  toggle,
  toggleAll,
}: {
  rows: CaseOutV1[];
  selected: Set<string>;
  toggle: (id: string) => void;
  toggleAll: () => void;
}) {
  if (!rows.length) {
    return (
      <div className="fx-panel-body">
        <span className="fx-mono" style={{ fontSize: 12, color: "var(--muted)" }}>
          Aucun case enregistré.
        </span>
      </div>
    );
  }
  return (
    <div className="fx-table-wrap">
      <table data-testid="cases-table" className="fx-table">
        <thead>
          <tr>
            <th style={{ width: 32 }}>
              <input
                type="checkbox"
                checked={selected.size === rows.length && rows.length > 0}
                onChange={toggleAll}
                aria-label="Tout sélectionner"
                style={{ accentColor: "var(--risk)" }}
              />
            </th>
            <th>Case ID</th>
            <th>Titre</th>
            <th>Sévérité</th>
            <th>Statut</th>
            <th>Vendor</th>
            <th className="num">Exposition</th>
            <th>Assigné</th>
            <th>Créé</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.case_id}>
              <td>
                <input
                  type="checkbox"
                  checked={selected.has(row.case_id)}
                  onChange={() => toggle(row.case_id)}
                  aria-label={`Sélectionner ${row.case_id}`}
                  style={{ accentColor: "var(--risk)" }}
                />
              </td>
              <td className="key fx-mono" style={{ fontSize: 11 }}>{row.case_id}</td>
              <td>{row.title}</td>
              <td>
                <SeverityBadge value={row.severity} />
              </td>
              <td>
                <span className="fx-mono" style={{ fontSize: 11 }}>
                  {STATUS_LABELS[row.status] ?? row.status}
                </span>
              </td>
              <td className="fx-mono" style={{ fontSize: 11 }}>
                {row.vendor_id ?? <span style={{ color: "var(--dim)" }}>—</span>}
              </td>
              <td className="num">{formatEur(row.exposure_eur)}</td>
              <td className="fx-mono" style={{ fontSize: 11 }}>
                {row.assignee ?? <span style={{ color: "var(--dim)" }}>—</span>}
              </td>
              <td>
                <span className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>
                  {formatDate(row.created_at)}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
