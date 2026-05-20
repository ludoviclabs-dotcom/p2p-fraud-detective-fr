import { proxyApiV1Request } from "@/lib/api-v1-proxy";

type Params = Promise<{ path?: string[] }>;

async function handle(request: Request, context: { params: Params }) {
  const { path = [] } = await context.params;
  const upstream = await proxyApiV1Request(request, `/api/v1/${path.join("/")}`);
  if (upstream) return upstream;

  return Response.json(
    {
      error: "NEXT_PUBLIC_API_URL non configure cote Vercel",
      hint: "Configurer le backend FastAPI ou ajouter une route demo specifique.",
    },
    { status: 503 },
  );
}

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export const GET = handle;
export const POST = handle;
export const PUT = handle;
export const PATCH = handle;
export const DELETE = handle;
export const OPTIONS = handle;
