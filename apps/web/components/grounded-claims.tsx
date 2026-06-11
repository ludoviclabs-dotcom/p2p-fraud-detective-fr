"use client";

import type { GroundedClaim } from "@/lib/api-client";

/** Chips des source_ids cités par un claim IA (provenance validée backend). */
export function SourceChips({ sourceIds }: { sourceIds: string[] }) {
  return (
    <span style={{ display: "inline-flex", flexWrap: "wrap", gap: 4, marginLeft: 8 }}>
      {sourceIds.map((sid) => (
        <code
          key={sid}
          className="fx-mono"
          style={{
            background: "var(--panel-2)",
            border: "1px solid var(--border)",
            color: "var(--info)",
            padding: "0 5px",
            fontSize: 10,
          }}
        >
          {sid}
        </code>
      ))}
    </span>
  );
}

/** Liste de claims sourcés (sortie IA structurée du socle ADR-0007). */
export function ClaimList({ claims }: { claims: GroundedClaim[] }) {
  return (
    <ul style={{ margin: 0, padding: 0, listStyle: "none" }} className="space-y-2">
      {claims.map((claim) => (
        <li key={claim.text} style={{ fontSize: 13, lineHeight: 1.6, color: "var(--fg-2)" }}>
          {claim.text}
          <SourceChips sourceIds={claim.source_ids} />
        </li>
      ))}
    </ul>
  );
}
