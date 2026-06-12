// Détection « payload cockpit vide » pour décider du fallback démo.
//
// Le proxy FastAPI (`NEXT_PUBLIC_API_URL`) peut répondre 200 avec un backend à
// base vide : métriques à zéro ET séries de tendance de 30 points tous à zéro.
// L'ancien test ne regardait que la *présence* des séries — donc un payload
// tout-à-zéro était jugé « plein » et le cockpit affichait 0 € d'exposition /
// 0 cases, alors que la table top-fournisseurs (qui, elle, retombe sur la démo)
// montrait des millions. Incohérence vitrine corrigée : un payload est « vide »
// dès lors qu'aucune métrique ni aucune tendance ne porte de valeur positive.

interface CockpitKpisLike {
  exposure_total_eur?: unknown;
  exposure_critical_eur?: unknown;
  n_cases_open?: unknown;
  n_cases_overdue?: unknown;
  trend_cases_created?: unknown;
  trend_cases_closed?: unknown;
  trend_critical_alerts?: unknown;
  trend_audit_activity?: unknown;
}

function isPositiveNumber(value: unknown): boolean {
  return typeof value === "number" && Number.isFinite(value) && value > 0;
}

function hasPositiveTrend(value: unknown): boolean {
  return (
    Array.isArray(value) &&
    value.some(
      (point) =>
        point != null &&
        typeof point === "object" &&
        isPositiveNumber((point as { value?: unknown }).value),
    )
  );
}

/**
 * `true` si le payload KPI ne contient aucune donnée exploitable (objet absent,
 * métriques nulles et tendances entièrement à zéro). Le handler de route doit
 * alors retomber sur `buildDemoCockpitKpis()`.
 */
export function isEmptyCockpitKpisPayload(payload: unknown): boolean {
  if (!payload || typeof payload !== "object") return true;
  const data = payload as CockpitKpisLike;

  const hasPositiveMetric = [
    data.exposure_total_eur,
    data.exposure_critical_eur,
    data.n_cases_open,
    data.n_cases_overdue,
  ].some(isPositiveNumber);

  const hasTrend = [
    data.trend_cases_created,
    data.trend_cases_closed,
    data.trend_critical_alerts,
    data.trend_audit_activity,
  ].some(hasPositiveTrend);

  return !hasPositiveMetric && !hasTrend;
}
