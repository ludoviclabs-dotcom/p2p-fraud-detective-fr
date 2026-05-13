/**
 * OIDC proxy route — forward toutes les requêtes `/api/auth/*` vers
 * le backend FastAPI `/oidc/*` (Phase 4 P4-3 existant).
 *
 * Pourquoi un proxy plutôt qu'un appel direct depuis le navigateur :
 * 1. Cookies SameSite=Strict côté `vercel.app` uniquement (pas cross-domain HF Spaces).
 * 2. Le state PKCE et la session HMAC vivent côté backend — on ne touche pas
 *    aux cookies sensibles côté client.
 * 3. CORS simplifié : un seul domaine côté navigateur.
 *
 * Mapping :
 *   GET  /api/auth/login         → 302 vers IdP via FastAPI /oidc/login
 *   GET  /api/auth/callback?code → callback FastAPI /oidc/callback
 *   POST /api/auth/logout        → FastAPI POST /oidc/logout
 *   GET  /api/auth/me            → FastAPI /oidc/me (session active)
 */

import { type NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

type Params = Promise<{ slug: string[] }>;

async function handle(req: NextRequest, ctx: { params: Params }) {
  if (!API_BASE) {
    return NextResponse.json(
      {
        error: "NEXT_PUBLIC_API_URL non configuré côté Vercel",
        hint: "Ajouter la variable d'env pointant vers HF Spaces ou backend FastAPI",
      },
      { status: 503 },
    );
  }

  const { slug } = await ctx.params;
  const subpath = slug.join("/");
  const url = new URL(`${API_BASE}/oidc/${subpath}`);
  // Forward des query params
  req.nextUrl.searchParams.forEach((v, k) => url.searchParams.set(k, v));

  const init: RequestInit = {
    method: req.method,
    headers: forwardHeaders(req.headers),
    redirect: "manual",
  };
  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.text();
  }

  const upstream = await fetch(url, init);

  // Préserver les Set-Cookie pour la session HMAC + state PKCE
  const setCookies = upstream.headers.getSetCookie?.() ?? [];
  const headers = new Headers();
  for (const cookie of setCookies) headers.append("set-cookie", cookie);
  const contentType = upstream.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  // Préserver les redirects 302 (login → IdP)
  if (upstream.status >= 300 && upstream.status < 400) {
    const location = upstream.headers.get("location");
    if (location) headers.set("location", location);
  }

  const body = await upstream.arrayBuffer();
  return new NextResponse(body, {
    status: upstream.status,
    headers,
  });
}

function forwardHeaders(reqHeaders: Headers): Headers {
  const out = new Headers();
  // Forward cookies + auth, drop host pour éviter conflits
  const allow = new Set(["cookie", "authorization", "content-type"]);
  reqHeaders.forEach((value, key) => {
    if (allow.has(key.toLowerCase())) out.set(key, value);
  });
  return out;
}

export const GET = handle;
export const POST = handle;
export const PUT = handle;
export const DELETE = handle;
export const PATCH = handle;
