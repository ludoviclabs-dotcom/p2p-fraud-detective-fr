import type { P2PTransaction } from "@/types/risk";

const MIN_MASK_LENGTH = 8;

export function maskSensitiveValue(value: string | undefined | null): string {
  if (!value) return "n/a";
  const compact = value.replace(/\s+/g, "");
  if (compact.length <= MIN_MASK_LENGTH) return compact;
  return `${compact.slice(0, 4)}••••${compact.slice(-4)}`;
}

function redactQrPayload(payload: string): string {
  return payload.replace(/[A-Z]{2}[0-9A-Z]{12,34}/g, (match) => maskSensitiveValue(match));
}

export function redactTransaction(transaction: P2PTransaction): P2PTransaction {
  return {
    ...transaction,
    beneficiary: {
      ...transaction.beneficiary,
      iban: maskSensitiveValue(transaction.beneficiary.iban),
      expectedIban: transaction.beneficiary.expectedIban
        ? maskSensitiveValue(transaction.beneficiary.expectedIban)
        : undefined,
    },
    qr: transaction.qr
      ? {
          ...transaction.qr,
          payload: redactQrPayload(transaction.qr.payload),
          expectedIban: transaction.qr.expectedIban
            ? maskSensitiveValue(transaction.qr.expectedIban)
            : undefined,
        }
      : undefined,
    document: transaction.document
      ? {
          ...transaction.document,
          ibanOnDocument: transaction.document.ibanOnDocument
            ? maskSensitiveValue(transaction.document.ibanOnDocument)
            : undefined,
          expectedIban: transaction.document.expectedIban
            ? maskSensitiveValue(transaction.document.expectedIban)
            : undefined,
        }
      : undefined,
  };
}
