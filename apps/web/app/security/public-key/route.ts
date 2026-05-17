import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export function GET() {
  return NextResponse.json(
    {
      public_key_b64: "",
      enabled: "false",
      algorithm: "",
      mode: "demo",
      data_origin: "synthetic",
      note: "Mode demo Vercel: signatures Ed25519 desactivees. En pilote, cet endpoint doit exposer la cle publique du backend FastAPI.",
    },
    {
      headers: {
        "x-p2pfd-data-origin": "synthetic",
        "x-p2pfd-live-sources": "false",
      },
    },
  );
}
