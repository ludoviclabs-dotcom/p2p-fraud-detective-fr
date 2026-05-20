const API_V1_PREFIX = "/api/v1";

const REQUEST_HEADERS_TO_FORWARD = ["accept", "content-type"] as const;
const RESPONSE_HEADERS_TO_FORWARD = [
  "cache-control",
  "content-type",
  "etag",
  "last-modified",
] as const;

export function buildApiV1ProxyUrl({
  apiBase,
  path,
  requestUrl,
}: {
  apiBase: string;
  path: string;
  requestUrl: string | URL;
}): URL {
  const incoming = new URL(String(requestUrl));
  const normalizedPath = path.startsWith(API_V1_PREFIX)
    ? path.slice(API_V1_PREFIX.length)
    : path;
  const safePath = normalizedPath
    .split("/")
    .filter(Boolean)
    .map(encodeURIComponent)
    .join("/");
  const upstream = new URL(
    `${API_V1_PREFIX.replace(/^\//, "")}${safePath ? `/${safePath}` : ""}`,
    apiBase.endsWith("/") ? apiBase : `${apiBase}/`,
  );
  upstream.search = incoming.search;
  return upstream;
}

export function makeApiV1UpstreamHeaders({
  apiSecret,
  incomingHeaders,
}: {
  apiSecret?: string;
  incomingHeaders: Headers;
}): Headers {
  const headers = new Headers();

  for (const key of REQUEST_HEADERS_TO_FORWARD) {
    const value = incomingHeaders.get(key);
    if (value) headers.set(key, value);
  }

  if (apiSecret) {
    headers.set("Authorization", `Bearer ${apiSecret}`);
  }

  return headers;
}

export function shouldForwardApiV1Body(method: string): boolean {
  return method !== "GET" && method !== "HEAD";
}

export async function proxyApiV1Request(
  request: Request,
  path: string,
): Promise<Response | null> {
  const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "";
  if (!apiBase) return null;

  const upstreamUrl = buildApiV1ProxyUrl({
    apiBase,
    path,
    requestUrl: request.url,
  });
  const init: RequestInit = {
    cache: "no-store",
    headers: makeApiV1UpstreamHeaders({
      apiSecret: process.env.FRAUD_API_SECRET ?? "",
      incomingHeaders: request.headers,
    }),
    method: request.method,
    redirect: "manual",
  };

  if (shouldForwardApiV1Body(request.method)) {
    init.body = await request.arrayBuffer();
  }

  try {
    const upstream = await fetch(upstreamUrl, init);
    return new Response(upstream.body, {
      headers: makeApiV1ResponseHeaders(upstream.headers),
      status: upstream.status,
      statusText: upstream.statusText,
    });
  } catch (error) {
    return Response.json(
      {
        error: "FastAPI backend unreachable",
        detail: error instanceof Error ? error.message : String(error),
      },
      { status: 502 },
    );
  }
}

function makeApiV1ResponseHeaders(upstreamHeaders: Headers): Headers {
  const headers = new Headers();

  for (const key of RESPONSE_HEADERS_TO_FORWARD) {
    const value = upstreamHeaders.get(key);
    if (value) headers.set(key, value);
  }

  headers.set("Cache-Control", "no-store");
  return headers;
}
