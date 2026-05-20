import { type NextRequest } from "next/server";
import {
  ALERTS_SSE_HEADERS,
  buildAlertsStreamUrl,
  isAlertsStreamAuthorized,
  makeAlertsUpstreamHeaders,
  sseEvent,
} from "@/lib/alerts-stream-proxy";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";
const API_SECRET = process.env.FRAUD_API_SECRET ?? "";
const REQUIRE_SESSION = process.env.P2P_ALERTS_STREAM_REQUIRE_SESSION === "1";

export const runtime = "nodejs";

export async function GET(request: NextRequest) {
  if (
    !isAlertsStreamAuthorized({
      cookieHeader: request.headers.get("cookie"),
      requireSession: REQUIRE_SESSION,
    })
  ) {
    return new Response(
      sseEvent("auth_error", {
        error: "Session OIDC requise pour ouvrir le flux alertes.",
      }),
      { headers: ALERTS_SSE_HEADERS, status: 401 },
    );
  }

  if (!API_BASE) {
    return new Response(
      sseEvent("backend_error", {
        error: "NEXT_PUBLIC_API_URL non configure",
        hint: "Backend FastAPI absent, bascule en polling.",
      }),
      { headers: ALERTS_SSE_HEADERS },
    );
  }

  const upstreamUrl = buildAlertsStreamUrl({
    apiBase: API_BASE,
    requestUrl: request.url,
    lastEventId: request.headers.get("last-event-id"),
  });

  const abortController = new AbortController();
  request.signal.addEventListener("abort", () => abortController.abort(), {
    once: true,
  });

  let upstream: Response;
  try {
    upstream = await fetch(upstreamUrl, {
      cache: "no-store",
      headers: makeAlertsUpstreamHeaders({
        apiSecret: API_SECRET,
        cookieHeader: request.headers.get("cookie"),
      }),
      signal: abortController.signal,
    });
  } catch (error) {
    return new Response(
      sseEvent("backend_error", {
        error: error instanceof Error ? error.message : "FastAPI alerts stream unreachable",
        hint: "Backend SSE indisponible, fallback polling.",
      }),
      { headers: ALERTS_SSE_HEADERS },
    );
  }

  if (!upstream.ok || !upstream.body) {
    return new Response(
      sseEvent("backend_error", {
        error: `FastAPI alerts stream ${upstream.status}`,
        body: await upstream.text(),
        hint: "Backend SSE indisponible, fallback polling.",
      }),
      { headers: ALERTS_SSE_HEADERS },
    );
  }

  return new Response(upstream.body, {
    status: 200,
    headers: ALERTS_SSE_HEADERS,
  });
}
