import { describe, expect, it } from "vitest";

import {
  normalizeCompanyName,
  simulateVopPrecheck,
  tokenSortSimilarity,
} from "./vop-sim";

describe("normalizeCompanyName", () => {
  it("strips legal suffixes, punctuation and normalizes whitespace", () => {
    expect(normalizeCompanyName("  aciers  nord-est   SAS ")).toBe("ACIERS NORD EST");
    expect(normalizeCompanyName("Prestaconseil SARL")).toBe("PRESTACONSEIL");
  });
});

describe("tokenSortSimilarity", () => {
  it("is order-insensitive", () => {
    expect(tokenSortSimilarity("Dupont Marc", "Marc Dupont")).toBe(100);
  });

  it("scores unrelated names low", () => {
    expect(tokenSortSimilarity("Global Intermediary Ltd", "Aciers Nord-Est SAS")).toBeLessThan(
      50,
    );
  });
});

describe("simulateVopPrecheck", () => {
  it("returns match for equivalent names", () => {
    const r = simulateVopPrecheck("Aciers Nord-Est SAS", "ACIERS NORD-EST");
    expect(r.verdict).toBe("match");
    expect(r.similarity).toBe(100);
  });

  it("returns close_match for near names", () => {
    const r = simulateVopPrecheck("Aciers Nord Est", "Aciers Nord-Est SAS");
    expect(r.verdict === "close_match" || r.verdict === "match").toBe(true);
  });

  it("returns no_match for divergent names", () => {
    expect(simulateVopPrecheck("Global Intermediary Ltd", "Aciers Nord-Est").verdict).toBe(
      "no_match",
    );
  });

  it("returns not_available without expected name", () => {
    expect(simulateVopPrecheck("X", undefined).verdict).toBe("not_available");
    expect(simulateVopPrecheck("X", "  ").verdict).toBe("not_available");
  });
});
