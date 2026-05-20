/**
 * Route handler upload - proxy multipart streaming vers FastAPI /detect/csv.
 *
 * En mode demo Vercel sans backend configure, la route renvoie un jeu de
 * resultats statique base sur le dataset P2P du repo.
 */

import { type NextRequest, NextResponse } from "next/server";

import { buildDemoUploadResponse } from "@/lib/demo-investigation";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";
const SECRET = process.env.FRAUD_API_SECRET ?? "";

export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  if (!API_BASE) {
    const formData = await req.formData();
    const file = formData.get("file");

    if (!(file instanceof File)) {
      return NextResponse.json(
        {
          error: "Aucun fichier fourni",
          hint: "Selectionner un CSV ou un Excel pour la detection demo.",
        },
        { status: 400 },
      );
    }

    return NextResponse.json(buildDemoUploadResponse(), { status: 200 });
  }

  const url = `${API_BASE}/detect/csv`;
  const headers = new Headers();
  if (SECRET) headers.set("Authorization", `Bearer ${SECRET}`);

  const contentType = req.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);

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
      "content-type": upstream.headers.get("content-type") ?? "application/json",
    },
  });
}
