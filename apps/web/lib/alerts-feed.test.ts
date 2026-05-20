import { describe, expect, it } from "vitest";
import type { AuditEntryOut } from "@/lib/api-client";
import {
  buildAlertStreamUrl,
  computeAlertFeedStats,
  getAlertStreamStatusLabel,
  mergeAuditEvent,
  parseAuditStreamEvent,
  parseHeartbeatCursor,
  parseStoredAlertCursor,
} from "@/lib/alerts-feed";

function auditEntry(
  seq: number,
  overrides: Partial<AuditEntryOut> = {},
): AuditEntryOut {
  return {
    seq,
    at: `2026-05-18T10:${String(seq).padStart(2, "0")}:00Z`,
    actor: "auditor@example.test",
    kind: "case_created",
    payload: {},
    prev_hash: "prev",
    hash: `hash-${seq}`,
    signature: "",
    ...overrides,
  };
}

describe("mergeAuditEvent", () => {
  it("deduplicates by seq, keeps newest values, sorts descending and caps the feed", () => {
    const previous = [
      auditEntry(2, { kind: "case_created" }),
      auditEntry(1, { kind: "case_triaged" }),
    ];

    const merged = mergeAuditEvent(
      previous,
      auditEntry(1, { kind: "case_closed" }),
      2,
    );

    expect(merged.map((event) => event.seq)).toEqual([2, 1]);
    expect(merged).toHaveLength(2);
    expect(merged[1]?.kind).toBe("case_closed");
  });
});

describe("computeAlertFeedStats", () => {
  it("counts events by kind, critical payloads and signed entries", () => {
    const stats = computeAlertFeedStats([
      auditEntry(3, {
        kind: "case_closed",
        payload: { severity: "critical" },
        signature: "sig-3",
      }),
      auditEntry(2, {
        kind: "case_closed",
        payload: { severity: "high" },
      }),
      auditEntry(1, {
        kind: "case_comment",
        payload: { severity: "medium" },
        signature: "sig-1",
      }),
    ]);

    expect(stats.total).toBe(3);
    expect([...stats.kinds.entries()]).toEqual([
      ["case_closed", 2],
      ["case_comment", 1],
    ]);
    expect(stats.critical).toBe(1);
    expect(stats.signed).toBe(2);
  });
});

describe("getAlertStreamStatusLabel", () => {
  it("describes live SSE, active polling and fallback polling states", () => {
    expect(
      getAlertStreamStatusLabel({ streamState: "open", isFetching: false }),
    ).toBe("Live SSE");
    expect(
      getAlertStreamStatusLabel({
        streamState: "connecting",
        isFetching: true,
      }),
    ).toBe("Polling - refresh en cours...");
    expect(
      getAlertStreamStatusLabel({
        streamState: "fallback",
        isFetching: false,
        refetchMs: 10_000,
      }),
    ).toBe("Fallback polling - 10s");
  });

  it("uses translated labels when a translator is provided", () => {
    const translate = (key: string, params?: Record<string, string | number>) =>
      `${key}:${params?.seconds ?? ""}`;

    expect(
      getAlertStreamStatusLabel({
        streamState: "fallback",
        isFetching: false,
        refetchMs: 15_000,
        translate,
      }),
    ).toBe("stream.fallback_polling:15");
  });
});

describe("alert stream replay helpers", () => {
  it("builds a stream URL from the persisted cursor", () => {
    expect(buildAlertStreamUrl(42)).toBe("/api/alerts/stream?cursor=42&limit=50");
    expect(buildAlertStreamUrl(-1, 25)).toBe("/api/alerts/stream?cursor=0&limit=25");
  });

  it("parses stored cursor and ignores invalid values", () => {
    expect(parseStoredAlertCursor("12")).toBe(12);
    expect(parseStoredAlertCursor("-1")).toBe(0);
    expect(parseStoredAlertCursor("bad")).toBe(0);
  });

  it("parses audit events and heartbeat cursors safely", () => {
    const event = parseAuditStreamEvent(JSON.stringify(auditEntry(7)));
    expect(event?.seq).toBe(7);
    expect(parseAuditStreamEvent("{")).toBeNull();
    expect(parseAuditStreamEvent(JSON.stringify({ seq: 1 }))).toBeNull();

    expect(parseHeartbeatCursor(JSON.stringify({ cursor: 9 }))).toBe(9);
    expect(parseHeartbeatCursor(JSON.stringify({ cursor: -1 }))).toBeNull();
    expect(parseHeartbeatCursor("{")).toBeNull();
  });
});
