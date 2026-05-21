"use client";

import { useEffect, useMemo } from "react";
import {
  SigmaContainer,
  useLoadGraph,
  useRegisterEvents,
} from "@react-sigma/core";
import "@react-sigma/core/lib/style.css";
import Graph from "graphology";
import { circular } from "graphology-layout";
import forceAtlas2 from "graphology-layout-forceatlas2";
import type { Schemas } from "@p2pfd/shared-types";

type RingsGraph = Schemas["RingsGraph"];

const COLORS = {
  vendor: "#1f3a6e",
  iban: "#e5a93a",
  highlight: "#a23e48",
};

function LoadGraph({
  data,
  onNodeClick,
}: {
  data: RingsGraph;
  onNodeClick: (nodeId: string) => void;
}) {
  const loadGraph = useLoadGraph();
  const registerEvents = useRegisterEvents();

  useEffect(() => {
    const graph = new Graph();
    for (const node of data.nodes) {
      graph.addNode(node.id, {
        label: node.label,
        size: node.kind === "iban" ? 8 : 5,
        color: node.kind === "iban" ? COLORS.iban : COLORS.vendor,
      });
    }
    for (const edge of data.edges) {
      if (graph.hasNode(edge.source) && graph.hasNode(edge.target)) {
        try {
          graph.addEdge(edge.source, edge.target, { size: 1 });
        } catch {
          // duplicate edge — ignore
        }
      }
    }
    // Circular initial puis ForceAtlas2 pour bonne séparation
    circular.assign(graph);
    if (graph.order > 0 && graph.order < 5000) {
      try {
        forceAtlas2.assign(graph, {
          iterations: 100,
          settings: {
            gravity: 1,
            scalingRatio: 10,
            slowDown: 5,
          },
        });
      } catch {
        // fallback à circular si forceAtlas2 plante (ex. graphe disconnecté trivial)
      }
    }
    loadGraph(graph);
  }, [data, loadGraph]);

  useEffect(() => {
    registerEvents({
      clickNode: (event) => onNodeClick(event.node),
    });
  }, [registerEvents, onNodeClick]);

  return null;
}

export function RingsGraphView({
  data,
  onSelect,
}: {
  data: RingsGraph;
  onSelect: (id: string) => void;
}) {
  const settings = useMemo(
    () => ({
      renderLabels: true,
      labelSize: 12,
      labelDensity: 0.5,
      labelGridCellSize: 200,
      defaultEdgeColor: "#1f242e",
      labelColor: { color: "#e9e6dc" },
    }),
    [],
  );

  return (
    <div
      style={{
        border: "1px solid var(--border)",
        background: "var(--bg-2)",
      }}
    >
      <SigmaContainer
        style={{ height: 600, background: "var(--bg-2)" }}
        settings={settings}
      >
        <LoadGraph data={data} onNodeClick={onSelect} />
      </SigmaContainer>
    </div>
  );
}
