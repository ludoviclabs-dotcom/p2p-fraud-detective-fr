import type { DetectorScore, P2PTransaction, ReasonCode } from "@/types/risk";
import { detectorResult, maskIban, reason, simpleSimilarity } from "@/lib/risk/risk-utils";

export function documentRibRisk(transaction: P2PTransaction): DetectorScore {
  const reasons: ReasonCode[] = [];
  const document = transaction.document;
  if (!document) {
    return detectorResult({
      detector: "documentRibRisk",
      label: "Document / RIB / Invoice Fraud Check",
      status: "demo",
      maxScore: 22,
      dataUsed: ["document signals unavailable"],
      reasonCodes: reasons,
      explanationWhenEmpty: "Aucun document fourni pour ce scénario.",
    });
  }

  if (
    document.ibanOnDocument &&
    document.expectedIban &&
    document.ibanOnDocument.replace(/\s+/g, "") !== document.expectedIban.replace(/\s+/g, "")
  ) {
    reasons.push(
      reason(
        "documentRibRisk",
        "DOCUMENT_IBAN_MISMATCH",
        "IBAN document incohérent",
        "L'IBAN présent sur la facture ou le RIB diffère de la référence attendue.",
        20,
        {
          ibanOnDocument: maskIban(document.ibanOnDocument),
          expectedIban: maskIban(document.expectedIban),
        },
      ),
    );
  }

  if (document.ribChangeRequested) {
    reasons.push(
      reason(
        "documentRibRisk",
        "DOCUMENT_RIB_CHANGE_REQUEST",
        "Demande de changement RIB",
        "Le document porte une demande de modification des coordonnées bancaires.",
        13,
      ),
    );
  }

  if (document.beneficiaryNameOnDocument && document.expectedBeneficiaryName) {
    const similarity = simpleSimilarity(
      document.beneficiaryNameOnDocument,
      document.expectedBeneficiaryName,
    );
    if (similarity < 0.62) {
      reasons.push(
        reason(
          "documentRibRisk",
          "DOCUMENT_NAME_MISMATCH",
          "Nom document incohérent",
          "Le nom présent sur le document ne correspond pas au bénéficiaire attendu.",
          12,
          {
            beneficiaryNameOnDocument: document.beneficiaryNameOnDocument,
            expectedBeneficiaryName: document.expectedBeneficiaryName,
          },
        ),
      );
    }
  }

  if (document.suspiciousFormatting) {
    reasons.push(
      reason(
        "documentRibRisk",
        "DOCUMENT_FORMATTING_ANOMALY",
        "Anomalie de présentation",
        "Le document synthétique contient une incohérence de mise en forme ou de libellé.",
        7,
      ),
    );
  }

  return detectorResult({
    detector: "documentRibRisk",
    label: "Document / RIB / Invoice Fraud Check",
    status: "demo",
    maxScore: 24,
    dataUsed: ["document.iban", "document.expectedIban", "document.beneficiaryName", "formatting"],
    reasonCodes: reasons,
    explanationWhenEmpty: "Document cohérent avec les références attendues.",
  });
}
