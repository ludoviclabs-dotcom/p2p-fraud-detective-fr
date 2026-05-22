import Link from "next/link";

import { getP2PDataset } from "@/data/get-dataset";
import { CaseWorkflowStatusBadge } from "@/components/case-workflow-status-badge";
import { SeverityBadge } from "@/components/ui/badge";
import { formatEuro, formatNumber } from "@/lib/p2p-demo-format";
import { getSignalLabel, SEVERITY_ORDER } from "@/lib/p2p-demo-taxonomy";
import { case360Href, getScenarioForP2PFindingSignal } from "@/lib/risk/case-links";
import { ForensicPage } from "@/components/forensic-page";

export default function ScoreIndexPage() {
  const dataset = getP2PDataset();
  const findings = [...dataset.findings]
    .sort(
      (a, b) =>
        SEVERITY_ORDER[b.severity] - SEVERITY_ORDER[a.severity] ||
        b.riskScore - a.riskScore ||
        b.exposureEur - a.exposureEur,
    )
    .slice(0, 80);

  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Detection</div>
          <h1 style={{ marginTop: 9 }}>
            Explorateur de <span className="italic">score</span>
          </h1>
          <p className="sub">
            File statique des invoices les plus risquées. Chaque score ouvre le contexte preuve,
            fournisseur et graphe associé.
          </p>
        </div>
        <div className="fx-head-actions">
          <Link href="/rings" className="fx-btn">
            Explorer le graphe <span>↗</span>
          </Link>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3" style={{ marginBottom: 24 }}>
        <div className="fx-stat info">
          <div className="fx-stat-top">
            <span className="glyph">▣</span>
          </div>
          <div className="lbl">Findings</div>
          <div className="val">{formatNumber(dataset.metrics.findingCount)}</div>
        </div>
        <div className="fx-stat risk">
          <div className="fx-stat-top">
            <span className="glyph">▲</span>
          </div>
          <div className="lbl">Critical</div>
          <div className="val">{formatNumber(dataset.metrics.criticalFindings)}</div>
        </div>
        <div className="fx-stat warn">
          <div className="fx-stat-top">
            <span className="glyph">Σ</span>
          </div>
          <div className="lbl">Exposition</div>
          <div className="val">{formatEuro(dataset.metrics.exposureEur)}</div>
        </div>
      </div>

      <div className="fx-panel">
        <div className="fx-panel-head">
          <h2>Scores prioritaires</h2>
          <span className="glyph">◇</span>
        </div>
        <div className="fx-table-wrap">
          <table data-testid="score-index-table" className="fx-table">
            <thead>
              <tr>
                <th>Invoice</th>
                <th>Fournisseur</th>
                <th>Signal</th>
                <th>Sévérité</th>
                <th>Workflow</th>
                <th>Case 360</th>
                <th className="num">Score</th>
                <th className="num">Exposition</th>
              </tr>
            </thead>
            <tbody>
              {findings.map((finding) => {
                const case360Scenario = getScenarioForP2PFindingSignal(finding.signal);
                return (
                  <tr key={finding.id}>
                    <td className="key">
                      <Link href={`/score/${finding.invoiceId}`} className="fx-link">
                        {finding.invoiceId}
                      </Link>
                    </td>
                    <td>
                      <Link href={`/vendors/${finding.vendorId}`} className="fx-link">
                        {finding.vendorName}
                      </Link>
                    </td>
                    <td>{getSignalLabel(finding.signal)}</td>
                    <td>
                      <SeverityBadge value={finding.severity} />
                    </td>
                    <td>
                      <CaseWorkflowStatusBadge caseIds={[`case:${finding.id}`]} />
                    </td>
                    <td>
                      <Link
                        href={case360Href(case360Scenario.caseId)}
                        className="fx-link"
                        data-testid="score-case-360-link"
                      >
                        {case360Scenario.shortTitle}
                      </Link>
                    </td>
                    <td className="num">{finding.riskScore}/100</td>
                    <td className="num">{formatEuro(finding.exposureEur)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="fx-card" style={{ marginTop: 16 }}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <span className="fx-mono" style={{ fontSize: 12, color: "var(--fg-2)" }}>
            § Le score détaillé reste relié au graphe d&apos;investigation.
          </span>
          <Link href="/rings" className="fx-link">
            Voir les anneaux →
          </Link>
        </div>
      </div>
    </ForensicPage>
  );
}
