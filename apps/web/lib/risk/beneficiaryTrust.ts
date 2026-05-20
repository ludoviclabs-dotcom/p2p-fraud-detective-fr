import type { DetectorScore, IbanNameMatch, P2PTransaction, ReasonCode } from "@/types/risk";
import {
  detectorResult,
  ibanCountry,
  maskIban,
  reason,
  simpleSimilarity,
} from "@/lib/risk/risk-utils";

export function beneficiaryTrust(transaction: P2PTransaction): DetectorScore {
  const reasons: ReasonCode[] = [];
  const beneficiary = transaction.beneficiary;
  const country = beneficiary.ibanCountry ?? ibanCountry(beneficiary.iban);
  const usualCountry = transaction.payer.usualCountry ?? "FR";
  const expectedName =
    beneficiary.expectedName ??
    transaction.document?.expectedBeneficiaryName ??
    transaction.analystContext?.expectedCounterparty;
  const nameMatch = matchBeneficiaryName(beneficiary.name, expectedName);

  if (beneficiary.firstPayment) {
    reasons.push(
      reason(
        "beneficiaryTrust",
        "NEW_BENEFICIARY",
        "Nouveau bénéficiaire",
        "Le paiement cible un bénéficiaire jamais payé dans le jeu de données synthétique.",
        10,
        { beneficiaryId: beneficiary.id },
      ),
    );
  }

  if (beneficiary.addedHoursAgo !== undefined && beneficiary.addedHoursAgo <= 24) {
    reasons.push(
      reason(
        "beneficiaryTrust",
        "BENEFICIARY_RECENTLY_ADDED",
        "Bénéficiaire ajouté récemment",
        "Le bénéficiaire a été ajouté peu avant l'ordre de paiement.",
        12,
        { addedHoursAgo: beneficiary.addedHoursAgo },
      ),
    );
  }

  if ((beneficiary.accountAgeDays ?? 999) <= 7) {
    reasons.push(
      reason(
        "beneficiaryTrust",
        "NEW_IBAN",
        "IBAN récent",
        "L'IBAN n'a quasiment pas d'historique de confiance dans la démo.",
        8,
        { accountAgeDays: beneficiary.accountAgeDays ?? null, iban: maskIban(beneficiary.iban) },
      ),
    );
  }

  if ((beneficiary.sharedIbanCount ?? 0) >= 2) {
    reasons.push(
      reason(
        "beneficiaryTrust",
        "SHARED_IBAN",
        "IBAN partagé",
        "Le même IBAN est relié à plusieurs contreparties synthétiques.",
        14,
        { sharedIbanCount: beneficiary.sharedIbanCount ?? 0 },
      ),
    );
  }

  if (country && usualCountry && country !== usualCountry) {
    reasons.push(
      reason(
        "beneficiaryTrust",
        "UNUSUAL_IBAN_COUNTRY",
        "Pays IBAN inhabituel",
        "Le pays de l'IBAN diffère du pays habituel du payeur ou du fournisseur attendu.",
        8,
        { ibanCountry: country, usualCountry },
      ),
    );
  }

  if (nameMatch === "close_match") {
    reasons.push(
      reason(
        "beneficiaryTrust",
        "IBAN_NAME_CLOSE_MATCH",
        "Nom bénéficiaire proche",
        "Le nom saisi ressemble au nom attendu mais mérite une vérification humaine.",
        6,
        { beneficiaryName: beneficiary.name, expectedName: expectedName ?? null },
      ),
    );
  }

  if (nameMatch === "no_match") {
    reasons.push(
      reason(
        "beneficiaryTrust",
        "IBAN_NAME_MISMATCH",
        "Nom bénéficiaire incohérent",
        "Le nom bénéficiaire ne correspond pas au nom attendu pour le paiement.",
        18,
        { beneficiaryName: beneficiary.name, expectedName: expectedName ?? null },
      ),
    );
  }

  if (beneficiary.supplierRibChangedDaysAgo !== undefined && beneficiary.supplierRibChangedDaysAgo <= 7) {
    reasons.push(
      reason(
        "beneficiaryTrust",
        "SUPPLIER_RIB_RECENT_CHANGE",
        "Changement RIB fournisseur récent",
        "Le RIB fournisseur a été modifié dans une fenêtre courte avant le paiement.",
        18,
        { supplierRibChangedDaysAgo: beneficiary.supplierRibChangedDaysAgo },
      ),
    );
  }

  return detectorResult({
    detector: "beneficiaryTrust",
    label: "Beneficiary / IBAN Trust Check",
    maxScore: 28,
    dataUsed: ["beneficiary.name", "beneficiary.iban", "expectedName", "beneficiary history"],
    reasonCodes: reasons,
    explanationWhenEmpty: "Bénéficiaire et IBAN cohérents avec l'historique synthétique.",
  });
}

export function matchBeneficiaryName(
  beneficiaryName: string | undefined,
  expectedName: string | undefined,
): IbanNameMatch {
  if (!beneficiaryName || !expectedName) return "unavailable";
  const similarity = simpleSimilarity(beneficiaryName, expectedName);
  if (similarity >= 0.92) return "match";
  if (similarity >= 0.66) return "close_match";
  return "no_match";
}
