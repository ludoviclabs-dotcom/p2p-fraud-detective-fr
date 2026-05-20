"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import {
  bulkAssignCases,
  bulkCloseCases,
  listCases,
  type CaseOutV1,
} from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { SeverityBadge } from "@/components/ui/badge";
import { formatEur, formatDate } from "@/lib/utils";

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
    <div className="px-8 py-10">
      <div className="mb-1 text-xs uppercase tracking-wider text-[#5a6478]">
        Pilotage
      </div>
      <h1 className="mb-1 text-3xl font-bold text-[#0f1b33] dark:text-white">
        File d'investigation
      </h1>
      <p className="mb-6 text-sm text-[#5a6478]">
        Case management + audit log immutable. Sélection multiple + actions
        groupées.
      </p>

      {/* Filtres */}
      <Card className="mb-4">
        <CardContent className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-[#5a6478]">
              Sévérité
            </label>
            <select
              data-testid="cases-severity-filter"
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
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
            <label className="mb-1 block text-xs font-medium text-[#5a6478]">
              Statut
            </label>
            <select
              data-testid="cases-status-filter"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-10 w-full rounded-md border border-[#e1e5ee] bg-white px-3 text-sm"
            >
              <option value="">Tous</option>
              <option value="new">Nouveau</option>
              <option value="triaged">Trié</option>
              <option value="in_progress">En cours</option>
              <option value="escalated">Escaladé</option>
              <option value="closed_confirmed">Clos — confirmé</option>
              <option value="closed_rejected">Clos — rejeté</option>
              <option value="closed_false_positive">
                Clos — faux positif
              </option>
            </select>
          </div>
          <div className="flex items-end">
            <div className="text-xs text-[#5a6478]">
              {rows.length} case(s) — {selected.size} sélectionné(s)
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Bulk ops */}
      {selected.size >= 2 ? (
        <Card data-testid="cases-bulk-panel" className="mb-4 border-l-4 border-l-[#e5a93a]">
          <CardHeader>
            <CardTitle>
              🧰 Actions groupées sur {selected.size} cases
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="flex gap-2">
              <Input
                placeholder="Assigner à (email)"
                value={bulkAssignee}
                onChange={(e) => setBulkAssignee(e.target.value)}
              />
              <Button
                onClick={() => bulkAssignee && assignMutation.mutate(bulkAssignee)}
                disabled={!bulkAssignee || assignMutation.isPending}
              >
                👥 Assigner
              </Button>
            </div>
            <div className="flex gap-2">
              <Input
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
                ✅ Clôturer
              </Button>
            </div>
            {assignMutation.isSuccess ? (
              <div className="text-xs text-[#3e7c5a]">
                Assignation OK : {assignMutation.data.n_ok} ·{" "}
                {assignMutation.data.n_errors} erreurs
              </div>
            ) : null}
            {closeMutation.isSuccess ? (
              <div className="text-xs text-[#3e7c5a]">
                Clôture OK : {closeMutation.data.n_ok} ·{" "}
                {closeMutation.data.n_errors} erreurs
              </div>
            ) : null}
          </CardContent>
        </Card>
      ) : null}

      {/* Table */}
      <Card>
        <div className="overflow-x-auto">
          {casesQuery.isLoading ? (
            <div className="p-4 text-sm text-[#5a6478]">Chargement…</div>
          ) : casesQuery.error ? (
            <div className="p-4 text-sm text-[#a23e48]">
              API indisponible : {(casesQuery.error as Error).message}
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
      </Card>
    </div>
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
      <div className="p-4 text-sm text-[#5a6478]">Aucun case enregistré.</div>
    );
  }
  return (
    <table data-testid="cases-table" className="w-full text-sm">
      <thead className="bg-[#f4f6fa] text-[#5a6478]">
        <tr>
          <th className="w-8 px-3 py-2">
            <input
              type="checkbox"
              checked={selected.size === rows.length && rows.length > 0}
              onChange={toggleAll}
              aria-label="Tout sélectionner"
            />
          </th>
          <th className="px-3 py-2 text-left">Case ID</th>
          <th className="px-3 py-2 text-left">Titre</th>
          <th className="px-3 py-2 text-left">Sévérité</th>
          <th className="px-3 py-2 text-left">Statut</th>
          <th className="px-3 py-2 text-left">Vendor</th>
          <th className="px-3 py-2 text-right">Exposition</th>
          <th className="px-3 py-2 text-left">Assigné</th>
          <th className="px-3 py-2 text-left">Créé</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr
            key={row.case_id}
            className="border-t border-[#e1e5ee] hover:bg-[#f9fafc]"
          >
            <td className="px-3 py-2">
              <input
                type="checkbox"
                checked={selected.has(row.case_id)}
                onChange={() => toggle(row.case_id)}
                aria-label={`Sélectionner ${row.case_id}`}
              />
            </td>
            <td className="px-3 py-2 font-mono text-xs">{row.case_id}</td>
            <td className="px-3 py-2">{row.title}</td>
            <td className="px-3 py-2">
              <SeverityBadge value={row.severity} />
            </td>
            <td className="px-3 py-2 text-xs">
              {STATUS_LABELS[row.status] ?? row.status}
            </td>
            <td className="px-3 py-2 font-mono text-xs">
              {row.vendor_id ?? "—"}
            </td>
            <td className="px-3 py-2 text-right">
              {formatEur(row.exposure_eur)}
            </td>
            <td className="px-3 py-2 text-xs">{row.assignee ?? "—"}</td>
            <td className="px-3 py-2 text-xs text-[#5a6478]">
              {formatDate(row.created_at)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
