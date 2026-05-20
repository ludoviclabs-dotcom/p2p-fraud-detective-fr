import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  allowedDevOrigins: ["127.0.0.1"],
  // typedRoutes desactive en Phase 0, reactive en Phase 2 quand tous les
  // segments de route auront leur page.
};

export default nextConfig;
