import demoData from "@/data/p2p-demo.json";
import type { FindingSummary, P2PDemoDataset, VendorSummary } from "@/types/p2p";

export function getP2PDataset(): P2PDemoDataset {
  return demoData as P2PDemoDataset;
}

export function getFinding(id: string): FindingSummary | undefined {
  return getP2PDataset().findings.find((finding) => finding.id === id);
}

export function getVendor(id: string): VendorSummary | undefined {
  return getP2PDataset().vendors.find(
    (vendor) => vendor.id === id || vendor.vendorId === id,
  );
}
