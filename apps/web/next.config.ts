import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  allowedDevOrigins: ["127.0.0.1"],
  // typedRoutes désactivé en Phase 0 — réactivé en Phase 2 quand tous les
  // segments de route auront leur page (sinon il faut caster `as Route`
  // pour chaque Link vers une route stub).
  // Permet de proxy /api/* vers le backend FastAPI quand
  // NEXT_PUBLIC_API_URL est défini (utile en dev local + Vercel preview).
  async rewrites() {
    const apiBase = process.env.NEXT_PUBLIC_API_URL;
    if (!apiBase) return [];
    return [
      {
        source: "/api/v1/:path*",
        destination: `${apiBase}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
