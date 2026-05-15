"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowUpRight, CircleAlert, EyeOff, Landmark, Network } from "lucide-react";
import Link from "next/link";

import { formatEuro, formatNumber } from "@/lib/format";
import type { GraphNode, P2PDemoDataset, Severity } from "@/types/p2p";

const SEVERITY_ORDER: Record<Severity, number> = {
  low: 1,
  medium: 2,
  high: 3,
  critical: 4,
};

const NODE_COLORS = {
  vendor: "#1F3A6E",
  iban: "#3E7CB1",
  finding: "#A23E48",
};

const SEVERITY_COLORS: Record<Severity, string> = {
  low: "#3E7C5A",
  medium: "#C97B1F",
  high: "#D35F2A",
  critical: "#A23E48",
};

const SIGNAL_OPTIONS = [
  { value: "all", label: "Tous les signaux" },
  { value: "shared_iban_ring", label: "Anneaux IBAN partagés" },
  { value: "vendor_cluster", label: "Clusters fournisseurs" },
];

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

export function GraphExplorer({ dataset }: { dataset: P2PDemoDataset }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [signal, setSignal] = useState("all");
  const [severity, setSeverity] = useState("all");
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [graphError, setGraphError] = useState<string | null>(null);

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

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
      <section className="panel overflow-hidden rounded-md">
        <div className="flex flex-col gap-3 border-b border-[#D8DEE9] bg-white p-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-[#141927]">Graphe interactif WebGL</h2>
            <p className="mt-1 text-sm text-[#5A6478]">
              {formatNumber(filtered.nodes.length)} nœuds · {formatNumber(filtered.edges.length)} liens ·{" "}
              {formatNumber(findingCount)} findings visibles
            </p>
          </div>

          <div className="flex flex-col gap-2 sm:flex-row">
            <label className="sr-only" htmlFor="signal-filter">
              Filtrer par signal
            </label>
            <select
              id="signal-filter"
              value={signal}
              onChange={(event) => setSignal(event.target.value)}
              className="rounded-md border border-[#D8DEE9] bg-white px-3 py-2 text-sm font-medium text-[#141927]"
            >
              {SIGNAL_OPTIONS.map((option) => (
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
              className="rounded-md border border-[#D8DEE9] bg-white px-3 py-2 text-sm font-medium text-[#141927]"
            >
              {SEVERITY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {filtered.nodes.length > 0 ? (
          <div className="graph-frame relative bg-white">
            <div ref={containerRef} className="h-full w-full" />
            {graphError ? (
              <div className="absolute inset-0 grid place-items-center bg-white px-6 text-center">
                <div>
                  <EyeOff aria-hidden className="mx-auto h-8 w-8 text-[#5A6478]" />
                  <p className="mt-3 font-semibold text-[#141927]">Rendu du graphe indisponible.</p>
                  <p className="mt-1 max-w-md text-sm text-[#5A6478]">{graphError}</p>
                </div>
              </div>
            ) : null}
          </div>
        ) : (
          <div className="grid h-[420px] place-items-center bg-white px-6 text-center">
            <div>
              <EyeOff aria-hidden className="mx-auto h-8 w-8 text-[#5A6478]" />
              <p className="mt-3 font-semibold text-[#141927]">Aucun nœud pour ce filtre.</p>
              <p className="mt-1 text-sm text-[#5A6478]">
                Relâchez la sévérité ou revenez à tous les signaux.
              </p>
            </div>
          </div>
        )}
      </section>

      <aside className="flex flex-col gap-5">
        <section className="panel rounded-md p-5">
          <h3 className="text-sm font-semibold uppercase tracking-[0.14em] text-[#5A6478]">
            Légende
          </h3>
          <div className="mt-4 space-y-3 text-sm">
            <div className="flex items-center gap-3">
              <span className="h-3 w-3 rounded-full bg-[#1F3A6E]" />
              <span>Fournisseur</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="h-3 w-3 rounded-full bg-[#3E7CB1]" />
              <span>IBAN masqué</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="h-3 w-3 rounded-full bg-[#A23E48]" />
              <span>Finding critique</span>
            </div>
          </div>
        </section>

        <section className="panel rounded-md p-5">
          <h3 className="text-sm font-semibold uppercase tracking-[0.14em] text-[#5A6478]">
            Sélection
          </h3>

          {!details ? (
            <p className="mt-4 text-sm leading-6 text-[#5A6478]">
              Cliquez sur un fournisseur, un IBAN ou un finding pour afficher le contexte
              d&apos;investigation.
            </p>
          ) : (
            <div className="mt-4 space-y-4">
              <div className="flex items-start gap-3">
                {details.node.kind === "vendor" ? (
                  <Landmark aria-hidden className="mt-0.5 h-5 w-5 text-[#1F3A6E]" />
                ) : details.node.kind === "iban" ? (
                  <Network aria-hidden className="mt-0.5 h-5 w-5 text-[#3E7CB1]" />
                ) : (
                  <CircleAlert aria-hidden className="mt-0.5 h-5 w-5 text-[#A23E48]" />
                )}
                <div>
                  <p className="text-lg font-semibold text-[#141927]">{details.node.label}</p>
                  <p className="mt-1 text-sm capitalize text-[#5A6478]">{details.node.kind}</p>
                </div>
              </div>

              <dl className="space-y-3 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="text-[#5A6478]">Sévérité</dt>
                  <dd className="font-medium capitalize text-[#141927]">{details.node.severity}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-[#5A6478]">Score</dt>
                  <dd className="mono text-[#141927]">{details.node.riskScore}/100</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-[#5A6478]">Exposition</dt>
                  <dd className="mono text-[#141927]">{formatEuro(details.node.exposureEur)}</dd>
                </div>
                {details.node.maskedValue ? (
                  <div className="flex justify-between gap-4">
                    <dt className="text-[#5A6478]">Valeur</dt>
                    <dd className="mono text-right text-[#141927]">{details.node.maskedValue}</dd>
                  </div>
                ) : null}
              </dl>

              {details.finding ? (
                <div className="rounded-md border border-[#D8DEE9] bg-[#F6F7FB] p-4 text-sm">
                  <p className="font-semibold text-[#141927]">{details.finding.signal}</p>
                  <p className="mono mt-1 text-[#5A6478]">{details.finding.invoiceId}</p>
                  <Link
                    href={`/score/${details.finding.invoiceId}`}
                    className="mt-3 inline-flex items-center gap-1 font-semibold text-[#1F3A6E]"
                  >
                    Ouvrir le score
                    <ArrowUpRight aria-hidden className="h-3.5 w-3.5" />
                  </Link>
                </div>
              ) : null}

              {details.vendor ? (
                <Link
                  href={`/vendors/${details.vendor.vendorId}`}
                  className="inline-flex items-center gap-2 rounded-md bg-[#1F3A6E] px-3 py-2 text-sm font-semibold text-white transition hover:bg-[#0F1B33]"
                >
                  Fiche fournisseur
                  <ArrowUpRight aria-hidden className="h-4 w-4" />
                </Link>
              ) : null}
            </div>
          )}
        </section>
      </aside>
    </div>
  );
}
