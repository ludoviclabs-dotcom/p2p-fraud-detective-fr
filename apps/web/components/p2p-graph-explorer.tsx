"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";

import { formatEuro, formatNumber } from "@/lib/p2p-demo-format";
import {
  getSignalLabel,
  SEVERITY_COLORS,
  SEVERITY_ORDER,
  SIGNAL_ORDER,
} from "@/lib/p2p-demo-taxonomy";
import { case360Href, getScenarioForP2PFindingSignal } from "@/lib/risk/case-links";
import type { GraphNode, P2PDemoDataset, Severity } from "@/types/p2p";

const NODE_COLORS = {
  vendor: "#1F3A6E",
  iban: "#3E7CB1",
  finding: "#A23E48",
};

const SEVERITY_OPTIONS = [
  { value: "all", label: "Toutes sévérités" },
  { value: "critical", label: "Critical" },
  { value: "high", label: "High et +" },
  { value: "medium", label: "Medium et +" },
];

interface SigmaRenderer {
  kill(): void;
  refresh(): void;
  getCamera(): {
    getState(): { ratio: number };
    setState(state: { ratio: number }): void;
  };
  on(event: "clickNode", callback: (payload: { node: string }) => void): void;
  on(event: "clickStage", callback: () => void): void;
}

function nodeSize(node: GraphNode): number {
  if (node.kind === "finding") return 3 + Math.min(node.riskScore / 34, 4);
  if (node.kind === "iban") return 4 + Math.min(node.riskScore / 24, 4);
  return 6 + Math.min(Math.log10(Math.max(node.exposureEur, 1)) * 1.2, 8);
}

function nodePosition(
  node: GraphNode,
  index: number,
  total: number,
  scale = 1,
): { x: number; y: number } {
  const angle = (index / Math.max(total, 1)) * Math.PI * 2;
  const radius = (node.kind === "vendor" ? 10 : node.kind === "iban" ? 6 : 2.7) * scale;
  const offset = node.kind === "finding" ? 0.35 : node.kind === "iban" ? 0.18 : 0;
  return {
    x: Math.cos(angle + offset) * radius + (node.kind === "vendor" ? 1.5 * scale : 0),
    y: Math.sin(angle + offset) * radius + (node.kind === "finding" ? 0.8 * scale : 0),
  };
}

function severityMatches(severity: Severity, selected: string): boolean {
  if (selected === "all") return true;
  return SEVERITY_ORDER[severity] >= SEVERITY_ORDER[selected as Severity];
}

function selectedNodeSummary(dataset: P2PDemoDataset, node: GraphNode | undefined) {
  if (!node) return null;
  if (node.kind === "finding") {
    const finding = dataset.findings.find((item) => item.id === node.id);
    return { node, finding, vendor: undefined };
  }
  if (node.kind === "vendor") {
    const vendor = dataset.vendors.find((item) => item.id === node.id);
    return { node, finding: undefined, vendor };
  }
  return { node, finding: undefined, vendor: undefined };
}

const selectStyle: React.CSSProperties = {
  height: 36,
  background: "var(--bg)",
  border: "1px solid var(--border)",
  padding: "0 10px",
  fontFamily: "var(--font-mono)",
  fontSize: 11,
  color: "var(--fg)",
  outline: "none",
};

