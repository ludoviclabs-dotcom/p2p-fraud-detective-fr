import type { DetectorScore, P2PTransaction, ReasonCode } from "@/types/risk";
import { detectorResult, reason } from "@/lib/risk/risk-utils";

export function deviceSession(transaction: P2PTransaction): DetectorScore {
  const reasons: ReasonCode[] = [];
  const device = transaction.device;
  if (!device) {
    return detectorResult({
      detector: "deviceSession",
      label: "Device & Session Risk Lite",
      status: "demo",
      maxScore: 18,
      dataUsed: ["device telemetry unavailable"],
      reasonCodes: reasons,
      explanationWhenEmpty: "Aucun signal device fourni pour ce scénario.",
    });
  }

  if (device.seenBefore === false) {
    reasons.push(
      reason(
        "deviceSession",
        "NEW_DEVICE",
        "Nouvel appareil",
        "L'appareil n'a jamais été vu dans l'historique synthétique.",
        9,
        { deviceId: device.id },
      ),
    );
  }

  if (device.ipCountry && device.usualCountry && device.ipCountry !== device.usualCountry) {
    reasons.push(
      reason(
        "deviceSession",
        "UNUSUAL_IP_COUNTRY",
        "Pays IP inhabituel",
        "Le pays IP de session diffère du pays habituel du payeur.",
        8,
        { ipCountry: device.ipCountry, usualCountry: device.usualCountry },
      ),
    );
  }

  if (device.remoteAccessDetected) {
    reasons.push(
      reason(
        "deviceSession",
        "REMOTE_ACCESS_FLAG",
        "Prise en main à distance",
        "Le scénario simule un indicateur de prise en main à distance.",
        13,
      ),
    );
  }

  if (device.impossibleTravel) {
    reasons.push(
      reason(
        "deviceSession",
        "IMPOSSIBLE_TRAVEL",
        "Impossible travel simulé",
        "Deux localisations de session sont incompatibles avec un trajet réaliste.",
        10,
      ),
    );
  }

  if (device.vpnOrProxy) {
    reasons.push(
      reason(
        "deviceSession",
        "VPN_OR_PROXY",
        "VPN/proxy simulé",
        "La session est marquée comme proxy ou VPN dans les données de démonstration.",
        6,
      ),
    );
  }

  if (device.phoneChangedHoursAgo !== undefined && device.phoneChangedHoursAgo <= 24) {
    reasons.push(
      reason(
        "deviceSession",
        "PHONE_RECENTLY_CHANGED",
        "Téléphone modifié récemment",
        "Le téléphone du payeur a été modifié avant le paiement.",
        10,
        { phoneChangedHoursAgo: device.phoneChangedHoursAgo },
      ),
    );
  }

  if (device.emailChangedHoursAgo !== undefined && device.emailChangedHoursAgo <= 24) {
    reasons.push(
      reason(
        "deviceSession",
        "EMAIL_RECENTLY_CHANGED",
        "Email modifié récemment",
        "L'email du payeur a été modifié avant le paiement.",
        8,
        { emailChangedHoursAgo: device.emailChangedHoursAgo },
      ),
    );
  }

  return detectorResult({
    detector: "deviceSession",
    label: "Device & Session Risk Lite",
    status: "demo",
    maxScore: 22,
    dataUsed: ["device.id", "ipCountry", "remoteAccess", "account change flags"],
    reasonCodes: reasons,
    explanationWhenEmpty: "Session cohérente avec l'historique synthétique du payeur.",
  });
}
