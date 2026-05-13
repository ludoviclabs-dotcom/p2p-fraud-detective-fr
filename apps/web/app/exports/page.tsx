"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { listCases, type CaseOutV1 } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SeverityBadge } from "@/components/ui/badge";
import { Download, FileText, Table as TableIcon } from "lucide-react";
import { formatEur, formatDate } from "@/lib/utils";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";
const SECRET = process.env.FRAUD_API_SECRET ?? "";

function downloadCasesCsv(rows: CaseOutV1[]) {
  const headers = [
    "case_id",
    "title",
    "severity",
    "status",
    "vendor_id",
    "exposure_eur",
    "assignee",
    "created_at",
  ];
  const lines = [headers.join(",")];
  for (const r of rows) {
    const cells = [
      r.case_id,
      `"${(r.title ?? "").replace(/"/g, '""')}"`,
      r.severity,
      r.status,
      r.vendor_id ?? "",
      String(r.exposure_eur ?? ""),
      r.assignee ?? "",
      r.created_at,
    ];
    lines.push(cells.join(","));
  }
  const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `cases_export_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

async function downloadPdf(caseId: string) {
  const url = `${API_BASE}/api/v1/exports/dossier.pdf?case_id=${encodeURIComponent(caseId)}`;
  const headers: HeadersInit = {};
  if (SECRET) headers.Authorization = `Bearer ${SECRET}`;
  const resp = await fetch(url, { headers });
  if (!resp.ok) {
    alert(`Erreur ${resp.status} : ${await resp.text()}`);
    return;
  }
  const blob = await resp.blob();
  const blobUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = blobUrl;
  a.download = `dossier_${caseId}.pdf`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(blobUrl);
}

export default function ExportsPage() {
  const [search, setSearch] = useState("");
  const [downloading, setDownloading] = useState<string | null>(null);

  const cases = useQuery({
    queryKey: ["exports-cases"],
    queryFn: () => listCases({ limit: 1000 }),
  });

  const rows = useMemo(() => {
    const all = cases.data ?? [];
    const filtered = !search
      ? all
      : all.filter(
          (c) =>
            c.case_id.toLowerCase().includes(search.toLowerCase()) ||
            c.title.toLowerCase().includes(search.toLowerCase()) ||
            (c.vendor_id ?? "").toLowerCase().includes(search.toLowerCase()),
        );
    return [...filtered].sort(
      (a, b) => (b.exposure_eur ?? 0) - (a.exposure_eur ?? 0),
    );
  }, [cases.data, search]);

  const handlePdf = async (caseId: string) => {
    setDownloading(caseId);
    try {
      await downloadPdf(caseId);
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="px-8 py-10">
      <div className="mb-1 text-xs uppercase tracking-wider text-[#5a6478]">
        Investigation
      </div>
      <h1 className="mb-1 text-3xl font-bold text-[#0f1b33] dark:text-white">
        Synthèse — export
      </h1>
      <p className="mb-6 text-sm text-[#5a6478]">
        Génération de dossiers d'enquête PDF (weasyprint côté FastAPI) et
        export CSV de la sélection. Conforme aux exigences d'archivage légal
        Sapin 2 (10 ans).
      </p>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>📥 Export global CSV</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap items-center gap-3">
          <Button
            onClick={() => downloadCasesCsv(rows)}
            disabled={!rows.length}
          >
            <TableIcon size={16} /> Télécharger {rows.length} case(s) en CSV
          </Button>
          <span className="text-xs text-[#5a6478]">
            Encodage UTF-8, séparateur virgule, escape RFC 4180.
          </span>
        </CardContent>
      </Card>

      <Card className="mb-4">
        <CardContent>
          <Input
            placeholder="Filtrer cases (id, titre, vendor)…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>📄 Dossiers PDF individuels</CardTitle>
        </CardHeader>
        <div className="overflow-x-auto">
          {cases.isLoading ? (
            <div className="p-4 text-sm text-[#5a6478]">Chargement…</div>
          ) : !rows.length ? (
            <div className="p-4 text-sm text-[#5a6478]">
              Aucun case à exporter.
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-[#f4f6fa] text-[#5a6478]">
                <tr>
                  <th className="px-3 py-2 text-left">Case ID</th>
                  <th className="px-3 py-2 text-left">Titre</th>
                  <th className="px-3 py-2 text-left">Sévérité</th>
                  <th className="px-3 py-2 text-right">Exposition</th>
                  <th className="px-3 py-2 text-left">Créé</th>
                  <th className="px-3 py-2 text-right">PDF</th>
                </tr>
              </thead>
              <tbody>
                {rows.slice(0, 200).map((c) => (
                  <tr
                    key={c.case_id}
                    className="border-t border-[#e1e5ee] hover:bg-[#f9fafc]"
                  >
                    <td className="px-3 py-2 font-mono text-xs">
                      {c.case_id.slice(0, 16)}
                    </td>
                    <td className="px-3 py-2">{c.title}</td>
                    <td className="px-3 py-2">
                      <SeverityBadge value={c.severity} />
                    </td>
                    <td className="px-3 py-2 text-right">
                      {formatEur(c.exposure_eur)}
                    </td>
                    <td className="px-3 py-2 text-xs text-[#5a6478]">
                      {formatDate(c.created_at)}
                    </td>
                    <td className="px-3 py-2 text-right">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePdf(c.case_id)}
                        disabled={downloading === c.case_id}
                      >
                        {downloading === c.case_id ? (
                          "⏳"
                        ) : (
                          <>
                            <Download size={12} /> PDF
                          </>
                        )}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {rows.length > 200 ? (
            <div className="px-3 py-2 text-xs text-[#5a6478]">
              Affichage limité aux 200 premiers · filtrer pour affiner.
            </div>
          ) : null}
        </div>
      </Card>

      <Card className="mt-4">
        <CardHeader>
          <CardTitle>
            <FileText size={16} className="inline" /> Format des dossiers PDF
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-[#5a6478]">
          <p>
            Les dossiers PDF sont générés côté FastAPI via <strong>weasyprint</strong>{" "}
            (HTML → PDF). Chaque dossier contient :
          </p>
          <ul className="ml-4 list-disc space-y-1">
            <li>En-tête institutionnel + case_id + horodatage</li>
            <li>Identification fournisseur (vendor_id, exposition)</li>
            <li>Sévérité + titre + statut + assigné</li>
            <li>Justification SHAP (si disponible côté détecteur)</li>
            <li>Mention « démonstration pédagogique, non transmissible à Tracfin »</li>
          </ul>
          <p className="mt-2">
            Endpoint :{" "}
            <code className="rounded bg-[#f4f6fa] px-1 py-0.5 text-xs">
              GET /api/v1/exports/dossier.pdf?case_id=...
            </code>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
