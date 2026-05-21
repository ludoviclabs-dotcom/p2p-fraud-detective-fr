import Link from "next/link";

import { CaseWorkflowExport } from "@/components/case-workflow-export";
import { getP2PDataset } from "@/data/get-dataset";
import { SEVERITY_ORDER } from "@/lib/p2p-demo-taxonomy";
import { ForensicPage } from "@/components/forensic-page";

export default function ExportsPage() {
  const dataset = getP2PDataset();
  const suggestedCases = [...dataset.findings]
    .sort(
      (a, b) =>
        SEVERITY_ORDER[b.severity] - SEVERITY_ORDER[a.severity] ||
        b.riskScore - a.riskScore ||
        b.exposureEur - a.exposureEur,
    )
    .slice(0, 40)
    .map((finding) => ({
      id: `case:${finding.id}`,
      findingId: finding.id,
      invoiceId: finding.invoiceId,
      vendorId: finding.vendorId,
      vendorName: finding.vendorName,
      ruleId: finding.ruleId,
      signal: finding.signal,
      severity: finding.severity,
      exposureEur: finding.exposureEur,
      riskScore: finding.riskScore,
    }));

  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Audit trail</div>
          <h1 style={{ marginTop: 9 }}>
            Registre et <span className="italic">exports</span>
          </h1>
          <p className="sub">
            Qualification locale des cas P2P : statut, décision, responsable,
            note d&apos;investigation et export CSV/JSON. La V1 reste statique
            et compatible Vercel ; une API FastAPI pourra reprendre ce contrat
            plus tard.
          </p>
        </div>
        <div className="fx-head-actions">
          <Link href="/score" className="fx-btn">
            Ouvrir les scores <span>↗</span>
          </Link>
        </div>
      </div>

      <section className="mt-4 grid gap-3 md:grid-cols-4" style={{ marginBottom: 24 }}>
        {[
          ["1", "Dashboard", "/dashboard"],
          ["2", "Graphe rings", "/rings"],
          ["3", "Score détaillé", "/score"],
          ["4", "Export audit", "/exports"],
        ].map(([step, label, href]) => (
          <Link
            key={step}
            href={href}
            className="fx-card"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 12,
              textDecoration: "none",
              minHeight: 64,
            }}
          >
            <span
              style={{ display: "flex", alignItems: "center", gap: 12 }}
            >
              <span
                className="fx-mono"
                style={{
                  width: 24,
                  height: 24,
                  display: "grid",
                  placeItems: "center",
                  border: "1px solid var(--border-strong)",
                  fontSize: 11,
                  color: "var(--risk)",
                  flexShrink: 0,
                }}
              >
                {step}
              </span>
              <span
                className="fx-mono"
                style={{ fontSize: 12, color: "var(--fg)", letterSpacing: "0.02em" }}
              >
                {label}
              </span>
            </span>
            <span
              className="fx-mono"
              style={{ fontSize: 11, color: "var(--muted)" }}
            >
              →
            </span>
          </Link>
        ))}
      </section>

      <div>
        <CaseWorkflowExport suggestedCases={suggestedCases} />
      </div>
    </ForensicPage>
  );
}
