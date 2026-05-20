/**
 * OIDC proxy route. It keeps the browser on the Vercel domain while forwarding
 * the actual OIDC flow to FastAPI `/oidc/*`.
 */

import { type NextRequest, NextResponse } from "next/server";
import {
  buildOidcProxyUrl,
  forwardOidcHeaders,
  getSetCookies,
  rewriteAuthLocation,
  rewriteAuthSetCookie,
  validateAuthProxyRoute,
} from "@/lib/oidc-proxy";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

type Params = Promise<{ slug: string[] }>;

async function handle(req: NextRequest, ctx: { params: Params }) {
  const { slug } = await ctx.params;
  const route = validateAuthProxyRoute(req.method, slug);
  if (!route.ok) {
    const headers = new Headers();
    if (route.allow) headers.set("Allow", route.allow);
    return NextResponse.json({ error: route.error }, { status: route.status, headers });
  }

  if (!API_BASE) {
    if (route.subpath === "me") {
      return NextResponse.json(
        {
          authenticated: false,
          error: "NEXT_PUBLIC_API_URL non configure cote Vercel",
        },
        { status: 401 },
      );
    }

    return NextResponse.json(
      {
        error: "NEXT_PUBLIC_API_URL non configure cote Vercel",
        hint: "Ajouter la variable d'env pointant vers HF Spaces ou backend FastAPI.",
      },
      { status: 503 },
    );
  }

  const upstreamUrl = buildOidcProxyUrl({
    apiBase: API_BASE,
    subpath: route.subpath,
    requestUrl: req.url,
  });

  const init: RequestInit = {
    method: req.method,
    headers: forwardOidcHeaders(req.headers, req.url),
    redirect: "manual",
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.text();
  }

  const upstream = await fetch(upstreamUrl, init);
  const headers = new Headers();
  const secureCookies = req.nextUrl.protocol === "https:";

  for (const cookie of getSetCookies(upstream.headers)) {
    headers.append("set-cookie", rewriteAuthSetCookie(cookie, secureCookies));
  }

  const contentType = upstream.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);

  if (upstream.status >= 300 && upstream.status < 400) {
    const location = upstream.headers.get("location");
    if (location) {
      headers.set(
        "location",
        rewriteAuthLocation({
          location,
          apiBase: API_BASE,
          requestUrl: req.url,
        }),
      );
    }
  }

  const body = await upstream.arrayBuffer();
  return new NextResponse(body, {
    status: upstream.status,
    headers,
  });
}

export const GET = handle;
export const POST = handle;
export const PUT = handle;
export const DELETE = handle;
export const PATCH = handle;
