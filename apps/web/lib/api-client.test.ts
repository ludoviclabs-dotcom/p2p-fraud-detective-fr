import { describe, expect, it } from "vitest";
import { resolveApiUrl } from "@/lib/api-client";

describe("resolveApiUrl", () => {
  it("keeps browser API calls on the Vercel origin", () => {
    expect(
      resolveApiUrl("/api/v1/cases", {
        apiBase: "https://api.example.test",
        isBrowser: true,
      }),
    ).toBe("/api/v1/cases");
  });

  it("allows server-side callers to hit FastAPI directly", () => {
    expect(
      resolveApiUrl("/api/v1/cases", {
        apiBase: "https://api.example.test",
        isBrowser: false,
      }),
    ).toBe("https://api.example.test/api/v1/cases");
  });

  it("preserves absolute URLs", () => {
    expect(resolveApiUrl("https://other.example.test/health")).toBe(
      "https://other.example.test/health",
    );
  });
});
