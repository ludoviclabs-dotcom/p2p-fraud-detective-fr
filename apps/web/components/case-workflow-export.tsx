"use client";

import Link from "next/link";
import { Download, FileSpreadsheet, RotateCcw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import {
  CASE_WORKFLOW_STORAGE_KEY,
  exportCaseWorkflowCsv,
  getCaseDecisionLabel,
  getCaseStatusLabel,
  type CaseWorkflowContext,
  type CaseWorkflowRecord,
} from "@/lib/case-workflow";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SeverityBadge } from "@/components/ui/badge";
import { formatEuro } from "@/lib/p2p-demo-format";
import { getSignalLabel } from "@/lib/p2p-demo-taxonomy";

function readStoredRecords(): CaseWorkflowRecord[] {
  if (typeof window === "undefined") return [];

  try {
    const raw = window.localStorage.getItem(CASE_WORKFLOW_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

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

  const refresh = () => setRecords(readStoredRecords());

  useEffect(() => {
    refresh();
    window.addEventListener("p2p-case-workflow-updated", refresh);
    window.addEventListener("storage", refresh);
    return () => {
      window.removeEventListener("p2p-case-workflow-updated", refresh);
      window.removeEventListener("storage", refresh);
    };
  }, []);

  const metrics = useMemo(() => {
    const exposure = records.reduce((sum, record) => sum + record.exposureEur, 0);
    const escalated = records.filter((record) => record.status === "escalated").length;
    const cleared = records.filter((record) => record.status === "cleared").length;
    return { exposure, escalated, cleared };
  }, [records]);

  const exportCsv = () => {
    downloadText(
      `p2p_case_workflow_${new Date().toISOString().slice(0, 10)}.csv`,
      exportCaseWorkflowCsv(records),
      "text/csv;charset=utf-8",
    );
  };

  const exportJson = () => {
    downloadText(
      `p2p_case_workflow_${new Date().toISOString().slice(0, 10)}.json`,
      JSON.stringify(records, null, 2),
      "application/json;charset=utf-8",
    );
  };

  return (
    <div className="space-y-5">
      <section className="grid gap-4 md:grid-cols-4">
        <Metric label="Cas qualifies" value={String(records.length)} />
        <Metric label="Escalades" value={String(metrics.escalated)} />
        <Metric label="Clotures" value={String(metrics.cleared)} />
        <Metric label="Exposition" value={formatEuro(metrics.exposure)} />
      </section>

      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <CardTitle>Registre local des decisions</CardTitle>
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" type="button" onClick={refresh}>
                <RotateCcw aria-hidden className="h-4 w-4" />
                Actualiser
              </Button>
              <Button
                variant="outline"
                type="button"
                disabled={!records.length}
                onClick={exportJson}
              >
                JSON
              </Button>
              <Button type="button" disabled={!records.length} onClick={exportCsv}>
                <Download aria-hidden className="h-4 w-4" />
                CSV audit
              </Button>
            </div>
          </div>
        </CardHeader>

        {records.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-[#f6f7fb] text-[#5a6478]">
                <tr>
                  <th className="px-4 py-3 text-left">Invoice</th>
                  <th className="px-4 py-3 text-left">Fournisseur</th>
                  <th className="px-4 py-3 text-left">Statut</th>
                  <th className="px-4 py-3 text-left">Decision</th>
                  <th className="px-4 py-3 text-left">Responsable</th>
                  <th className="px-4 py-3 text-right">Exposition</th>
                </tr>
              </thead>
              <tbody>
                {records.map((record) => (
                  <tr key={record.id} className="border-t border-[#e6ebf2]">
                    <td className="px-4 py-3">
                      <Link
                        href={`/score/${record.invoiceId}`}
                        className="mono text-xs font-semibold text-[#1f3a6e]"
                      >
                        {record.invoiceId}
                      </Link>
                      <div className="mt-1">
                        <SeverityBadge value={record.severity} />
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        href={`/vendors/${record.vendorId}`}
                        className="font-medium text-[#141927] hover:text-[#1f3a6e]"
                      >
                        {record.vendorName}
                      </Link>
                      <div className="mt-1 text-xs text-[#5a6478]">
                        {getSignalLabel(record.signal)}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-[#141927]">
                      {getCaseStatusLabel(record.status)}
                    </td>
                    <td className="px-4 py-3 text-[#141927]">
                      {getCaseDecisionLabel(record.decision)}
                    </td>
                    <td className="px-4 py-3 text-[#5a6478]">
                      {record.assignee || "-"}
                    </td>
                    <td className="mono px-4 py-3 text-right text-[#141927]">
                      {formatEuro(record.exposureEur)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <CardContent className="space-y-3 text-sm leading-6 text-[#5a6478]">
            <div className="flex items-center gap-2 font-medium text-[#141927]">
              <FileSpreadsheet aria-hidden className="h-4 w-4 text-[#1f3a6e]" />
              Aucun cas qualifie dans ce navigateur.
            </div>
            <p>
              Ouvrir une fiche score ou fournisseur, renseigner la qualification audit,
              puis revenir ici pour exporter le registre.
            </p>
          </CardContent>
        )}
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Cas prioritaires a qualifier</CardTitle>
        </CardHeader>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-[#f6f7fb] text-[#5a6478]">
              <tr>
                <th className="px-4 py-3 text-left">Invoice</th>
                <th className="px-4 py-3 text-left">Signal</th>
                <th className="px-4 py-3 text-left">Severite</th>
                <th className="px-4 py-3 text-right">Score</th>
                <th className="px-4 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {suggestedCases.slice(0, 20).map((item) => (
                <tr key={item.id} className="border-t border-[#e6ebf2]">
                  <td className="px-4 py-3">
                    <Link
                      href={`/score/${item.invoiceId}`}
                      className="mono text-xs font-semibold text-[#1f3a6e]"
                    >
                      {item.invoiceId}
                    </Link>
                    <div className="mt-1 text-xs text-[#5a6478]">
                      {item.vendorName}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-[#141927]">
                    {getSignalLabel(item.signal)}
                  </td>
                  <td className="px-4 py-3">
                    <SeverityBadge value={item.severity} />
                  </td>
                  <td className="mono px-4 py-3 text-right text-[#141927]">
                    {item.riskScore}/100
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      href={`/score/${item.invoiceId}`}
                      className="font-semibold text-[#1f3a6e]"
                    >
                      Qualifier
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardContent>
        <div className="text-xs font-semibold uppercase tracking-[0.14em] text-[#5a6478]">
          {label}
        </div>
        <div className="mt-2 text-2xl font-semibold text-[#141927]">{value}</div>
      </CardContent>
    </Card>
  );
}
