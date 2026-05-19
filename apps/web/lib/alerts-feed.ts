import type { AuditEntryOut } from "@/lib/api-client";

export const ALERTS_REFETCH_MS = 5_000;

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
  limit = 50,
): AuditEntryOut[] {
  const deduped = previous.filter((item) => item.seq !== next.seq);
  return [next, ...deduped].sort((a, b) => b.seq - a.seq).slice(0, limit);
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
}: {
  streamState: StreamState;
  isFetching: boolean;
  refetchMs?: number;
}): string {
  if (streamState === "open") {
    return "Live SSE";
  }

  if (isFetching) {
    return "Polling · refresh en cours...";
  }

  return `Fallback polling · ${refetchMs / 1000}s`;
}
