"use client";

import { useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import Link from "next/link";
import { ForensicPage } from "@/components/forensic-page";
import { SeverityBadge } from "@/components/ui/badge";
import {
  scanConflicts,
  type ConflictFindingOut,
  type EmployeeIn,
} from "@/lib/api-client";
import {
  DEMO_EMPLOYEES,
  DEMO_VENDORS,
  parseEmployeesCsv,
  scanConflictsLocally,
} from "@/data/conflicts-demo";

type ScanSource = "backend" | "offline";

export default function ConflictsPage() {
  const [employees, setEmployees] = useState<EmployeeIn[]>(DEMO_EMPLOYEES);
  const [employeesSource, setEmployeesSource] = useState<"demo" | "csv">("demo");
  const [results, setResults] = useState<ConflictFindingOut[] | null>(null);
  const [scanSource, setScanSource] = useState<ScanSource>("offline");
  const [csvError, setCsvError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const mutation = useMutation({
    mutationFn: () => scanConflicts({ employees, vendors: DEMO_VENDORS }),
    onSuccess: (data) => {
      setResults(data);
      setScanSource("backend");
    },
    onError: () => {
      // Backend injoignable → même matching exécuté localement (démo offline).
      setResults(scanConflictsLocally(employees, DEMO_VENDORS));
      setScanSource("offline");
    },
  });

  const onCsvSelected = async (file: File) => {
    setCsvError(null);
    const text = await file.text();
    const rows = parseEmployeesCsv(text);
    if (!rows.length) {
      setCsvError(
        "CSV illisible — en-tête requis avec au minimum les colonnes employee_id et full_name " +
          "(optionnelles : email, phone, address, iban, department, can_approve_payments).",
      );
      return;
    }
    setEmployees(rows);
    setEmployeesSource("csv");
    setResults(null);
  };

  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Contrôles master data</div>
          <h1 style={{ marginTop: 9 }}>
            Conflits d&apos;intérêts — <span className="italic">employé ↔ fournisseur</span>
          </h1>
          <p className="sub">
            Croisement du référentiel RH avec le référentiel fournisseurs : IBAN de paie identique
            à un IBAN fournisseur, adresse commune, homonymie forte — et rupture de séparation des
            tâches quand l&apos;employé lié peut approuver des paiements.
          </p>
        </div>
      </div>

      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <h2>Description du contrôle</h2>
        </div>
        <div className="fx-panel-body">
          <p style={{ fontSize: 14, lineHeight: 1.6, color: "var(--fg-2)" }}>
            Le référentiel RH transite dans la requête de scan et n&apos;est{" "}
            <strong style={{ color: "var(--fg)" }}>jamais persisté</strong> (RGPD : minimisation,
            finalité détection de fraude interne). En production, les IBAN de paie sont hachés
            côté ingestion. Quatre règles : COI_SHARED_IBAN (CRITICAL), COI_SHARED_ADDRESS (HIGH),
            COI_NAME_MATCH (MEDIUM), COI_APPROVER_LINK (HIGH — rupture 4-eyes).
          </p>
          <div style={{ marginTop: 16 }}>
            <div className="fx-eyebrow">Références réglementaires</div>
            <ul className="space-y-1" style={{ marginTop: 8, listStyle: "none", padding: 0 }}>
              {[
                ["ISA 240", "Management override — parties liées non déclarées"],
                ["ISA 550", "Parties liées et transactions avec des parties liées"],
                ["Sapin 2 art. 17", "Cartographie des risques de corruption"],
                ["Code pénal 432-12", "Prise illégale d'intérêts (secteur public)"],
              ].map(([label, ref]) => (
                <li key={label} className="fx-mono" style={{ fontSize: 12 }}>
                  <span style={{ color: "var(--fg)" }}>{label}</span>
                  <span style={{ color: "var(--muted)" }}> · {ref}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <div>
            <div className="fx-eyebrow">§ Référentiel RH</div>
            <h2 style={{ marginTop: 4 }}>
              {employeesSource === "demo"
                ? `Jeu de démonstration — ${employees.length} employés`
                : `Import CSV — ${employees.length} employés`}
            </h2>
          </div>
          <span className="glyph">↥</span>
        </div>
        <div className="fx-panel-body">
          <div className="fx-table-wrap" style={{ marginBottom: 14 }}>
            <table className="fx-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Nom</th>
                  <th>Service</th>
                  <th>IBAN paie</th>
                  <th>Approbation paiements</th>
                </tr>
              </thead>
              <tbody>
                {employees.slice(0, 8).map((e) => (
                  <tr key={e.employee_id}>
                    <td className="key">{e.employee_id}</td>
                    <td>{e.full_name}</td>
                    <td>{e.department ?? "—"}</td>
                    <td className="fx-mono" style={{ fontSize: 11 }}>
                      {e.iban ? `${e.iban.slice(0, 4)}…${e.iban.replace(/\s/g, "").slice(-4)}` : "—"}
                    </td>
                    <td style={{ color: e.can_approve_payments ? "var(--warn)" : "var(--muted)" }}>
                      {e.can_approve_payments ? "OUI" : "non"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {employees.length > 8 ? (
              <div className="fx-mono" style={{ fontSize: 10, color: "var(--muted)", padding: "6px 2px" }}>
                … et {employees.length - 8} autres lignes
              </div>
            ) : null}
          </div>

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
            <button
              type="button"
              className="fx-btn-ghost sm"
              disabled={mutation.isPending}
              onClick={() => mutation.mutate()}
            >
              {mutation.isPending ? "◷ Scan en cours…" : "▶ Lancer le scan croisé"}
            </button>
            <button
              type="button"
              className="fx-btn-ghost sm"
              onClick={() => fileRef.current?.click()}
            >
              ↥ Importer un CSV RH
            </button>
            {employeesSource === "csv" ? (
              <button
                type="button"
                className="fx-btn-ghost sm"
                onClick={() => {
                  setEmployees(DEMO_EMPLOYEES);
                  setEmployeesSource("demo");
                  setResults(null);
                }}
              >
                × Revenir au jeu de démo
              </button>
            ) : null}
            <input
              ref={fileRef}
              type="file"
              accept=".csv,text/csv"
              style={{ display: "none" }}
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) void onCsvSelected(f);
                e.target.value = "";
              }}
            />
            <span className="fx-mono" style={{ fontSize: 10, color: "var(--muted)" }}>
              Croisé contre {DEMO_VENDORS.length} fournisseurs du référentiel démo
            </span>
          </div>
          {csvError ? (
            <p className="fx-mono" style={{ fontSize: 11, color: "var(--warn)", marginTop: 10 }}>
              {csvError}
            </p>
          ) : null}
        </div>
      </div>

      {results !== null ? <ResultsPanel results={results} source={scanSource} /> : null}
    </ForensicPage>
  );
}

function ResultsPanel({
  results,
  source,
}: {
  results: ConflictFindingOut[];
  source: ScanSource;
}) {
  const critical = results.filter((r) => r.severity === "critical").length;
  const high = results.filter((r) => r.severity === "high").length;

  return (
    <div className="fx-panel">
      <div className="fx-panel-head">
        <div>
          <div className="fx-eyebrow">§ Résultats du scan</div>
          <h2 style={{ marginTop: 4 }}>
            {results.length ? `${results.length} lien(s) non déclaré(s)` : "Aucun lien détecté"}
          </h2>
        </div>
        <span
          className="fx-mono"
          style={{
            fontSize: 10,
            padding: "3px 8px",
            border: `1px solid ${source === "backend" ? "var(--ok)" : "var(--info)"}`,
            color: source === "backend" ? "var(--ok)" : "var(--info)",
          }}
        >
          {source === "backend" ? "SCAN BACKEND" : "DÉMO OFFLINE (calcul local)"}
        </span>
      </div>
      <div className="fx-panel-body">
        {results.length ? (
          <>
            <div className="fx-mono" style={{ fontSize: 11, color: "var(--muted)", marginBottom: 12 }}>
              {critical} critical · {high} high — chaque ligne est un candidat d&apos;enquête, pas
              une conclusion : vérifier la déclaration d&apos;intérêts avant escalade.
            </div>
            <div className="fx-table-wrap">
              <table className="fx-table">
                <thead>
                  <tr>
                    <th>Règle</th>
                    <th>Sévérité</th>
                    <th>Employé</th>
                    <th>Fournisseur</th>
                    <th>Détail</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r, i) => (
                    <tr key={`${r.rule_id}-${r.employee_id}-${r.siren}-${i}`}>
                      <td className="key">{r.rule_id}</td>
                      <td>
                        <SeverityBadge value={r.severity} />
                      </td>
                      <td className="fx-mono" style={{ fontSize: 11 }}>
                        {r.employee_id}
                      </td>
                      <td>
                        {r.vendor_name}
                        <div className="fx-mono" style={{ fontSize: 10, color: "var(--muted)" }}>
                          SIREN {r.siren}
                        </div>
                      </td>
                      <td style={{ fontSize: 12, color: "var(--fg-2)" }}>
                        {String(r.evidence?.reason ?? r.signal)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ marginTop: 14, display: "flex", gap: 8, flexWrap: "wrap" }}>
              <Link href="/rings" className="fx-btn-ghost sm">
                Visualiser le graphe des liens →
              </Link>
              <Link href="/exports" className="fx-btn-ghost sm">
                Exporter la preuve signée →
              </Link>
            </div>
          </>
        ) : (
          <span className="fx-mono" style={{ fontSize: 12, color: "var(--muted)" }}>
            Aucun IBAN, adresse ou homonymie partagés entre ce référentiel RH et les fournisseurs.
          </span>
        )}
      </div>
    </div>
  );
}
