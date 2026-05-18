"use client";

import { useEffect, useMemo, useState } from "react";

import {
  CASE_WORKFLOW_STORAGE_KEY,
  getCaseStatusLabel,
  type CaseWorkflowRecord,
} from "@/lib/case-workflow";

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

export function CaseWorkflowStatusBadge({
  caseIds,
  vendorId,
}: {
  caseIds?: string[];
  vendorId?: string;
}) {
  const [records, setRecords] = useState<CaseWorkflowRecord[]>([]);

  useEffect(() => {
    const refresh = () => setRecords(readStoredRecords());
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
      <span className="inline-flex rounded bg-[#eef3fb] px-2 py-1 text-xs font-semibold text-[#5a6478]">
        A qualifier
      </span>
    );
  }

  return (
    <span className="inline-flex rounded bg-[#e8f8f1] px-2 py-1 text-xs font-semibold text-[#22754c]">
      {getCaseStatusLabel(match.status)}
    </span>
  );
}
