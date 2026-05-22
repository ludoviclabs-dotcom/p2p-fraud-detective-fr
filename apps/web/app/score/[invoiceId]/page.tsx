import Link from "next/link";
import { notFound } from "next/navigation";

import { getFinding, getFindingContext, getFindingVendor } from "@/data/get-dataset";
import { CaseWorkflowPanel } from "@/components/case-workflow-panel";
import { SeverityBadge } from "@/components/ui/badge";
import { formatEuro, formatNumber } from "@/lib/p2p-demo-format";
import { getSignalLabel } from "@/lib/p2p-demo-taxonomy";
import { case360Href, getScenarioForP2PFindingSignal } from "@/lib/risk/case-links";
import { ForensicPage } from "@/components/forensic-page";

export default async function ScoreDetailPage({
  params,
}: {
  params: Promise<{ invoiceId: string }>;
}) {
  const { invoiceId } = await params;
  const finding = getFinding(invoiceId);
  if (!finding) notFound();

  const vendor = getFindingVendor(finding);
  const context = getFindingContext(finding.id);
  const ibanNodes = context.nodes.filter((node) => node.kind === "iban");
  const vendorNodes = context.nodes.filter((node) => node.kind === "vendor");
  const case360Scenario = getScenarioForP2PFindingSignal(finding.signal);

  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <Link href="/rings" className="fx-link" style={{ marginBottom: 12, display: "inline-flex" }}>
            ← Retour au graphe
          </Link>
          <div className="fx-eyebrow" style={{ marginTop: 8 }}>Score investigation</div>
          <h1 style={{ marginTop: 9 }}>{finding.invoiceId}</h1>
          <p className="sub">
            {getSignalLabel(finding.signal)} — {finding.ruleId}
          </p>
        </div>
        <div className="fx-head-actions">
          <Link href={case360Href(case360Scenario.caseId)} className="fx-btn">
            Ouvrir Case 360 <span>↗</span>
          </Link>
          <SeverityBadge value={finding.severity} />
          <span
            className="fx-mono"
            style={{
              background: "var(--panel-2)",
              border: "1px solid var(--border)",
              padding: "8px 14px",
              fontSize: 13,
              color: "var(--fg)",
            }}
          >
            {finding.riskScore}/100
          </span>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4" style={{ marginBottom: 20 }}>
        <div className="fx-stat info">
          <div className="fx-stat-top"><span className="glyph">Σ</span></div>
          <div className="lbl">Exposition</div>
          <div className="val">{formatEuro(finding.exposureEur)}</div>
        </div>
        <div className="fx-stat warn">
          <div className="fx-stat-top"><span className="glyph">§</span></div>
          <div className="lbl">Rule</div>
          <div className="val" style={{ fontSize: 18 }}>{finding.ruleId}</div>
        </div>
        <div className="fx-stat ok">
          <div className="fx-stat-top"><span className="glyph">◫</span></div>
          <div className="lbl">Nœuds liés</div>
          <div className="val">{formatNumber(context.nodes.length)}</div>
        </div>
        <div className="fx-stat risk">
          <div className="fx-stat-top"><span className="glyph">▲</span></div>
          <div className="lbl">Findings connexes</div>
          <div className="val">{formatNumber(context.relatedFindings.length)}</div>
        </div>
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-5">
          <div className="fx-panel">
            <div className="fx-panel-head">
              <h2>Preuve exploitable</h2>
              <span className="glyph">□</span>
            </div>
            <div className="fx-panel-body">
              <dl className="grid gap-4 md:grid-cols-2">
                {Object.entries(finding.evidence).map(([key, value]) => (
                  <div
                    key={key}
                    style={{
                      background: "var(--bg-2)",
                      border: "1px solid var(--border)",
                      padding: "14px 16px",
                    }}
                  >
                    <dt className="fx-eyebrow">{key}</dt>
                    <dd
                      className="fx-mono"
                      style={{ marginTop: 8, fontSize: 13, color: "var(--fg)" }}
                    >
                      {renderEvidenceValue(value)}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          </div>

          <div className="fx-panel">
            <div className="fx-panel-head">
              <h2>Findings connexes dans le graphe</h2>
              <span className="glyph">◇</span>
            </div>
            <div className="fx-table-wrap">
              <table className="fx-table">
                <thead>
                  <tr>
                    <th>Invoice</th>
                    <th>Signal</th>
                    <th>Sévérité</th>
                    <th className="num">Exposition</th>
                  </tr>
                </thead>
                <tbody>
                  {context.relatedFindings.slice(0, 10).map((item) => (
                    <tr key={item.id}>
                      <td className="key">
                        <Link href={`/score/${item.invoiceId}`} className="fx-link">
                          {item.invoiceId}
                        </Link>
                      </td>
                      <td>{getSignalLabel(item.signal)}</td>
                      <td>
                        <SeverityBadge value={item.severity} />
                      </td>
                      <td className="num">{formatEuro(item.exposureEur)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <aside className="space-y-5">
          <CaseWorkflowPanel
            compact
            context={{
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
            }}
          />

          <div className="fx-panel">
            <div className="fx-panel-head">
              <h2>Fournisseur</h2>
              <span className="glyph">★</span>
            </div>
            <div className="fx-panel-body space-y-3">
              <div>
                <div
                  className="fx-mono"
                  style={{ fontSize: 14, fontWeight: 600, color: "var(--fg)" }}
                >
                  {finding.vendorName}
                </div>
                <div className="fx-mono" style={{ marginTop: 4, fontSize: 11, color: "var(--muted)" }}>
                  {finding.vendorId}
                </div>
              </div>
              {vendor ? (
                <>
                  <div className="grid grid-cols-2 gap-3">
                    <div
                      style={{
                        background: "var(--bg-2)",
                        border: "1px solid var(--border)",
                        padding: "11px 13px",
                      }}
                    >
                      <div className="fx-eyebrow">SIREN</div>
                      <div className="fx-mono" style={{ marginTop: 5, fontSize: 13, color: "var(--fg)" }}>
                        {vendor.siren ?? "-"}
                      </div>
                    </div>
                    <div
                      style={{
                        background: "var(--bg-2)",
                        border: "1px solid var(--border)",
                        padding: "11px 13px",
                      }}
                    >
                      <div className="fx-eyebrow">Score</div>
                      <div className="fx-mono" style={{ marginTop: 5, fontSize: 13, color: "var(--fg)" }}>
                        {vendor.riskScore}/100
                      </div>
                    </div>
                  </div>
                  <Link href={`/vendors/${vendor.vendorId}`} className="fx-btn sm">
                    Ouvrir la fiche <span>↗</span>
                  </Link>
                </>
              ) : null}
            </div>
          </div>

          <div className="fx-panel">
            <div className="fx-panel-head">
              <h2>Contexte graphe</h2>
              <span className="glyph">◫</span>
            </div>
            <div className="fx-panel-body space-y-4">
              <GraphNodeList
                title="IBAN masqués"
                items={ibanNodes.map((node) => node.maskedValue ?? node.label)}
              />
              <GraphNodeList
                title="Fournisseurs reliés"
                items={vendorNodes.map((node) => node.label)}
              />
            </div>
          </div>

          <div className="fx-panel">
            <div className="fx-panel-head">
              <h2>Case 360 recommandé</h2>
              <span className="glyph">◎</span>
            </div>
            <div className="fx-panel-body">
              <div className="fx-eyebrow">{case360Scenario.caseId}</div>
              <p className="fx-mono" style={{ marginTop: 8, fontSize: 12, lineHeight: 1.65, color: "var(--muted)" }}>
                {case360Scenario.description}
              </p>
              <Link href={case360Href(case360Scenario.caseId)} className="fx-link" style={{ marginTop: 14 }}>
                Voir la timeline, les reason codes et l’Evidence Pack →
              </Link>
            </div>
          </div>

          <div className="fx-panel">
            <div className="fx-panel-head">
              <h2>Prochaine action</h2>
              <span className="glyph">▣</span>
            </div>
            <div className="fx-panel-body">
              <p
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 12,
                  lineHeight: 1.65,
                  color: "var(--muted)",
                }}
              >
                Valider la pièce source, vérifier l&apos;IBAN masqué, puis rattacher la
                conclusion à la fiche fournisseur avant export audit.
              </p>
              <Link
                href="/exports"
                className="fx-link"
                data-testid="score-detail-export-link"
                style={{ marginTop: 14 }}
              >
                Préparer l&apos;export →
              </Link>
            </div>
          </div>
        </aside>
      </div>
    </ForensicPage>
  );
}

function renderEvidenceValue(value: unknown): string {
  if (Array.isArray(value)) return value.join(", ");
  if (value && typeof value === "object") return JSON.stringify(value);
  return String(value ?? "-");
}

function GraphNodeList({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <div className="fx-eyebrow">{title}</div>
      {items.length ? (
        <div className="mt-2 space-y-2">
          {items.slice(0, 8).map((item) => (
            <div
              key={item}
              className="fx-mono"
              style={{
                background: "var(--bg-2)",
                border: "1px solid var(--border)",
                padding: "8px 12px",
                fontSize: 11,
                color: "var(--fg)",
              }}
            >
              {item}
            </div>
          ))}
        </div>
      ) : (
        <p
          className="fx-mono"
          style={{ marginTop: 8, fontSize: 12, color: "var(--muted)" }}
        >
          Aucun nœud direct.
        </p>
      )}
    </div>
  );
}
