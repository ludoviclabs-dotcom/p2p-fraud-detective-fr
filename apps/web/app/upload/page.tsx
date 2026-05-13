"use client";

import { useState, useRef, type DragEvent, type ChangeEvent } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SeverityBadge } from "@/components/ui/badge";
import { Upload, FileText, AlertCircle, CheckCircle2 } from "lucide-react";
import { formatEur } from "@/lib/utils";

type DetectFinding = {
  invoice_id: string;
  rule_id: string;
  severity: string;
  signal: string;
  detector?: string;
  evidence?: Record<string, unknown>;
};

type DetectResponse = {
  n_invoices: number;
  detectors_run: string[];
  findings: DetectFinding[];
};

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DetectResponse | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  };

  const onSelect = (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) setFile(f);
  };

  const upload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    setResult(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const resp = await fetch("/api/uploads", {
        method: "POST",
        body: formData,
      });
      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(`HTTP ${resp.status} : ${text.slice(0, 200)}`);
      }
      const data: DetectResponse = await resp.json();
      setResult(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="px-8 py-10">
      <div className="mb-1 text-xs uppercase tracking-wider text-[#5a6478]">
        Données
      </div>
      <h1 className="mb-1 text-3xl font-bold text-[#0f1b33] dark:text-white">
        Import des données
      </h1>
      <p className="mb-6 text-sm text-[#5a6478]">
        Upload d'un CSV/Excel de factures fournisseurs (auto-détection schéma
        ERP : SAP, Sage X3, Cegid, Oracle). Le fichier est streamé vers le
        backend FastAPI sans buffering RAM (Route Handler Node.js).
      </p>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>📤 Glisser-déposer un fichier</CardTitle>
        </CardHeader>
        <CardContent>
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            onClick={() => inputRef.current?.click()}
            className={`flex h-40 cursor-pointer flex-col items-center justify-center gap-2 rounded-md border-2 border-dashed transition-colors ${
              dragOver
                ? "border-[#1f3a6e] bg-[#f4f6fa]"
                : "border-[#e1e5ee] hover:border-[#1f3a6e] hover:bg-[#f9fafc]"
            }`}
          >
            <Upload size={32} className="text-[#5a6478]" />
            <div className="text-sm text-[#5a6478]">
              {file ? (
                <span className="flex items-center gap-2">
                  <FileText size={16} />
                  <strong className="text-[#0f1b33]">{file.name}</strong> (
                  {(file.size / 1024).toFixed(1)} Ko)
                </span>
              ) : (
                <>
                  Glissez votre fichier ici ou{" "}
                  <strong className="text-[#1f3a6e]">cliquez pour parcourir</strong>
                </>
              )}
            </div>
            <div className="text-xs text-[#9aa3b2]">CSV, XLSX — max 50 Mo</div>
          </div>
          <input
            ref={inputRef}
            type="file"
            accept=".csv,.xlsx,.xls,.tsv,.parquet"
            onChange={onSelect}
            className="hidden"
          />

          <div className="mt-4 flex flex-wrap items-center gap-3">
            <Button
              onClick={upload}
              disabled={!file || uploading}
              type="button"
            >
              {uploading ? "⏳ Streaming en cours…" : "🚀 Lancer la détection"}
            </Button>
            {file ? (
              <Button
                onClick={() => {
                  setFile(null);
                  setResult(null);
                  setError(null);
                }}
                variant="ghost"
                type="button"
              >
                Annuler
              </Button>
            ) : null}
          </div>

          {error ? (
            <div className="mt-3 flex items-center gap-2 rounded border border-[#a23e48] bg-[#fdecee] p-3 text-sm text-[#a23e48]">
              <AlertCircle size={16} />
              {error}
            </div>
          ) : null}
        </CardContent>
      </Card>

      {result ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-[#3e7c5a]">
              <CheckCircle2 size={18} /> Détection terminée
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-4 grid gap-3 md:grid-cols-3 text-sm">
              <div>
                <div className="text-xs uppercase tracking-wider text-[#5a6478]">
                  Factures analysées
                </div>
                <div className="text-xl font-semibold text-[#0f1b33]">
                  {result.n_invoices.toLocaleString("fr-FR")}
                </div>
              </div>
              <div>
                <div className="text-xs uppercase tracking-wider text-[#5a6478]">
                  Détecteurs exécutés
                </div>
                <div className="text-xl font-semibold text-[#0f1b33]">
                  {result.detectors_run.length}
                </div>
                <div className="text-xs text-[#5a6478]">
                  {result.detectors_run.join(", ")}
                </div>
              </div>
              <div>
                <div className="text-xs uppercase tracking-wider text-[#5a6478]">
                  Findings remontés
                </div>
                <div className="text-xl font-semibold text-[#a23e48]">
                  {result.findings.length}
                </div>
              </div>
            </div>

            {result.findings.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-[#f4f6fa] text-[#5a6478]">
                    <tr>
                      <th className="px-3 py-2 text-left">Invoice ID</th>
                      <th className="px-3 py-2 text-left">Rule</th>
                      <th className="px-3 py-2 text-left">Sévérité</th>
                      <th className="px-3 py-2 text-left">Signal</th>
                      <th className="px-3 py-2 text-right">Exposition</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.findings.slice(0, 100).map((f, i) => {
                      const exp = f.evidence?.exposure_eur as
                        | number
                        | undefined;
                      return (
                        <tr
                          key={`${f.invoice_id}-${f.rule_id}-${i}`}
                          className="border-t border-[#e1e5ee]"
                        >
                          <td className="px-3 py-2 font-mono text-xs">
                            {f.invoice_id}
                          </td>
                          <td className="px-3 py-2 font-mono text-xs">
                            {f.rule_id}
                          </td>
                          <td className="px-3 py-2">
                            <SeverityBadge value={f.severity} />
                          </td>
                          <td className="px-3 py-2">{f.signal}</td>
                          <td className="px-3 py-2 text-right">
                            {formatEur(exp)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                {result.findings.length > 100 ? (
                  <div className="px-3 py-2 text-xs text-[#5a6478]">
                    Affichage limité aux 100 premiers ·{" "}
                    {result.findings.length - 100} masqués.
                  </div>
                ) : null}
              </div>
            ) : (
              <div className="text-sm text-[#3e7c5a]">
                ✅ Aucun finding remonté — dataset clean.
              </div>
            )}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
