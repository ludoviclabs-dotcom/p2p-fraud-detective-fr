import { describe, expect, it } from "vitest";
import {
  buildApiV1ProxyUrl,
  makeApiV1UpstreamHeaders,
  shouldForwardApiV1Body,
} from "@/lib/api-v1-proxy";

describe("buildApiV1ProxyUrl", () => {
  it("maps relative Vercel API paths to the FastAPI v1 backend", () => {
    const url = buildApiV1ProxyUrl({
      apiBase: "https://api.example.test/root/",
      path: "/api/v1/vendors/acme-42/timeline",
      requestUrl: "https://app.example.test/api/v1/vendors/acme-42/timeline?days=90",
    });

    expect(url.toString()).toBe(
      "https://api.example.test/root/api/v1/vendors/acme-42/timeline?days=90",
    );
  });
});

describe("makeApiV1UpstreamHeaders", () => {
  it("adds server-side bearer auth without forwarding browser host metadata", () => {
    const headers = makeApiV1UpstreamHeaders({
      apiSecret: "secret",
      incomingHeaders: new Headers({
        accept: "application/json",
        "content-type": "application/json",
        host: "app.example.test",
      }),
    });

    expect(headers.get("authorization")).toBe("Bearer secret");
    expect(headers.get("accept")).toBe("application/json");
    expect(headers.get("content-type")).toBe("application/json");
    expect(headers.get("host")).toBeNull();
  });
});

describe("shouldForwardApiV1Body", () => {
  it("forwards request bodies only for mutating methods", () => {
    expect(shouldForwardApiV1Body("GET")).toBe(false);
    expect(shouldForwardApiV1Body("HEAD")).toBe(false);
    expect(shouldForwardApiV1Body("POST")).toBe(true);
    expect(shouldForwardApiV1Body("PATCH")).toBe(true);
  });
});
