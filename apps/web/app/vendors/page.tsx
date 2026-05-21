import Link from "next/link";

import { getP2PDataset } from "@/data/get-dataset";
import { CaseWorkflowStatusBadge } from "@/components/case-workflow-status-badge";
import { SeverityBadge } from "@/components/ui/badge";
import { formatEuro, formatNumber } from "@/lib/p2p-demo-format";
import { SEVERITY_ORDER } from "@/lib/p2p-demo-taxonomy";
import { ForensicPage } from "@/components/forensic-page";

export default function VendorsIndexPage() {
  const dataset = getP2PDataset();
  const vendors = [...dataset.vendors]
    .sort(
      (a, b) =>
        SEVERITY_ORDER[b.severity] - SEVERITY_ORDER[a.severity] ||
        b.exposureEur - a.exposureEur ||
        b.riskScore - a.riskScore,
    )
    .slice(0, 80);

  const criticalVendors = dataset.vendors.filter(
    (vendor) => vendor.severity === "critical",
  ).length;

  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Investigation</div>
          <h1 style={{ marginTop: 9 }}>
            Fournisseurs <span className="italic">exposés</span>
          </h1>
          <p className="sub">
            Index statique issu du dataset de démonstration. Chaque ligne ouvre une fiche
            fournisseur 360 connectée aux findings et au graphe.
          </p>
        </div>
        <div className="fx-head-actions">
          <Link href="/rings" className="fx-btn">
            Explorer le graphe <span>↗</span>
          </Link>
        </div>
      </div>

      <div className="mb-6 grid gap-4 md:grid-cols-3">
        <div className="fx-stat info">
          <div className="fx-stat-top">
            <span className="glyph">▣</span>
          </div>
          <div className="lbl">Fournisseurs</div>
          <div className="val">{formatNumber(dataset.metrics.vendorCount)}</div>
        </div>
        <div className="fx-stat risk">
          <div className="fx-stat-top">
            <span className="glyph">▲</span>
          </div>
          <div className="lbl">Critical</div>
          <div className="val">{formatNumber(criticalVendors)}</div>
        </div>
        <div className="fx-stat warn">
          <div className="fx-stat-top">
            <span className="glyph">Σ</span>
          </div>
          <div className="lbl">Exposition graphe</div>
          <div className="val">{formatEuro(dataset.metrics.exposureEur)}</div>
        </div>
      </div>

      <div className="fx-panel">
        <div className="fx-panel-head">
          <div>
            <h2>Top fournisseurs à investiguer</h2>
          </div>
          <span className="glyph">◫</span>
        </div>
        <div className="fx-table-wrap">
          <table className="fx-table">
            <thead>
              <tr>
                <th>Fournisseur</th>
                <th>SIREN</th>
                <th>Sévérité</th>
                <th>Workflow</th>
                <th className="num">Score</th>
                <th className="num">Findings</th>
                <th className="num">Exposition</th>
              </tr>
            </thead>
            <tbody>
              {vendors.map((vendor) => (
                <tr key={vendor.id}>
                  <td>
                    <Link href={`/vendors/${vendor.vendorId}`} className="fx-link">
                      {vendor.name}
                    </Link>
                    <div
                      className="fx-mono"
                      style={{ fontSize: 11, color: "var(--muted)", marginTop: 3 }}
                    >
                      {vendor.vendorId}
                    </div>
                  </td>
                  <td className="key fx-mono" style={{ fontSize: 11 }}>
                    {vendor.siren ?? <span style={{ color: "var(--dim)" }}>—</span>}
                  </td>
                  <td>
                    <SeverityBadge value={vendor.severity} />
                  </td>
                  <td>
                    <CaseWorkflowStatusBadge
                      caseIds={vendor.findingIds.map((id) => `case:${id}`)}
                      vendorId={vendor.vendorId}
                    />
                  </td>
                  <td className="num">{vendor.riskScore}/100</td>
                  <td className="num">{vendor.findingIds.length}</td>
                  <td className="num">{formatEuro(vendor.exposureEur)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </ForensicPage>
  );
}
