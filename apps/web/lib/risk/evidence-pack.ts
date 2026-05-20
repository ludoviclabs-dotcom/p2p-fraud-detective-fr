import { scoreTransaction } from "@/lib/risk/scoreEngine";
import type { EvidencePack, P2PTransaction, RiskGraphSummary, RiskScoreResult } from "@/types/risk";

export const EVIDENCE_DISCLAIMER =
  "Démonstrateur professionnel sur données synthétiques. Aucun scoring bancaire réel, aucune certification conformité, aucun fingerprinting réel, aucun dark web scraping. La décision finale reste humaine.";

export function buildEvidencePack(input: {
  caseId: string;
  transaction: P2PTransaction;
  score?: RiskScoreResult;
  graphSummary: RiskGraphSummary;
  analystNotes?: string;
  auditTrail?: EvidencePack["auditTrail"];
  timeline?: EvidencePack["timeline"];
}): EvidencePack {
  const score = input.score ?? scoreTransaction(input.transaction);
  const now = new Date().toISOString();

  return {
    caseId: input.caseId,
    generatedAt: now,
    transaction: input.transaction,
    score,
    typology: score.typology,
    decision: score.decision,
    reasonCodes: score.reasonCodes,
    detectorScores: score.detectorScores,
    timeline:
      input.timeline ??
      [
        {
          at: input.transaction.createdAt,
          actor: "risk-engine-demo-v1",
          event: "Transaction reçue",
          detail: "Transaction synthétique chargée dans le Workbench.",
        },
        {
          at: score.generatedAt,
          actor: "risk-engine-demo-v1",
          event: "Score calculé",
          detail: `Score ${score.score}/100, niveau ${score.level}, décision ${score.decision}.`,
        },
      ],
    graphSummary: input.graphSummary,
    recommendedActions: score.recommendedActions,
    analystNotes: input.analystNotes ?? "",
    auditTrail:
      input.auditTrail ??
      [
        {
          at: now,
          actor: "demo-analyst",
          action: "evidence_pack_generated",
          detail: "Evidence pack généré côté démonstrateur.",
        },
      ],
    disclaimer: EVIDENCE_DISCLAIMER,
  };
}

export function evidencePackHtml(pack: EvidencePack): string {
  const reasonRows = pack.reasonCodes
    .map(
      (reason) =>
        `<tr><td>${escapeHtml(reason.code)}</td><td>${escapeHtml(reason.label)}</td><td>${reason.weight}</td><td>${escapeHtml(reason.detector)}</td></tr>`,
    )
    .join("");

  const detectorRows = pack.detectorScores
    .map(
      (detector) =>
        `<tr><td>${escapeHtml(detector.label)}</td><td>${detector.score}/${detector.maxScore}</td><td>${escapeHtml(detector.status)}</td></tr>`,
    )
    .join("");

  return `<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <title>Evidence Pack ${escapeHtml(pack.caseId)}</title>
  <style>
    body { font-family: Inter, Segoe UI, Arial, sans-serif; color: #111827; margin: 32px; }
    h1, h2 { color: #08111f; }
    .muted { color: #667085; }
    .score { font-size: 36px; font-weight: 800; color: #2f6bff; }
    table { border-collapse: collapse; width: 100%; margin: 12px 0 24px; }
    th, td { border: 1px solid #e6ebf2; padding: 8px; text-align: left; font-size: 13px; }
    th { background: #f7f9fc; }
    .box { border: 1px solid #e6ebf2; border-radius: 8px; padding: 16px; margin: 16px 0; }
  </style>
</head>
<body>
  <h1>Evidence Pack - ${escapeHtml(pack.caseId)}</h1>
  <p class="muted">Généré le ${escapeHtml(pack.generatedAt)}</p>
  <div class="box">
    <div class="score">${pack.score.score}/100</div>
    <p><strong>Niveau:</strong> ${pack.score.level} · <strong>Décision:</strong> ${pack.decision} · <strong>Typologie:</strong> ${pack.typology}</p>
  </div>
  <h2>Transaction</h2>
  <pre>${escapeHtml(JSON.stringify(pack.transaction, null, 2))}</pre>
  <h2>Reason codes</h2>
  <table><thead><tr><th>Code</th><th>Libellé</th><th>Poids</th><th>Détecteur</th></tr></thead><tbody>${reasonRows}</tbody></table>
  <h2>Détecteurs</h2>
  <table><thead><tr><th>Module</th><th>Score</th><th>Statut</th></tr></thead><tbody>${detectorRows}</tbody></table>
  <h2>Graphe</h2>
  <p>${escapeHtml(pack.graphSummary.suspiciousPath)}</p>
  <h2>Notes analyste</h2>
  <p>${escapeHtml(pack.analystNotes || "Aucune note.")}</p>
  <h2>Disclaimer</h2>
  <p>${escapeHtml(pack.disclaimer)}</p>
</body>
</html>`;
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
