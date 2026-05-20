import type { DetectorScore, P2PTransaction, ReasonCode } from "@/types/risk";
import {
  detectorResult,
  domainFromUrl,
  extractIban,
  includesAny,
  maskIban,
  reason,
  simpleSimilarity,
} from "@/lib/risk/risk-utils";

const SENSITIVE_URL_WORDS = ["secure", "securise", "sécurisé", "verify", "urgent", "wallet", "crypto", "refund"];

export function qrRisk(transaction: P2PTransaction): DetectorScore {
  const reasons: ReasonCode[] = [];
  const qr = transaction.qr;
  if (!qr?.payload) {
    return detectorResult({
      detector: "qrRisk",
      label: "QR Code Fraud Analyzer",
      status: "demo",
      maxScore: 22,
      dataUsed: ["qr.payload unavailable"],
      reasonCodes: reasons,
      explanationWhenEmpty: "Aucun payload QR fourni pour ce scénario.",
    });
  }

  const payloadDomain = domainFromUrl(qr.payload);
  const payloadIban = extractIban(qr.payload);
  const expectedIban = qr.expectedIban ?? transaction.beneficiary.expectedIban ?? transaction.document?.expectedIban;

  if (/https?:\/\//i.test(qr.payload) && payloadDomain) {
    reasons.push(
      reason(
        "qrRisk",
        "QR_URL_PRESENT",
        "URL dans le QR",
        "Le payload QR redirige vers une URL au lieu de porter uniquement une référence de paiement.",
        5,
        { domain: payloadDomain },
      ),
    );
  }

  if (payloadIban && expectedIban && payloadIban.replace(/\s+/g, "") !== expectedIban.replace(/\s+/g, "")) {
    reasons.push(
      reason(
        "qrRisk",
        "QR_IBAN_MISMATCH",
        "IBAN QR différent",
        "L'IBAN extrait du QR code diffère de l'IBAN attendu.",
        22,
        { payloadIban: maskIban(payloadIban), expectedIban: maskIban(expectedIban) },
      ),
    );
  }

  if (payloadDomain && qr.expectedDomain) {
    const similarity = simpleSimilarity(payloadDomain, qr.expectedDomain);
    if (payloadDomain !== qr.expectedDomain && similarity >= 0.58) {
      reasons.push(
        reason(
          "qrRisk",
          "QR_TYPOSQUATTED_DOMAIN",
          "Domaine typosquatté",
          "Le domaine du QR ressemble au domaine attendu sans être identique.",
          14,
          { payloadDomain, expectedDomain: qr.expectedDomain },
        ),
      );
    }
  }

  if (includesAny(qr.payload, SENSITIVE_URL_WORDS)) {
    reasons.push(
      reason(
        "qrRisk",
        "QR_SENSITIVE_URL_WORDS",
        "Mots sensibles dans l'URL",
        "Le payload QR contient des termes fréquemment associés à la pression ou à la sécurisation frauduleuse.",
        9,
      ),
    );
  }

  if (payloadDomain && /free|bit\.ly|tinyurl|pay-secure|support|wallet/i.test(payloadDomain)) {
    reasons.push(
      reason(
        "qrRisk",
        "QR_SUSPICIOUS_URL",
        "URL QR suspecte",
        "Le domaine du QR présente une forme ou un hébergement inhabituel pour un paiement fournisseur.",
        12,
        { payloadDomain },
      ),
    );
  }

  return detectorResult({
    detector: "qrRisk",
    label: "QR Code Fraud Analyzer",
    status: "demo",
    maxScore: 24,
    dataUsed: ["qr.payload", "expectedIban", "expectedDomain"],
    reasonCodes: reasons,
    explanationWhenEmpty: "Payload QR cohérent avec les références attendues.",
  });
}
