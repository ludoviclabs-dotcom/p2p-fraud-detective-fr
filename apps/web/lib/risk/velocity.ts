import type { DetectorScore, P2PTransaction, ReasonCode } from "@/types/risk";
import { detectorResult, reason } from "@/lib/risk/risk-utils";

export function velocity(transaction: P2PTransaction): DetectorScore {
  const reasons: ReasonCode[] = [];
  const average = transaction.payer.historicalAverageAmount ?? 0;
  const threshold = transaction.payer.approvalThresholdEur;
  const recentPayments = transaction.payer.recentPaymentCount24h ?? 0;
  const newBeneficiaries = transaction.payer.recentNewBeneficiaries24h ?? 0;
  const splitPayments = transaction.payer.splitPaymentsCount24h ?? 0;

  if (average > 0 && transaction.amount >= average * 3) {
    reasons.push(
      reason(
        "velocity",
        "UNUSUAL_AMOUNT",
        "Montant inhabituel",
        "Le montant dépasse fortement le profil historique synthétique du payeur.",
        12,
        { amount: transaction.amount, historicalAverageAmount: average },
      ),
    );
  }

  if ((transaction.isInstant || transaction.rail === "SEPA_INSTANT") && transaction.beneficiary.firstPayment) {
    reasons.push(
      reason(
        "velocity",
        "NEW_BENEFICIARY_INSTANT_PAYMENT",
        "Nouveau bénéficiaire + virement instantané",
        "La combinaison bénéficiaire nouveau et paiement instantané augmente la pression opérationnelle.",
        14,
        { rail: transaction.rail },
      ),
    );
  }

  if (recentPayments >= 5) {
    reasons.push(
      reason(
        "velocity",
        "HIGH_24H_PAYMENT_VELOCITY",
        "Volume 24h élevé",
        "Le payeur a initié plusieurs paiements dans une fenêtre courte.",
        8,
        { recentPaymentCount24h: recentPayments },
      ),
    );
  }

  if (newBeneficiaries >= 2) {
    reasons.push(
      reason(
        "velocity",
        "MULTIPLE_NEW_BENEFICIARIES",
        "Plusieurs nouveaux bénéficiaires",
        "Plusieurs bénéficiaires ont été ajoutés dans les dernières 24 heures.",
        10,
        { recentNewBeneficiaries24h: newBeneficiaries },
      ),
    );
  }

  if (splitPayments >= 2) {
    reasons.push(
      reason(
        "velocity",
        "SPLIT_PAYMENTS",
        "Fractionnement simulé",
        "Plusieurs paiements rapprochés suggèrent un contournement de seuil.",
        12,
        { splitPaymentsCount24h: splitPayments },
      ),
    );
  }

  if (threshold && transaction.amount >= threshold * 0.9 && transaction.amount < threshold) {
    reasons.push(
      reason(
        "velocity",
        "JUST_UNDER_APPROVAL_THRESHOLD",
        "Juste sous seuil",
        "Le montant est positionné sous le seuil d'approbation configuré.",
        9,
        { amount: transaction.amount, approvalThresholdEur: threshold },
      ),
    );
  }

  return detectorResult({
    detector: "velocity",
    label: "Velocity Checks",
    maxScore: 24,
    dataUsed: ["amount", "rail", "payer history", "approval threshold"],
    reasonCodes: reasons,
    explanationWhenEmpty: "Pas d'anomalie de vélocité notable dans la fenêtre synthétique.",
  });
}
