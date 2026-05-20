const AUTH_PREFIX = "/api/auth";
const OIDC_PREFIX = "/oidc";

const ALLOWED_ROUTES: Record<string, readonly string[]> = {
  callback: ["GET"],
  login: ["GET"],
  logout: ["POST"],
  me: ["GET"],
};

export type AuthRouteValidation =
  | { ok: true; subpath: string }
  | { ok: false; status: 404 | 405; error: string; allow?: string };

export function validateAuthProxyRoute(
  method: string,
  slug: readonly string[] | undefined,
): AuthRouteValidation {
  const subpath = (slug ?? []).join("/");
  if (!subpath || subpath.includes("..") || subpath.includes("//")) {
    return { ok: false, status: 404, error: "Route auth inconnue." };
  }

  const allowedMethods = ALLOWED_ROUTES[subpath];
  if (!allowedMethods) {
    return { ok: false, status: 404, error: "Route auth inconnue." };
  }

  if (!allowedMethods.includes(method)) {
    return {
      ok: false,
      status: 405,
      error: "Methode non autorisee pour cette route auth.",
      allow: allowedMethods.join(", "),
    };
  }

  return { ok: true, subpath };
}

export function buildOidcProxyUrl({
  apiBase,
  subpath,
  requestUrl,
}: {
  apiBase: string;
  subpath: string;
  requestUrl: string | URL;
}): URL {
  const incoming = new URL(String(requestUrl));
  const encodedSubpath = subpath
    .split("/")
    .map((segment) => encodeURIComponent(segment))
    .join("/");
  const upstream = new URL(
    `${OIDC_PREFIX.replace(/^\//, "")}/${encodedSubpath}`,
    apiBase.endsWith("/") ? apiBase : `${apiBase}/`,
  );
  incoming.searchParams.forEach((value, key) => upstream.searchParams.set(key, value));
  return upstream;
}

export function forwardOidcHeaders(reqHeaders: Headers, requestUrl: string | URL): Headers {
  const incoming = new URL(String(requestUrl));
  const out = new Headers();
  const allow = new Set(["accept", "authorization", "content-type", "cookie"]);

  reqHeaders.forEach((value, key) => {
    if (allow.has(key.toLowerCase())) {
      out.set(key, value);
    }
  });

  out.set("X-Forwarded-Host", incoming.host);
  out.set("X-Forwarded-Proto", incoming.protocol.replace(":", ""));
  return out;
}

export function getSetCookies(headers: Headers): string[] {
  const getter = (headers as Headers & { getSetCookie?: () => string[] }).getSetCookie;
  if (typeof getter === "function") return getter.call(headers);

  const single = headers.get("set-cookie");
  return single ? [single] : [];
}

export function rewriteAuthSetCookie(cookie: string, secureCookies: boolean): string {
  let rewritten = cookie.replace(/;\s*Path=\/oidc(?=;|$)/i, `; Path=${AUTH_PREFIX}`);

  if (secureCookies && !/;\s*Secure(?:;|$)/i.test(rewritten)) {
    rewritten = `${rewritten}; Secure`;
  }

  return rewritten;
}

export function rewriteAuthLocation({
  location,
  apiBase,
  requestUrl,
}: {
  location: string;
  apiBase: string;
  requestUrl: string | URL;
}): string {
  const requestOrigin = new URL(String(requestUrl)).origin;
  const apiOrigin = new URL(apiBase).origin;
  const target = new URL(location, apiBase);

  if (target.origin !== apiOrigin || !target.pathname.startsWith(OIDC_PREFIX)) {
    return location;
  }

  target.pathname = target.pathname.replace(OIDC_PREFIX, AUTH_PREFIX);
  return `${requestOrigin}${target.pathname}${target.search}${target.hash}`;
}
