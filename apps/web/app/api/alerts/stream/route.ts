import { type NextRequest } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";
const API_SECRET = process.env.FRAUD_API_SECRET ?? "";

export const runtime = "nodejs";

const SSE_HEADERS = {
  "Cache-Control": "no-cache, no-transform",
  Connection: "keep-alive",
  "Content-Type": "text/event-stream; charset=utf-8",
  "X-Accel-Buffering": "no",
};

export async function GET(request: NextRequest) {
  if (!API_BASE) {
    return new Response(
      sseEvent("backend_error", {
        error: "NEXT_PUBLIC_API_URL non configure",
        hint: "La page bascule en polling tant que le backend FastAPI n'est pas configure.",
      }),
      { headers: SSE_HEADERS },
    );
  }

  const url = new URL(`${API_BASE}/api/v1/alerts/stream`);
  request.nextUrl.searchParams.forEach((value, key) => url.searchParams.set(key, value));

  const headers = new Headers();
  if (API_SECRET) headers.set("Authorization", `Bearer ${API_SECRET}`);

  const upstream = await fetch(url, {
    cache: "no-store",
    headers,
  });

  if (!upstream.ok || !upstream.body) {
    return new Response(
      sseEvent("backend_error", {
        error: `FastAPI alerts stream ${upstream.status}`,
        body: await upstream.text(),
      }),
      { headers: SSE_HEADERS },
    );
  }

  return new Response(upstream.body, {
    status: 200,
    headers: SSE_HEADERS,
  });
}

function sseEvent(event: string, payload: unknown) {
  return `event: ${event}\ndata: ${JSON.stringify(payload)}\n\n`;
}
