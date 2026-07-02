/**
 * Simulation VoP locale — fallback offline du pré-check nom ↔ IBAN.
 *
 * Reproduit la sémantique du backend (`enrichment/vop_client.py`, mode
 * simulation) : normalisation des raisons sociales, similarité token-sort,
 * verdicts EPC (match / close_match / no_match). Utilisée quand le backend
 * FastAPI est injoignable — la démo `/connecteurs` reste fonctionnelle.
 */

export type VopVerdict = "match" | "close_match" | "no_match" | "not_available";

export interface VopSimResult {
  verdict: VopVerdict;
  similarity: number | null;
  detail: string;
  provider: "simulation-locale";
}

const MATCH_THRESHOLD = 95;
const CLOSE_MATCH_THRESHOLD = 80;

const LEGAL_SUFFIXES = [" SAS", " SARL", " SA", " SASU", " EURL", " SCI", " LTD", " GMBH"];

export function normalizeCompanyName(value: string): string {
  // Ponctuation → espace : « NORD-EST » et « NORD EST » doivent matcher.
  let s = value
    .toUpperCase()
    .replace(/[-.,·'’]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  for (const suffix of LEGAL_SUFFIXES) {
    if (s.endsWith(suffix)) s = s.slice(0, -suffix.length).trim();
  }
  return s;
}

function levenshtein(a: string, b: string): number {
  if (a === b) return 0;
  if (!a.length) return b.length;
  if (!b.length) return a.length;
  let prev = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i++) {
    const cur = [i];
    for (let j = 1; j <= b.length; j++) {
      cur[j] = Math.min(
        prev[j] + 1,
        cur[j - 1] + 1,
        prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1),
      );
    }
    prev = cur;
  }
  return prev[b.length];
}

export function tokenSortSimilarity(a: string, b: string): number {
  const sa = normalizeCompanyName(a).split(" ").sort().join(" ");
  const sb = normalizeCompanyName(b).split(" ").sort().join(" ");
  const maxLen = Math.max(sa.length, sb.length);
  if (maxLen === 0) return 0;
  return Math.round((1 - levenshtein(sa, sb) / maxLen) * 1000) / 10;
}

export function simulateVopPrecheck(
  beneficiaryName: string,
  expectedName: string | undefined,
): VopSimResult {
  if (!expectedName?.trim()) {
    return {
      verdict: "not_available",
      similarity: null,
      detail:
        "Simulation VoP : renseigner le nom attendu (registre interne ou Sirene) pour comparer.",
      provider: "simulation-locale",
    };
  }
  const similarity = tokenSortSimilarity(beneficiaryName, expectedName);
  if (similarity >= MATCH_THRESHOLD) {
    return {
      verdict: "match",
      similarity,
      detail: "Concordance nom ↔ IBAN (équivalent EPC MATCH).",
      provider: "simulation-locale",
    };
  }
  if (similarity >= CLOSE_MATCH_THRESHOLD) {
    return {
      verdict: "close_match",
      similarity,
      detail:
        "Quasi-concordance (EPC CLOSE MATCH) — vérifier le nom exact par canal vérifié avant d'enregistrer.",
      provider: "simulation-locale",
    };
  }
  return {
    verdict: "no_match",
    similarity,
    detail:
      "Divergence nom ↔ IBAN (EPC NO MATCH) — ne pas enregistrer le RIB sans vérification renforcée.",
    provider: "simulation-locale",
  };
}
