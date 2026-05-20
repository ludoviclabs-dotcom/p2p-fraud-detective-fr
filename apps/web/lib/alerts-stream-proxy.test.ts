import { describe, expect, it } from "vitest";
import {
  buildAlertsStreamUrl,
  isAlertsStreamAuthorized,
  makeAlertsUpstreamHeaders,
  resolveReplayCursor,
  sseEvent,
} from "@/lib/alerts-stream-proxy";

describe("buildAlertsStreamUrl", () => {
  it("forwards only bounded stream parameters to FastAPI", () => {
    const url = buildAlertsStreamUrl({
      apiBase: "https://api.example.test",
      requestUrl:
        "https://app.example.test/api/alerts/stream?limit=999&cursor=12&poll_seconds=0.2&unknown=x",
    });

    expect(url.toString()).toBe(
      "https://api.example.test/api/v1/alerts/stream?cursor=12&limit=200&poll_seconds=1",
    );
  });

  it("falls back to Last-Event-ID when query cursor is absent", () => {
    const url = buildAlertsStreamUrl({
      apiBase: "https://api.example.test/root/",
      requestUrl: "https://app.example.test/api/alerts/stream?once=true",
      lastEventId: "88",
    });

    expect(url.toString()).toBe(
      "https://api.example.test/root/api/v1/alerts/stream?cursor=88&limit=50&poll_seconds=5&once=true",
    );
  });
});

describe("resolveReplayCursor", () => {
  it("prefers explicit query cursor over Last-Event-ID", () => {
    const params = new URLSearchParams({ cursor: "9" });
    expect(resolveReplayCursor(params, "99")).toBe(9);
  });

  it("ignores invalid cursor values", () => {
    const params = new URLSearchParams({ cursor: "bad" });
    expect(resolveReplayCursor(params, "7")).toBe(7);
  });
});

describe("alerts stream headers and auth", () => {
  it("adds bearer auth and cookies for the upstream stream", () => {
    const headers = makeAlertsUpstreamHeaders({
      apiSecret: "secret",
      cookieHeader: "p2pfd_session=s1",
    });

    expect(headers.get("authorization")).toBe("Bearer secret");
    expect(headers.get("cookie")).toBe("p2pfd_session=s1");
    expect(headers.get("accept")).toBe("text/event-stream");
  });

  it("can require an OIDC session cookie without breaking public demo mode", () => {
    expect(
      isAlertsStreamAuthorized({ cookieHeader: null, requireSession: false }),
    ).toBe(true);
    expect(
      isAlertsStreamAuthorized({ cookieHeader: "foo=bar", requireSession: true }),
    ).toBe(false);
    expect(
      isAlertsStreamAuthorized({
        cookieHeader: "foo=bar; p2pfd_session=s1",
        requireSession: true,
      }),
    ).toBe(true);
  });

  it("serializes compliant SSE events", () => {
    expect(sseEvent("heartbeat", { cursor: 2 })).toBe(
      'event: heartbeat\ndata: {"cursor":2}\n\n',
    );
  });
});
