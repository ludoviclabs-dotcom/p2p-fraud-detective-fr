import type { AuditEntryOut } from "@/lib/api-client";

export const ALERTS_REFETCH_MS = 5_000;
export const ALERTS_FEED_LIMIT = 50;
export const ALERTS_CURSOR_STORAGE_KEY = "p2pfd_alerts_cursor";

export type StreamState = "connecting" | "open" | "fallback";

export interface AlertFeedStats {
  total: number;
  kinds: Map<string, number>;
  critical: number;
  signed: number;
}

export function mergeAuditEvent(
  previous: AuditEntryOut[],
  next: AuditEntryOut,
  limit = ALERTS_FEED_LIMIT,
): AuditEntryOut[] {
  const deduped = previous.filter((item) => item.seq !== next.seq);
  return [next, ...deduped].sort((a, b) => b.seq - a.seq).slice(0, limit);
}

export function parseStoredAlertCursor(value: string | null): number {
  if (!value) return 0;
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed) || parsed < 0) return 0;
  return parsed;
}

export function readStoredAlertCursor(storage: Storage | undefined): number {
  if (!storage) return 0;
  return parseStoredAlertCursor(storage.getItem(ALERTS_CURSOR_STORAGE_KEY));
}

export function writeStoredAlertCursor(
  storage: Storage | undefined,
  cursor: number,
): void {
  if (!storage || !Number.isFinite(cursor) || cursor < 0) return;
  storage.setItem(ALERTS_CURSOR_STORAGE_KEY, String(Math.floor(cursor)));
}

export function buildAlertStreamUrl(
  cursor: number,
  limit = ALERTS_FEED_LIMIT,
): string {
  const params = new URLSearchParams({
    cursor: String(Math.max(0, Math.floor(cursor))),
    limit: String(limit),
  });
  return `/api/alerts/stream?${params.toString()}`;
}

export function parseAuditStreamEvent(raw: string): AuditEntryOut | null {
  try {
    const parsed = JSON.parse(raw) as Partial<AuditEntryOut>;
    if (typeof parsed.seq !== "number" || !parsed.kind || !parsed.at) {
      return null;
    }
    return parsed as AuditEntryOut;
  } catch {
    return null;
  }
}

export function parseHeartbeatCursor(raw: string): number | null {
  try {
    const parsed = JSON.parse(raw) as { cursor?: unknown };
    if (typeof parsed.cursor !== "number" || parsed.cursor < 0) return null;
    return Math.floor(parsed.cursor);
  } catch {
    return null;
  }
}

export function computeAlertFeedStats(events: AuditEntryOut[]): AlertFeedStats {
  const kinds = new Map<string, number>();
  let critical = 0;
  let signed = 0;

  for (const event of events) {
    kinds.set(event.kind, (kinds.get(event.kind) ?? 0) + 1);

    const severity = event.payload?.severity;
    if (severity === "critical") {
      critical += 1;
    }

    if (event.signature) {
      signed += 1;
    }
  }

  return {
    total: events.length,
    kinds,
    critical,
    signed,
  };
}

export function getAlertStreamStatusLabel({
  streamState,
  isFetching,
  refetchMs = ALERTS_REFETCH_MS,
  translate,
}: {
  streamState: StreamState;
  isFetching: boolean;
  refetchMs?: number;
  translate?: (key: string, params?: Record<string, string | number>) => string;
}): string {
  if (streamState === "open") {
    return translate?.("stream.live_sse") ?? "Live SSE";
  }

  if (isFetching) {
    return translate?.("stream.polling_fetching") ?? "Polling - refresh en cours...";
  }

  const seconds = refetchMs / 1000;
  return (
    translate?.("stream.fallback_polling", { seconds }) ??
    `Fallback polling - ${seconds}s`
  );
}
