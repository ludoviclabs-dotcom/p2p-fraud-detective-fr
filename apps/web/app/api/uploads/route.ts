/**
 * Route handler upload — proxy multipart streaming vers FastAPI /detect/csv.
 *
 * Côté Next.js, on streame le request body (FormData) sans le buffer en
 * mémoire — critique pour les CSV de gros volumes (>50 MB).
 */

import { type NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";
const SECRET = process.env.FRAUD_API_SECRET ?? "";

export const runtime = "nodejs"; // streaming Request body nécessite Node runtime

export async function POST(req: NextRequest) {
  if (!API_BASE) {
    return NextResponse.json(
      {
        error: "NEXT_PUBLIC_API_URL non configuré",
        hint: "Définir l'URL du backend FastAPI dans les env vars Vercel",
      },
      { status: 503 },
    );
  }

  const url = `${API_BASE}/detect/csv`;
  const headers = new Headers();
  if (SECRET) headers.set("Authorization", `Bearer ${SECRET}`);
  // Forward Content-Type (multipart boundary inclus)
  const contentType = req.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);

  // Stream le body upstream — Next.js + Node 18+ supportent ReadableStream
  // pour le request body, ce qui évite de tout charger en RAM.
  const upstream = await fetch(url, {
    method: "POST",
    headers,
    body: req.body,
    // @ts-expect-error: duplex requis pour les request streams en Node
    duplex: "half",
  });

  const body = await upstream.arrayBuffer();
  return new NextResponse(body, {
    status: upstream.status,
    headers: {
      "content-type":
        upstream.headers.get("content-type") ?? "application/json",
    },
  });
}
