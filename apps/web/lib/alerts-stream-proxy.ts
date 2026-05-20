export const ALERTS_STREAM_PATH = "/api/v1/alerts/stream";
export const ALERTS_STREAM_DEFAULT_LIMIT = 50;
export const ALERTS_STREAM_MAX_LIMIT = 200;
export const ALERTS_STREAM_DEFAULT_POLL_SECONDS = 5;
export const ALERTS_STREAM_MAX_POLL_SECONDS = 60;

export const ALERTS_SSE_HEADERS: Record<string, string> = {
  "Cache-Control": "no-cache, no-transform",
  Connection: "keep-alive",
  "Content-Type": "text/event-stream; charset=utf-8",
  "X-Accel-Buffering": "no",
};

export function buildAlertsStreamUrl({
  apiBase,
  requestUrl,
  lastEventId,
}: {
  apiBase: string;
  requestUrl: string | URL;
  lastEventId?: string | null;
}): URL {
  const incoming = new URL(String(requestUrl));
  const upstream = new URL(
    ALERTS_STREAM_PATH.replace(/^\//, ""),
    apiBase.endsWith("/") ? apiBase : `${apiBase}/`,
  );

  upstream.searchParams.set(
    "cursor",
    String(resolveReplayCursor(incoming.searchParams, lastEventId)),
  );
  upstream.searchParams.set(
    "limit",
    String(
      boundedInteger(
        incoming.searchParams.get("limit"),
        ALERTS_STREAM_DEFAULT_LIMIT,
        1,
        ALERTS_STREAM_MAX_LIMIT,
      ),
    ),
  );
  upstream.searchParams.set(
    "poll_seconds",
    String(
      boundedNumber(
        incoming.searchParams.get("poll_seconds"),
        ALERTS_STREAM_DEFAULT_POLL_SECONDS,
        1,
        ALERTS_STREAM_MAX_POLL_SECONDS,
      ),
    ),
  );

  if (isTruthy(incoming.searchParams.get("once"))) {
    upstream.searchParams.set("once", "true");
  }

  return upstream;
}

export function resolveReplayCursor(
  searchParams: URLSearchParams,
  lastEventId?: string | null,
): number {
  const queryCursor = boundedInteger(searchParams.get("cursor"), 0, 0, Number.MAX_SAFE_INTEGER);
  if (queryCursor > 0) return queryCursor;
  return boundedInteger(lastEventId ?? null, 0, 0, Number.MAX_SAFE_INTEGER);
}

export function makeAlertsUpstreamHeaders({
  apiSecret,
  cookieHeader,
}: {
  apiSecret?: string;
  cookieHeader?: string | null;
}): Headers {
  const headers = new Headers({
    Accept: "text/event-stream",
    "Cache-Control": "no-cache",
  });

  if (apiSecret) {
    headers.set("Authorization", `Bearer ${apiSecret}`);
  }

  if (cookieHeader) {
    headers.set("Cookie", cookieHeader);
  }

  return headers;
}

export function isAlertsStreamAuthorized({
  cookieHeader,
  requireSession,
}: {
  cookieHeader?: string | null;
  requireSession: boolean;
}): boolean {
  if (!requireSession) return true;
  return /(?:^|;\s*)p2pfd_session=/.test(cookieHeader ?? "");
}

export function sseEvent(event: string, payload: unknown): string {
  return `event: ${event}\ndata: ${JSON.stringify(payload)}\n\n`;
}

function boundedInteger(
  value: string | null,
  fallback: number,
  min: number,
  max: number,
): number {
  if (value === null || value.trim() === "") return fallback;
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.min(max, Math.max(min, parsed));
}

function boundedNumber(
  value: string | null,
  fallback: number,
  min: number,
  max: number,
): number {
  if (value === null || value.trim() === "") return fallback;
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.min(max, Math.max(min, parsed));
}

function isTruthy(value: string | null): boolean {
  if (!value) return false;
  return ["1", "true", "yes"].includes(value.toLowerCase());
}
