import { describe, expect, it } from "vitest";

import { isEmptyCockpitKpisPayload } from "@/lib/cockpit-payload";
import { buildDemoCockpitKpis } from "@/lib/demo-cockpit";

describe("isEmptyCockpitKpisPayload", () => {
  it("traite null / undefined / non-objet comme vide", () => {
    expect(isEmptyCockpitKpisPayload(null)).toBe(true);
    expect(isEmptyCockpitKpisPayload(undefined)).toBe(true);
    expect(isEmptyCockpitKpisPayload("nope")).toBe(true);
    expect(isEmptyCockpitKpisPayload(42)).toBe(true);
  });

  it("traite un backend à base vide (métriques 0 + tendances 0) comme vide", () => {
    // Reproduit la réponse réelle observée en prod : 200 OK, tout à zéro mais
    // séries de tendance non vides (30 points à 0). Régression C1.
    const emptyBackend = {
      exposure_total_eur: 0,
      exposure_critical_eur: 0,
      n_cases_open: 0,
      n_cases_overdue: 0,
      n_cases_unassigned_critical: 0,
      trend_cases_created: Array.from({ length: 30 }, (_, i) => ({
        date: `2026-05-${String((i % 28) + 1).padStart(2, "0")}`,
        value: 0,
      })),
      trend_cases_closed: [{ date: "2026-05-01", value: 0 }],
      trend_critical_alerts: [{ date: "2026-05-01", value: 0 }],
      trend_audit_activity: [{ date: "2026-05-01", value: 0 }],
    };
    expect(isEmptyCockpitKpisPayload(emptyBackend)).toBe(true);
  });

  it("n'est pas vide dès qu'une métrique est positive", () => {
    expect(isEmptyCockpitKpisPayload({ exposure_total_eur: 1_240_000 })).toBe(false);
    expect(isEmptyCockpitKpisPayload({ n_cases_open: 7 })).toBe(false);
  });

  it("n'est pas vide dès qu'une tendance porte au moins une valeur positive", () => {
    expect(
      isEmptyCockpitKpisPayload({
        trend_cases_created: [
          { date: "2026-05-01", value: 0 },
          { date: "2026-05-02", value: 3 },
        ],
      }),
    ).toBe(false);
  });

  it("considère le payload démo riche comme non vide", () => {
    expect(isEmptyCockpitKpisPayload(buildDemoCockpitKpis())).toBe(false);
  });
});
