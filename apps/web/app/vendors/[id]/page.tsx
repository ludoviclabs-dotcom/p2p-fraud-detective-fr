import Link from "next/link";
import type { ReactNode } from "react";

import { getP2PDataset, getVendor, getVendorFindings } from "@/data/get-dataset";
import { CaseWorkflowPanel } from "@/components/case-workflow-panel";
import { SeverityBadge } from "@/components/ui/badge";
import { formatEuro, formatNumber } from "@/lib/p2p-demo-format";
import { getSignalLabel, SEVERITY_ORDER } from "@/lib/p2p-demo-taxonomy";
import { ForensicPage } from "@/components/forensic-page";

export default async function VendorDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const vendor = getVendor(id);
  if (!vendor) return <UnknownVendorDetail requestedId={id} />;

  const dataset = getP2PDataset();
  const findings = getVendorFindings(id);
  const signalCounts = findings.reduce<Record<string, number>>((counts, finding) => {
    counts[finding.signal] = (counts[finding.signal] ?? 0) + 1;
    return counts;
  }, {});

  const ibanConnections = dataset.edges
    .filter((edge) => edge.kind === "uses_iban" && edge.source === vendor.id)
    .map((edge) => {
      const node = dataset.nodes.find((item) => item.id === edge.target);
      return node ? { edge, node } : null;
    })
    .filter((item): item is NonNullable<typeof item> => Boolean(item))
    .sort((a, b) => b.edge.findingIds.length - a.edge.findingIds.length);

  const topFindings = findings.slice(0, 12);
  const leadFinding = topFindings[0];
  const findingTotal = findings.length;
  const criticalOrHigh = findings.filter(
    (finding) => SEVERITY_ORDER[finding.severity] >= SEVERITY_ORDER.high,
  ).length;

  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Fiche fournisseur 360</div>
          <h1 style={{ marginTop: 9 }}>{vendor.name}</h1>
          <div style={{ marginTop: 10, display: "flex", flexWrap: "wrap", gap: 16 }}>
            <span className="fx-mono" style={{ fontSize: 12, color: "var(--muted)" }}>
              {vendor.vendorId}
            </span>
            {vendor.siren ? (
              <span className="fx-mono" style={{ fontSize: 12, color: "var(--muted)" }}>
                SIREN {vendor.siren}
              </span>
            ) : null}
            {vendor.apeCode ? (
              <span className="fx-mono" style={{ fontSize: 12, color: "var(--muted)" }}>
                APE {vendor.apeCode}
              </span>
            ) : null}
          </div>
        </div>
        <div className="fx-head-actions">
          <Link href="/rings" className="fx-btn-ghost sm">
            ← Retour au graphe
          </Link>
          <Link href="/vendors" className="fx-btn-ghost sm">
            Liste fournisseurs
          </Link>
          <SeverityBadge value={vendor.severity} />
          <span
            className="fx-mono"
            style={{
              fontSize: 12,
              color: "var(--fg)",
              background: "var(--panel-2)",
              border: "1px solid var(--border)",
              padding: "6px 12px",
            }}
          >
            Score {vendor.riskScore}/100
          </span>
        </div>
      </div>

      <div className="mb-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard glyph="Σ" label="Exposition" value={formatEuro(vendor.exposureEur)} />
        <KpiCard glyph="§" label="Findings" value={formatNumber(findingTotal)} />
        <KpiCard glyph="▲" label="Critical / high" value={formatNumber(criticalOrHigh)} />
        <KpiCard glyph="∿" label="IBAN connectés" value={formatNumber(ibanConnections.length)} />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="fx-panel">
          <div className="fx-panel-head">
            <h2>Findings reliés au fournisseur</h2>
            <span className="glyph">§</span>
          </div>
          <div className="fx-table-wrap">
            <table data-testid="vendor-findings-table" className="fx-table">
              <thead>
                <tr>
                  <th>Invoice</th>
                  <th>Signal</th>
                  <th>Sévérité</th>
                  <th className="num">Score</th>
                  <th className="num">Exposition</th>
                  <th className="num">Action</th>
                </tr>
              </thead>
              <tbody>
                {topFindings.map((finding) => (
                  <tr key={finding.id}>
                    <td className="key fx-mono" style={{ fontSize: 11 }}>
                      {finding.invoiceId}
                    </td>
                    <td>{getSignalLabel(finding.signal)}</td>
                    <td>
                      <SeverityBadge value={finding.severity} />
                    </td>
                    <td className="num">{finding.riskScore}/100</td>
                    <td className="num">{formatEuro(finding.exposureEur)}</td>
                    <td className="num">
                      <Link
                        href={`/score/${finding.invoiceId}`}
                        className="fx-link"
                      >
                        Ouvrir ↗
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <aside className="space-y-5">
          {leadFinding ? (
            <CaseWorkflowPanel
              compact
              context={{
                id: `case:${leadFinding.id}`,
                findingId: leadFinding.id,
                invoiceId: leadFinding.invoiceId,
                vendorId: vendor.vendorId,
                vendorName: vendor.name,
                ruleId: leadFinding.ruleId,
                signal: leadFinding.signal,
                severity: leadFinding.severity,
                exposureEur: leadFinding.exposureEur,
                riskScore: leadFinding.riskScore,
              }}
            />
          ) : null}

          <div className="fx-panel">
            <div className="fx-panel-head">
              <h2>Breakdown signaux</h2>
              <span className="glyph">∿</span>
            </div>
            <div
              className="fx-panel-body space-y-3"
              data-testid="vendor-signal-breakdown"
            >
              {Object.entries(signalCounts)
                .sort((a, b) => b[1] - a[1])
                .map(([signal, count]) => (
                  <div key={signal}>
                    <div className="flex items-center justify-between gap-3">
                      <span style={{ fontSize: 13, color: "var(--fg)" }}>
                        {getSignalLabel(signal)}
                      </span>
                      <span
                        className="fx-mono"
                        style={{ fontSize: 11, color: "var(--muted)" }}
                      >
                        {count}
                      </span>
                    </div>
                    <div className="fx-bar" style={{ marginTop: 6 }}>
                      <i
                        style={{
                          width: `${Math.max((count / Math.max(findingTotal, 1)) * 100, 8)}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
            </div>
          </div>

          <div className="fx-panel">
            <div className="fx-panel-head">
              <h2>Connexions IBAN</h2>
              <span className="glyph">◇</span>
            </div>
            <div
              className="fx-panel-body space-y-3"
              data-testid="vendor-iban-connections"
            >
              {ibanConnections.length ? (
                ibanConnections.slice(0, 8).map(({ edge, node }) => (
                  <div
                    key={`${edge.source}-${edge.target}`}
                    className="fx-card"
                    style={{ padding: "10px 14px" }}
                  >
                    <div
                      className="fx-mono"
                      style={{ fontSize: 12, color: "var(--fg)" }}
                    >
                      {node.maskedValue ?? node.label}
                    </div>
                    <div
                      className="fx-mono"
                      style={{ fontSize: 11, color: "var(--muted)", marginTop: 4 }}
                    >
                      {edge.findingIds.length} finding(s) associé(s)
                    </div>
                  </div>
                ))
              ) : (
                <p
                  className="fx-mono"
                  style={{ fontSize: 12, color: "var(--muted)" }}
                >
                  Aucune connexion IBAN directe.
                </p>
              )}
            </div>
          </div>

          <div className="fx-card-accent">
            <div className="fx-eyebrow">Décision audit</div>
            <p
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: 13,
                lineHeight: 1.6,
                color: "var(--fg-2)",
                marginTop: 10,
              }}
            >
              Priorité à la revue des invoices critical/high, puis validation du RIB et
              recherche de fournisseurs partageant les mêmes coordonnées bancaires.
            </p>
            <div style={{ marginTop: 14 }}>
              <Link href="/rings" className="fx-btn sm">
                Revenir au graphe ↗
              </Link>
            </div>
          </div>
        </aside>
      </div>
    </ForensicPage>
  );
}

function UnknownVendorDetail({ requestedId }: { requestedId: string }) {
  const dataset = getP2PDataset();
  const fallbackVendors = [...dataset.vendors]
    .sort((left, right) => right.riskScore - left.riskScore)
    .slice(0, 3);

  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Fiche fournisseur 360</div>
          <h1 style={{ marginTop: 9 }}>
            Fournisseur synthétique <span className="italic">non chargé</span>
          </h1>
        </div>
        <div className="fx-head-actions">
          <Link href="/sandbox" className="fx-btn-ghost sm">
            ← Retour à la démo
          </Link>
        </div>
      </div>

      <div className="fx-notice" style={{ marginBottom: 24 }}>
        <span className="glyph">⚠</span>
        <div>
          <div className="nt">Identifiant non reconnu</div>
          <p className="nb">
            L&apos;identifiant{" "}
            <span className="fx-mono" style={{ color: "var(--fg)" }}>
              {requestedId}
            </span>{" "}
            vient probablement d&apos;un scénario backend ou d&apos;une ancienne démo. La route reste
            volontairement accessible pour préserver le parcours, mais seules les fiches
            synthétiques ci-dessous contiennent des données complètes.
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3" style={{ marginBottom: 24 }}>
        {fallbackVendors.map((vendor) => (
          <Link
            key={vendor.vendorId}
            href={`/vendors/${encodeURIComponent(vendor.vendorId)}`}
            className="fx-panel"
            style={{ display: "block", textDecoration: "none", padding: "20px" }}
          >
            <SeverityBadge value={vendor.severity} />
            <div
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 18,
                color: "var(--fg)",
                marginTop: 12,
              }}
            >
              {vendor.name}
            </div>
            <div
              className="fx-mono"
              style={{ fontSize: 11, color: "var(--muted)", marginTop: 4 }}
            >
              {vendor.vendorId}
            </div>
            <div
              className="fx-mono"
              style={{ fontSize: 11, color: "var(--fg-2)", marginTop: 10 }}
            >
              Score {vendor.riskScore}/100 · {formatEuro(vendor.exposureEur)}
            </div>
          </Link>
        ))}
      </div>

      <div className="flex flex-wrap gap-3">
        <Link href="/p2p-scenarios" className="fx-btn">
          Tester les scénarios P2P ↗
        </Link>
        <Link href="/risk-docs" className="fx-btn-ghost">
          Lire les limites de démo
        </Link>
      </div>
    </ForensicPage>
  );
}

function KpiCard({
  glyph,
  label,
  value,
}: {
  glyph: ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="fx-stat">
      <div className="fx-stat-top">
        <span className="glyph">{glyph}</span>
      </div>
      <div className="lbl">{label}</div>
      <div className="val">{value}</div>
    </div>
  );
}
