"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { listCases, type CaseOutV1 } from "@/lib/api-client";
import { Input } from "@/components/ui/input";
import { SeverityBadge } from "@/components/ui/badge";
import { formatEur } from "@/lib/utils";
import { ForensicPage } from "@/components/forensic-page";

export default function SanctionsPage() {
  const [search, setSearch] = useState("");

  const query = useQuery({
    queryKey: ["sanctions-cases"],
    queryFn: () => listCases({ limit: 500 }),
  });

  const sanctionsCases = useMemo(() => {
    return (query.data ?? []).filter((c) => {
      const t = (c.title || "").toLowerCase();
      return (
        t.includes("sanction") ||
        t.includes("pep") ||
        t.includes("ofac") ||
        t.includes("aml")
      );
    });
  }, [query.data]);

  const filteredCases = useMemo(() => {
    if (!search) return sanctionsCases;
    const q = search.toLowerCase();
    return sanctionsCases.filter(
      (c) =>
        c.vendor_id?.toLowerCase().includes(q) ||
        c.title.toLowerCase().includes(q) ||
        c.case_id.toLowerCase().includes(q),
    );
  }, [sanctionsCases, search]);

  const n_critical = sanctionsCases.filter((c) => c.severity === "critical").length;
  const n_pep = sanctionsCases.filter((c) =>
    (c.title || "").toLowerCase().includes("pep"),
  ).length;
  const n_listed = sanctionsCases.filter((c) =>
    (c.title || "").toLowerCase().includes("sanction"),
  ).length;
  const totalExposure = sanctionsCases.reduce(
    (s, c) => s + (c.exposure_eur ?? 0),
    0,
  );

  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Contrôles statistiques</div>
          <h1 style={{ marginTop: 9 }}>
            Sanctions <span className="italic">&amp; PEP</span>
          </h1>
          <p className="sub">
            Croisement des fournisseurs avec OpenSanctions (UE consolidée, OFAC SDN, Trésor FR) +
            listes PEP. Source live activable via{" "}
            <span className="fx-mono" style={{ color: "var(--fg-2)" }}>
              ENRICHMENT_MODE=live
            </span>{" "}
            +{" "}
            <span className="fx-mono" style={{ color: "var(--fg-2)" }}>
              YENTE_BASE_URL
            </span>{" "}
            (cf. P5-1).
          </p>
        </div>
      </div>

      <div className="mb-5 grid gap-4 md:grid-cols-4">
        <div className="fx-stat info">
          <div className="fx-stat-top">
            <span className="glyph">§</span>
          </div>
          <div className="lbl">Cas sanctions/PEP</div>
          <div className="val">{sanctionsCases.length}</div>
        </div>
        <div className="fx-stat risk">
          <div className="fx-stat-top">
            <span className="glyph">▲</span>
          </div>
          <div className="lbl">CRITICAL</div>
          <div className="val">{n_critical}</div>
        </div>
        <div className="fx-stat warn">
          <div className="fx-stat-top">
            <span className="glyph">◇</span>
          </div>
          <div className="lbl">Liens PEP</div>
          <div className="val">{n_pep}</div>
          <div
            className="fx-mono"
            style={{ fontSize: 10, color: "var(--muted)", marginTop: 4 }}
          >
            {n_listed} listés sanctions
          </div>
        </div>
        <div className="fx-stat">
          <div className="fx-stat-top">
            <span className="glyph">Σ</span>
          </div>
          <div className="lbl">Exposition flagée</div>
          <div className="val">{formatEur(totalExposure)}</div>
        </div>
      </div>

      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-body">
          <Input
            aria-label="Rechercher un fournisseur, une case ou un titre sanctions PEP"
            placeholder="Rechercher vendor / case / titre…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <h2>Cas flagués sanctions / PEP</h2>
          <span className="glyph">▲</span>
        </div>
        {query.isLoading ? (
          <div className="fx-panel-body">
            <span className="fx-mono" style={{ fontSize: 12, color: "var(--muted)" }}>
              Chargement…
            </span>
          </div>
        ) : !filteredCases.length ? (
          <div className="fx-panel-body">
            <div className="fx-notice">
              <span className="glyph">⚠</span>
              <div>
                <div className="nt">Aucun cas sanctions/PEP</div>
                <p className="nb">
                  Lancer le détecteur côté Streamlit (page Sanctions &amp; PEP legacy) pour
                  alimenter cette vue.
                </p>
              </div>
            </div>
          </div>
        ) : (
          <CasesTable rows={filteredCases} />
        )}
      </div>

      <div className="fx-panel">
        <div className="fx-panel-head">
          <h2>Sources actives</h2>
          <span className="glyph">◷</span>
        </div>
        <div className="fx-table-wrap">
          <table className="fx-table">
            <thead>
              <tr>
                <th>Source</th>
                <th>URL</th>
                <th>Licence</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="key">OpenSanctions Yente</td>
                <td className="fx-mono" style={{ fontSize: 11 }}>
                  api.opensanctions.org/match/sanctions
                </td>
                <td>CC-BY 4.0</td>
              </tr>
              <tr>
                <td className="key">UE consolidée</td>
                <td className="fx-mono" style={{ fontSize: 11 }}>
                  via Yente
                </td>
                <td>EU Open Data</td>
              </tr>
              <tr>
                <td className="key">OFAC SDN</td>
                <td className="fx-mono" style={{ fontSize: 11 }}>
                  via Yente
                </td>
                <td>US Public Domain</td>
              </tr>
              <tr>
                <td className="key">Snapshot local CSV</td>
                <td className="fx-mono" style={{ fontSize: 11 }}>
                  data/sanctions/snapshot_*.csv
                </td>
                <td>fallback démo</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div className="fx-panel-body">
          <a
            href="https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/blob/main/docs/sources_de_donnees.md"
            target="_blank"
            rel="noreferrer"
            className="fx-btn-ghost sm"
          >
            § Voir docs/sources_de_donnees.md ↗
          </a>
        </div>
      </div>
    </ForensicPage>
  );
}

function CasesTable({ rows }: { rows: CaseOutV1[] }) {
  return (
    <div className="fx-table-wrap">
      <table className="fx-table">
        <thead>
          <tr>
            <th>Vendor</th>
            <th>Titre</th>
            <th>Sévérité</th>
            <th className="num">Exposition</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((c) => (
            <tr key={c.case_id}>
              <td>
                {c.vendor_id ? (
                  <Link
                    href={`/vendors/${encodeURIComponent(c.vendor_id)}`}
                    className="fx-link"
                  >
                    {c.vendor_id}
                  </Link>
                ) : (
                  <span style={{ color: "var(--dim)" }}>—</span>
                )}
              </td>
              <td>{c.title}</td>
              <td>
                <SeverityBadge value={c.severity} />
              </td>
              <td className="num">{formatEur(c.exposure_eur)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
