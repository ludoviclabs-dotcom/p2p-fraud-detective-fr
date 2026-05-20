import { describe, expect, it } from "vitest";
import {
  buildOidcProxyUrl,
  forwardOidcHeaders,
  rewriteAuthLocation,
  rewriteAuthSetCookie,
  validateAuthProxyRoute,
} from "@/lib/oidc-proxy";

describe("validateAuthProxyRoute", () => {
  it("allows only the production OIDC surface", () => {
    expect(validateAuthProxyRoute("GET", ["login"])).toEqual({
      ok: true,
      subpath: "login",
    });
    expect(validateAuthProxyRoute("GET", ["me"])).toEqual({
      ok: true,
      subpath: "me",
    });
    expect(validateAuthProxyRoute("POST", ["logout"])).toEqual({
      ok: true,
      subpath: "logout",
    });
    expect(validateAuthProxyRoute("POST", ["login"])).toMatchObject({
      ok: false,
      status: 405,
      allow: "GET",
    });
    expect(validateAuthProxyRoute("GET", ["admin"])).toMatchObject({
      ok: false,
      status: 404,
    });
  });
});

describe("buildOidcProxyUrl", () => {
  it("maps /api/auth/* to /oidc/* and keeps query params", () => {
    const url = buildOidcProxyUrl({
      apiBase: "https://api.example.test",
      subpath: "callback",
      requestUrl: "https://app.example.test/api/auth/callback?code=abc&state=xyz",
    });

    expect(url.toString()).toBe(
      "https://api.example.test/oidc/callback?code=abc&state=xyz",
    );
  });
});

describe("forwardOidcHeaders", () => {
  it("forwards only safe browser headers plus x-forwarded metadata", () => {
    const input = new Headers({
      authorization: "Bearer x",
      cookie: "p2pfd_session=s1",
      host: "evil.example",
      accept: "application/json",
    });
    const output = forwardOidcHeaders(input, "https://app.example.test/api/auth/me");

    expect(output.get("authorization")).toBe("Bearer x");
    expect(output.get("cookie")).toBe("p2pfd_session=s1");
    expect(output.get("host")).toBeNull();
    expect(output.get("x-forwarded-host")).toBe("app.example.test");
    expect(output.get("x-forwarded-proto")).toBe("https");
  });
});

describe("cookie and redirect rewriting", () => {
  it("rewrites FastAPI state cookies onto the proxied auth path", () => {
    expect(
      rewriteAuthSetCookie(
        "p2pfd_oidc_state=abc; Path=/oidc; HttpOnly; SameSite=lax",
        true,
      ),
    ).toBe("p2pfd_oidc_state=abc; Path=/api/auth; HttpOnly; SameSite=lax; Secure");
  });

  it("keeps root session cookies on the app domain", () => {
    expect(
      rewriteAuthSetCookie(
        "p2pfd_session=s1; Path=/; HttpOnly; SameSite=lax; Secure",
        true,
      ),
    ).toBe("p2pfd_session=s1; Path=/; HttpOnly; SameSite=lax; Secure");
  });

  it("rewrites same-backend /oidc redirects to the Vercel auth proxy", () => {
    expect(
      rewriteAuthLocation({
        location: "/oidc/callback?code=abc",
        apiBase: "https://api.example.test",
        requestUrl: "https://app.example.test/api/auth/login",
      }),
    ).toBe("https://app.example.test/api/auth/callback?code=abc");
  });

  it("leaves IdP redirects untouched", () => {
    expect(
      rewriteAuthLocation({
        location: "https://idp.example.test/authorize",
        apiBase: "https://api.example.test",
        requestUrl: "https://app.example.test/api/auth/login",
      }),
    ).toBe("https://idp.example.test/authorize");
  });
});
