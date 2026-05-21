import Link from "next/link";

import { GraphExplorer } from "@/components/p2p-graph-explorer";
import { getP2PDataset } from "@/data/get-dataset";
import { formatDate, formatEuro, formatNumber } from "@/lib/p2p-demo-format";
import { SEVERITY_COLORS } from "@/lib/p2p-demo-taxonomy";
import { case360Href, getPrimaryCase360Scenario } from "@/lib/risk/case-links";
import { ForensicPage } from "@/components/forensic-page";

export default function RingsPage() {
  const dataset = getP2PDataset();
  const primaryCase = getPrimaryCase360Scenario();

  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Détection ML · démo statique</div>
          <h1 style={{ marginTop: 9 }}>
            Anneaux de <span className="italic">fraude</span>
          </h1>
          <p className="sub">
            Graphe vendor ↔ IBAN ↔ finding généré depuis le détecteur Python NetworkX. Les IBAN
            sont masqués avant publication ; la page reste utilisable sur Vercel sans backend
            FastAPI.
          </p>
        </div>
        <div className="fx-head-actions">
          <Link href={case360Href(primaryCase.caseId)} className="fx-btn">
            Ouvrir Case 360 <span>↗</span>
          </Link>
        </div>
      </div>

      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-body">
          <div className="grid gap-4 md:grid-cols-5">
            <Metric label="Généré le" value={formatDate(dataset.generatedAt)} />
            <Metric label="Nœuds" value={formatNumber(dataset.nodes.length)} />
            <Metric label="Liens" value={formatNumber(dataset.edges.length)} />
            <Metric label="Findings" value={formatNumber(dataset.findings.length)} />
            <Metric label="Exposition" value={formatEuro(dataset.metrics.exposureEur)} />
          </div>
        </div>
      </div>

      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <h2>Graphe interactif WebGL</h2>
          <span className="glyph">◫</span>
        </div>
        <div style={{ overflow: "hidden" }}>
          <GraphExplorer dataset={dataset} />
        </div>
      </div>

      <div className="fx-panel">
        <div className="fx-panel-head">
          <h2>Légende</h2>
          <span className="glyph">§</span>
        </div>
        <div className="fx-panel-body">
          <div className="flex flex-wrap gap-5">
            <LegendItem color="var(--info)" label="Fournisseur (vendor_name)" />
            <LegendItem color="var(--fg-2)" label="IBAN masqué" />
            {(["critical", "high", "medium"] as const).map((level) => (
              <LegendItem
                key={level}
                color={SEVERITY_COLORS[level]}
                label={`Finding ${level}`}
              />
            ))}
          </div>
        </div>
      </div>
    </ForensicPage>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="fx-eyebrow">{label}</div>
      <div
        className="fx-mono"
        style={{ marginTop: 6, fontSize: 14, fontWeight: 600, color: "var(--fg)" }}
      >
        {value}
      </div>
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <span
        style={{
          display: "inline-block",
          width: 10,
          height: 10,
          borderRadius: "50%",
          background: color,
          flexShrink: 0,
        }}
      />
      <span className="fx-mono" style={{ fontSize: 12, color: "var(--fg-2)" }}>
        {label}
      </span>
    </div>
  );
}
