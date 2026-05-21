"use client";

import { useState, useRef, type DragEvent, type ChangeEvent } from "react";
import { SeverityBadge } from "@/components/ui/badge";
import { formatEur } from "@/lib/utils";
import { ForensicPage } from "@/components/forensic-page";

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
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Données</div>
          <h1 style={{ marginTop: 9 }}>
            Import des <span className="italic">données</span>
          </h1>
          <p className="sub">
            Upload d&apos;un CSV/Excel de factures fournisseurs (auto-détection
            schéma ERP : SAP, Sage X3, Cegid, Oracle). Le fichier est streamé
            vers le backend FastAPI sans buffering RAM (Route Handler Node.js).
          </p>
        </div>
      </div>

      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <div>
            <h2>Glisser-déposer un fichier</h2>
            <div className="sub">CSV, XLSX — max 50 Mo</div>
          </div>
          <span className="glyph">▲</span>
        </div>
        <div className="fx-panel-body">
          <div
            data-testid="upload-dropzone"
            role="button"
            tabIndex={0}
            aria-controls="upload-input"
            aria-label="Choisir un fichier CSV ou Excel synthétique à analyser"
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            onClick={() => inputRef.current?.click()}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                inputRef.current?.click();
              }
            }}
            style={{
              height: 140,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
              cursor: "pointer",
              border: dragOver
                ? "2px dashed var(--risk)"
                : "2px dashed var(--border-strong)",
              background: dragOver ? "var(--risk-soft)" : "var(--bg-2)",
              transition: "border-color .15s, background .15s",
            }}
          >
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: 28,
                color: dragOver ? "var(--risk)" : "var(--muted)",
              }}
            >
              ▲
            </span>
            <div
              className="fx-mono"
              style={{ fontSize: 13, color: "var(--fg-2)" }}
            >
              {file ? (
                <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ color: "var(--muted)" }}>◫</span>
                  <strong style={{ color: "var(--fg)" }}>{file.name}</strong>
                  <span style={{ color: "var(--muted)" }}>
                    ({(file.size / 1024).toFixed(1)} Ko)
                  </span>
                </span>
              ) : (
                <>
                  Glissez votre fichier ici ou{" "}
                  <strong style={{ color: "var(--fg)" }}>
                    cliquez pour parcourir
                  </strong>
                </>
              )}
            </div>
            <div className="fx-eyebrow">CSV, XLSX — max 50 Mo</div>
          </div>
          <input
            id="upload-input"
            data-testid="upload-input"
            ref={inputRef}
            type="file"
            aria-label="Fichier de factures synthétiques"
            accept=".csv,.xlsx,.xls,.tsv,.parquet"
            onChange={onSelect}
            style={{ display: "none" }}
          />

          <div className="mt-4 flex flex-wrap items-center gap-3">
            <button
              className="fx-btn"
              onClick={upload}
              disabled={!file || uploading}
              type="button"
            >
              {uploading ? "◷ Streaming en cours…" : "▲ Lancer la détection"}
            </button>
            {file ? (
              <button
                className="fx-btn-ghost"
                onClick={() => {
                  setFile(null);
                  setResult(null);
                  setError(null);
                }}
                type="button"
              >
                Annuler
              </button>
            ) : null}
          </div>

          {error ? (
            <div
              className="fx-notice"
              style={{ marginTop: 12, borderLeftColor: "var(--risk)" }}
            >
              <span className="glyph">⚠</span>
              <div>
                <div className="nt">Erreur d&apos;upload</div>
                <p className="nb">{error}</p>
              </div>
            </div>
          ) : null}
        </div>
      </div>

      {result ? (
        <div className="fx-panel" data-testid="upload-result">
          <div className="fx-panel-head">
            <div>
              <h2>
                Détection <span className="italic">terminée</span>
              </h2>
              <div className="sub">Résultats de l&apos;analyse</div>
            </div>
            <span className="glyph">✓</span>
          </div>
          <div className="fx-panel-body">
            <div className="grid gap-3 md:grid-cols-3" style={{ marginBottom: 20 }}>
              <div className="fx-stat info">
                <div className="lbl">Factures analysées</div>
                <div className="val">
                  {result.n_invoices.toLocaleString("fr-FR")}
                </div>
              </div>
              <div className="fx-stat ok">
                <div className="lbl">Détecteurs exécutés</div>
                <div className="val">{result.detectors_run.length}</div>
                <div
                  className="fx-mono"
                  style={{
                    fontSize: 10,
                    color: "var(--muted)",
                    marginTop: 6,
                    lineHeight: 1.5,
                  }}
                >
                  {result.detectors_run.join(", ")}
                </div>
              </div>
              <div className="fx-stat risk">
                <div className="lbl">Findings remontés</div>
                <div className="val">{result.findings.length}</div>
              </div>
            </div>

            {result.findings.length > 0 ? (
              <>
                <div className="fx-table-wrap">
                  <table
                    data-testid="upload-findings-table"
                    className="fx-table"
                  >
                    <thead>
                      <tr>
                        <th>Invoice ID</th>
                        <th>Rule</th>
                        <th>Sévérité</th>
                        <th>Signal</th>
                        <th className="num">Exposition</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.findings.slice(0, 100).map((f, i) => {
                        const exp = f.evidence?.exposure_eur as
                          | number
                          | undefined;
                        return (
                          <tr key={`${f.invoice_id}-${f.rule_id}-${i}`}>
                            <td className="key">{f.invoice_id}</td>
                            <td>{f.rule_id}</td>
                            <td>
                              <SeverityBadge value={f.severity} />
                            </td>
                            <td>{f.signal}</td>
                            <td className="num">{formatEur(exp)}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
                {result.findings.length > 100 ? (
                  <div
                    className="fx-mono"
                    style={{
                      fontSize: 10,
                      color: "var(--muted)",
                      padding: "8px 0",
                    }}
                  >
                    Affichage limité aux 100 premiers ·{" "}
                    {result.findings.length - 100} masqués.
                  </div>
                ) : null}
              </>
            ) : (
              <div
                className="fx-notice"
                style={{ borderLeftColor: "var(--verified)" }}
              >
                <span
                  className="glyph"
                  style={{ color: "var(--verified)" }}
                >
                  ✓
                </span>
                <div>
                  <div className="nt" style={{ color: "var(--verified)" }}>
                    Dataset clean
                  </div>
                  <p className="nb">Aucun finding remonté.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : null}
    </ForensicPage>
  );
}