export function GraphExplorer({ dataset }: { dataset: P2PDemoDataset }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [signal, setSignal] = useState("all");
  const [severity, setSeverity] = useState("all");
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [graphError, setGraphError] = useState<string | null>(null);

  const signalOptions = useMemo(() => {
    const availableSignals = new Set(dataset.findings.map((finding) => finding.signal));
    const orderedSignals = SIGNAL_ORDER.filter((value) => availableSignals.delete(value));
    const extraSignals = Array.from(availableSignals).sort();
    return [
      { value: "all", label: "Tous les signaux" },
      ...[...orderedSignals, ...extraSignals].map((value) => ({
        value,
        label: getSignalLabel(value),
      })),
    ];
  }, [dataset.findings]);

  const filtered = useMemo(() => {
    const findingIds = new Set(
      dataset.findings
        .filter((finding) => signal === "all" || finding.signal === signal)
        .filter((finding) => severityMatches(finding.severity, severity))
        .map((finding) => finding.id),
    );
    const nodeIds = new Set<string>();
    const edges = dataset.edges.filter((edge) => {
      const keep = edge.findingIds.some((id) => findingIds.has(id));
      if (keep) {
        nodeIds.add(edge.source);
        nodeIds.add(edge.target);
      }
      return keep;
    });
    const nodes = dataset.nodes.filter((node) => nodeIds.has(node.id) || findingIds.has(node.id));
    return { nodes, edges, findingIds };
  }, [dataset, severity, signal]);

  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;
    container.innerHTML = "";
    let renderer: SigmaRenderer | null = null;
    let cancelled = false;
    setGraphError(null);

    async function mountGraph() {
      await new Promise((resolve) => requestAnimationFrame(resolve));
      if (container.clientHeight === 0) {
        await new Promise((resolve) => setTimeout(resolve, 50));
      }

      const isCompact = container.clientWidth < 640;
      const graphScale = isCompact ? 0.58 : 1;
      const [{ default: Graph }, { default: Sigma }] = await Promise.all([
        import("graphology"),
        import("sigma"),
      ]);
      if (cancelled) return;

      const graph = new Graph();
      const kindTotals = filtered.nodes.reduce<Record<GraphNode["kind"], number>>(
        (totals, node) => {
          totals[node.kind] += 1;
          return totals;
        },
        { vendor: 0, iban: 0, finding: 0 },
      );
      const kindIndexes: Record<GraphNode["kind"], number> = { vendor: 0, iban: 0, finding: 0 };

      filtered.nodes.forEach((node) => {
        const position = nodePosition(
          node,
          kindIndexes[node.kind]++,
          kindTotals[node.kind],
          graphScale,
        );
        graph.addNode(node.id, {
          ...position,
          label: isCompact ? "" : node.label,
          size: nodeSize(node) * (isCompact ? 0.86 : 1),
          color: node.kind === "finding" ? SEVERITY_COLORS[node.severity] : NODE_COLORS[node.kind],
          nodeType: node.kind,
          severity: node.severity,
        });
      });
      filtered.edges.forEach((edge, index) => {
        if (graph.hasNode(edge.source) && graph.hasNode(edge.target)) {
          graph.addEdgeWithKey(
            `${edge.source}-${edge.target}-${index}`,
            edge.source,
            edge.target,
            {
              color:
                edge.kind === "uses_iban"
                  ? "rgba(62, 124, 177, 0.42)"
                  : "rgba(15, 27, 51, 0.24)",
              size: Math.min(1 + edge.weight * 0.2, 4),
            },
          );
        }
      });

      renderer = new Sigma(graph, container, {
        defaultEdgeColor: "rgba(15, 27, 51, 0.18)",
        defaultNodeColor: "#1F3A6E",
        labelColor: { color: "#141927" },
        labelDensity: isCompact ? 0 : 0.04,
        labelGridCellSize: 80,
        labelRenderedSizeThreshold: isCompact ? 100 : 11,
        nodeReducer: (_node: string, data: { label?: string; nodeType?: string }) => ({
          ...data,
          label: data.nodeType === "finding" ? "" : data.label,
        }),
        renderEdgeLabels: false,
        zIndex: true,
      }) as SigmaRenderer;

      if (isCompact) {
        const camera = renderer.getCamera();
        const state = camera.getState();
        camera.setState({ ratio: state.ratio * 1.55 });
        renderer.refresh();
      }

      renderer.on("clickNode", ({ node }) => setSelectedNodeId(node));
      renderer.on("clickStage", () => setSelectedNodeId(null));
    }

    void mountGraph().catch((error: unknown) => {
      console.error("Unable to render P2P graph", error);
      setGraphError(error instanceof Error ? error.message : "Le graphe n'a pas pu etre rendu.");
    });

    return () => {
      cancelled = true;
      renderer?.kill();
    };
  }, [filtered]);

  const selectedNode = dataset.nodes.find((node) => node.id === selectedNodeId);
  const details = selectedNodeSummary(dataset, selectedNode);
  const findingCount = filtered.findingIds.size;
  const priorityNodes = useMemo(
    () =>
      [...filtered.nodes]
        .sort(
          (a, b) =>
            SEVERITY_ORDER[b.severity] - SEVERITY_ORDER[a.severity] ||
            b.riskScore - a.riskScore ||
            b.exposureEur - a.exposureEur,
        )
        .slice(0, 10),
    [filtered.nodes],
  );

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
      {/* Graph panel */}
      <section className="fx-panel overflow-hidden">
        {/* Chrome header */}
        <div className="fx-panel-head flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2>Graphe interactif WebGL</h2>
            <div className="sub">
              {formatNumber(filtered.nodes.length)} nœuds &middot;{" "}
              {formatNumber(filtered.edges.length)} liens &middot;{" "}
              {formatNumber(findingCount)} findings visibles
            </div>
          </div>

          <div className="flex flex-col gap-2 sm:flex-row">
            <label className="sr-only" htmlFor="signal-filter">
              Filtrer par signal
            </label>
            <select
              id="signal-filter"
              value={signal}
              onChange={(event) => setSignal(event.target.value)}
              style={selectStyle}
            >
              {signalOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <label className="sr-only" htmlFor="severity-filter">
              Filtrer par sévérité
            </label>
            <select
              id="severity-filter"
              value={severity}
              onChange={(event) => setSeverity(event.target.value)}
              style={selectStyle}
            >
              {SEVERITY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Graph canvas area */}
        {filtered.nodes.length > 0 ? (
          <div
            className="graph-frame relative"
            data-testid="graph-frame"
            style={{ background: "var(--bg-2)" }}
          >
            <div ref={containerRef} className="h-full w-full" />
            {graphError ? (
              <div
                className="absolute inset-0 grid place-items-center px-6"
                style={{ background: "var(--bg-2)" }}
              >
                <div style={{ textAlign: "center" }}>
                  <span
                    className="fx-mono"
                    style={{ fontSize: 24, color: "var(--muted)", display: "block" }}
                  >
                    ◫
                  </span>
                  <p
                    className="fx-mono"
                    style={{ marginTop: 10, fontSize: 13, color: "var(--fg)" }}
                  >
                    Rendu du graphe indisponible.
                  </p>
                  <p
                    className="fx-mono"
                    style={{ marginTop: 4, fontSize: 11, color: "var(--muted)", maxWidth: 400 }}
                  >
                    {graphError}
                  </p>
                </div>
              </div>
            ) : null}
          </div>
        ) : (
          <div
            className="grid place-items-center px-6"
            style={{ height: 420, background: "var(--bg-2)", textAlign: "center" }}
          >
            <div>
              <span
                className="fx-mono"
                style={{ fontSize: 24, color: "var(--muted)", display: "block" }}
              >
                ◫
              </span>
              <p
                className="fx-mono"
                style={{ marginTop: 10, fontSize: 13, color: "var(--fg)" }}
              >
                Aucun nœud pour ce filtre.
              </p>
              <p
                className="fx-mono"
                style={{ marginTop: 4, fontSize: 11, color: "var(--muted)" }}
              >
                Relâchez la sévérité ou revenez à tous les signaux.
              </p>
            </div>
          </div>
        )}
      </section>

      {/* Right sidebar panels */}
      <aside className="flex flex-col gap-5">
        {/* Legend */}
        <div className="fx-panel">
          <div className="fx-panel-head">
            <h2>Légende</h2>
          </div>
          <div className="fx-panel-body space-y-4">
            <div className="space-y-2">
              <div className="fx-eyebrow">Types de nœuds</div>
              <div className="flex items-center gap-3">
                <span
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: "50%",
                    background: NODE_COLORS.vendor,
                    flexShrink: 0,
                    display: "inline-block",
                  }}
                />
                <span className="fx-mono" style={{ fontSize: 12, color: "var(--fg-2)" }}>
                  Fournisseur
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: "50%",
                    background: NODE_COLORS.iban,
                    flexShrink: 0,
                    display: "inline-block",
                  }}
                />
                <span className="fx-mono" style={{ fontSize: 12, color: "var(--fg-2)" }}>
                  IBAN masqué
                </span>
              </div>
            </div>

            <div
              className="space-y-2"
              style={{ borderTop: "1px solid var(--border)", paddingTop: 14 }}
            >
              <div className="fx-eyebrow">Sévérité des findings</div>
              {(["critical", "high", "medium"] as const).map((level) => (
                <div key={level} className="flex items-center gap-3">
                  <span
                    style={{
                      width: 10,
                      height: 10,
                      borderRadius: "50%",
                      background: SEVERITY_COLORS[level],
                      flexShrink: 0,
                      display: "inline-block",
                    }}
                  />
                  <span
                    className="fx-mono"
                    style={{ fontSize: 12, color: "var(--fg-2)", textTransform: "capitalize" }}
                  >
                    {level}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Priority nodes */}
        <div className="fx-panel">
          <div className="fx-panel-head">
            <h2>Nœuds prioritaires</h2>
          </div>
          <div className="fx-panel-body space-y-2" data-testid="graph-priority-list">
            {priorityNodes.map((node) => (
              <button
                key={node.id}
                type="button"
                onClick={() => setSelectedNodeId(node.id)}
                aria-pressed={selectedNodeId === node.id}
                data-node-kind={node.kind}
                data-testid="priority-node"
                style={{
                  width: "100%",
                  background:
                    selectedNodeId === node.id ? "var(--panel-2)" : "var(--bg)",
                  border: `1px solid ${selectedNodeId === node.id ? "var(--risk)" : "var(--border)"}`,
                  padding: "10px 12px",
                  textAlign: "left",
                  cursor: "pointer",
                  transition: "all .15s",
                }}
              >
                <span className="flex items-center justify-between gap-3">
                  <span
                    className="fx-mono"
                    style={{
                      fontSize: 12,
                      color: "var(--fg)",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {node.label}
                  </span>
                  <span className="fx-mono" style={{ fontSize: 11, color: "var(--muted)", flexShrink: 0 }}>
                    {node.riskScore}/100
                  </span>
                </span>
                <span className="flex items-center justify-between gap-3 mt-1">
                  <span
                    className="fx-mono"
                    style={{ fontSize: 10, color: "var(--muted)", textTransform: "capitalize" }}
                  >
                    {node.kind}
                  </span>
                  <span className="fx-mono" style={{ fontSize: 10, color: "var(--muted)" }}>
                    {formatEuro(node.exposureEur)}
                  </span>
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Selection detail */}
        <div className="fx-panel" data-testid="graph-selection-panel">
          <div className="fx-panel-head">
            <h2>Sélection</h2>
          </div>

          {!details ? (
            <div className="fx-panel-body">
              <p className="fx-mono" style={{ fontSize: 11, color: "var(--muted)", lineHeight: 1.65 }}>
                Cliquez sur un fournisseur, un IBAN ou un finding pour afficher le contexte
                d&apos;investigation.
              </p>
            </div>
          ) : (
            <div className="fx-panel-body space-y-4">
              <div className="flex items-start gap-3">
                <span
                  className="fx-mono"
                  style={{
                    fontSize: 16,
                    color:
                      details.node.kind === "vendor"
                        ? "var(--info)"
                        : details.node.kind === "iban"
                          ? "var(--warn)"
                          : "var(--risk)",
                    marginTop: 2,
                    flexShrink: 0,
                  }}
                >
                  {details.node.kind === "vendor"
                    ? "Σ"
                    : details.node.kind === "iban"
                      ? "∿"
                      : "▲"}
                </span>
                <div>
                  <p
                    style={{
                      fontFamily: "var(--font-display)",
                      fontSize: 18,
                      color: "var(--fg)",
                      lineHeight: 1.1,
                    }}
                  >
                    {details.node.label}
                  </p>
                  <p
                    className="fx-mono"
                    style={{ marginTop: 4, fontSize: 11, color: "var(--muted)", textTransform: "capitalize" }}
                  >
                    {details.node.kind}
                  </p>
                </div>
              </div>

              <dl className="space-y-3">
                {(
                  [
                    ["Sévérité", details.node.severity],
                    ["Score", `${details.node.riskScore}/100`],
                    ["Exposition", formatEuro(details.node.exposureEur)],
                    ...(details.node.maskedValue
                      ? [["Valeur", details.node.maskedValue] as [string, string]]
                      : []),
                  ] as [string, string][]
                ).map(([k, v]) => (
                  <div key={k} className="flex justify-between gap-4">
                    <dt className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>
                      {k}
                    </dt>
                    <dd
                      className="fx-mono"
                      style={{ fontSize: 12, color: "var(--fg)", textTransform: "capitalize" }}
                    >
                      {v}
                    </dd>
                  </div>
                ))}
              </dl>

              {details.finding ? (
                <div
                  style={{
                    background: "var(--bg-2)",
                    border: "1px solid var(--border)",
                    padding: "14px 16px",
                  }}
                >
                  <p
                    className="fx-mono"
                    style={{ fontSize: 12, color: "var(--fg)" }}
                  >
                    {getSignalLabel(details.finding.signal)}
                  </p>
                  <p
                    className="fx-mono"
                    style={{ marginTop: 4, fontSize: 11, color: "var(--muted)" }}
                  >
                    {details.finding.invoiceId}
                  </p>
                  <Link
                    href={`/score/${details.finding.invoiceId}`}
                    className="fx-link"
                    style={{ marginTop: 10 }}
                  >
                    Ouvrir le score ↗
                  </Link>
                  <Link
                    href={case360Href(getScenarioForP2PFindingSignal(details.finding.signal).caseId)}
                    className="fx-link"
                    style={{ marginTop: 8 }}
                  >
                    Ouvrir Case 360 →
                  </Link>
                </div>
              ) : null}

              {details.vendor ? (
                <Link
                  href={`/vendors/${details.vendor.vendorId}`}
                  className="fx-btn sm"
                  style={{ display: "inline-flex" }}
                >
                  Fiche fournisseur ↗
                </Link>
              ) : null}
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}
