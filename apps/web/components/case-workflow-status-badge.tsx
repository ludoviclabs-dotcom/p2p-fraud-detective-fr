"use client";

import { useEffect, useMemo, useState } from "react";

import {
  getCaseStatusLabel,
  readStoredCaseWorkflowRecords,
  type CaseWorkflowRecord,
} from "@/lib/case-workflow";

export function CaseWorkflowStatusBadge({
  caseIds,
  vendorId,
}: {
  caseIds?: string[];
  vendorId?: string;
}) {
  const [records, setRecords] = useState<CaseWorkflowRecord[]>([]);

  useEffect(() => {
    const refresh = () => setRecords(readStoredCaseWorkflowRecords());
    refresh();
    window.addEventListener("p2p-case-workflow-updated", refresh);
    window.addEventListener("storage", refresh);
    return () => {
      window.removeEventListener("p2p-case-workflow-updated", refresh);
      window.removeEventListener("storage", refresh);
    };
  }, []);

  const match = useMemo(() => {
    const ids = new Set(caseIds ?? []);
    return records.find(
      (record) =>
        ids.has(record.id) ||
        ids.has(record.findingId) ||
        record.vendorId === vendorId,
    );
  }, [caseIds, records, vendorId]);

  if (!match) {
    return (
      <span
        className="fx-mono"
        style={{
          display: "inline-block",
          padding: "2px 8px",
          fontSize: 10,
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          color: "var(--muted)",
          border: "1px solid var(--border-strong)",
          background: "var(--panel)",
        }}
      >
        A qualifier
      </span>
    );
  }

  return (
    <span
      className="fx-mono"
      style={{
        display: "inline-block",
        padding: "2px 8px",
        fontSize: 10,
        letterSpacing: "0.1em",
        textTransform: "uppercase",
        color: "var(--verified)",
        border: "1px solid var(--verified)",
        background: "rgba(127,163,127,0.08)",
      }}
    >
      {getCaseStatusLabel(match.status)}
    </span>
  );
}
