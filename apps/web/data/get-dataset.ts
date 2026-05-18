import demoData from "@/data/p2p-demo.json";
import { SEVERITY_ORDER } from "@/lib/p2p-demo-taxonomy";
import type { FindingSummary, GraphNode, P2PDemoDataset, VendorSummary } from "@/types/p2p";

export function getP2PDataset(): P2PDemoDataset {
  return demoData as P2PDemoDataset;
}

export function getFinding(id: string): FindingSummary | undefined {
  return getP2PDataset().findings.find(
    (finding) => finding.id === id || finding.invoiceId === id,
  );
}

export function getVendor(id: string): VendorSummary | undefined {
  return getP2PDataset().vendors.find(
    (vendor) => vendor.id === id || vendor.vendorId === id,
  );
}

export function getVendorFindings(id: string): FindingSummary[] {
  const dataset = getP2PDataset();
  const vendor = getVendor(id);
  if (!vendor) return [];

  const findingIds = new Set(vendor.findingIds);
  return dataset.findings
    .filter(
      (finding) =>
        findingIds.has(finding.id) ||
        finding.vendorId === vendor.vendorId ||
        finding.vendorName === vendor.name,
    )
    .sort(
      (a, b) =>
        SEVERITY_ORDER[b.severity] - SEVERITY_ORDER[a.severity] ||
        b.riskScore - a.riskScore ||
        b.exposureEur - a.exposureEur,
    );
}

export function getFindingVendor(finding: FindingSummary): VendorSummary | undefined {
  return getVendor(finding.vendorId) ?? getP2PDataset().vendors.find(
    (vendor) => vendor.name === finding.vendorName,
  );
}

export function getFindingContext(findingId: string): {
  nodes: GraphNode[];
  relatedFindings: FindingSummary[];
} {
  const dataset = getP2PDataset();
  const edges = dataset.edges.filter((edge) => edge.findingIds.includes(findingId));
  const nodeIds = new Set<string>();
  const findingIds = new Set<string>([findingId]);

  for (const edge of edges) {
    nodeIds.add(edge.source);
    nodeIds.add(edge.target);
    for (const id of edge.findingIds) findingIds.add(id);
  }

  return {
    nodes: dataset.nodes.filter((node) => nodeIds.has(node.id)),
    relatedFindings: dataset.findings.filter((finding) => findingIds.has(finding.id)),
  };
}
