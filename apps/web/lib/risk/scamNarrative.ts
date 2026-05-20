import type { DetectorScore, P2PTransaction, ReasonCode } from "@/types/risk";
import { detectorResult, includesAny, reason } from "@/lib/risk/risk-utils";

const PATTERNS = {
  urgency: ["urgent", "vite", "immédiatement", "aujourd'hui", "bloqué", "dernière chance"],
  authority: ["banque", "conseiller", "police", "dgfip", "administration", "support", "direction", "ceo", "dirigeant"],
  secrecy: ["confidentiel", "ne prevenez personne", "ne prévenez personne", "secret", "discret"],
  secureAccount: ["compte securise", "compte sécurisé", "compte temporaire", "mise en securite", "mise en sécurité"],
  investment: ["rendement garanti", "crypto", "investissement", "opportunité", "trading", "plateforme"],
  romance: ["amour", "billet", "douane", "urgence familiale", "besoin d'aide", "rencontre"],
  technicalSupport: ["support technique", "prise en main", "anydesk", "teamviewer", "remote access"],
  administration: ["impot", "impôt", "dgfip", "amende", "tresor public", "trésor public"],
};

export function scamNarrative(transaction: P2PTransaction): DetectorScore {
  const text = transaction.narrative?.text ?? "";
  const reasons: ReasonCode[] = [];

  if (includesAny(text, PATTERNS.urgency)) {
    reasons.push(
      reason(
        "scamNarrative",
        "NARRATIVE_URGENCY",
        "Langage d'urgence",
        "Le libellé ou contexte contient des marqueurs d'urgence typiques d'une fraude par manipulation.",
        12,
      ),
    );
  }

  if (includesAny(text, PATTERNS.authority)) {
    reasons.push(
      reason(
        "scamNarrative",
        "NARRATIVE_AUTHORITY_IMPERSONATION",
        "Autorité usurpée",
        "La narration fait référence à une autorité ou un interlocuteur d'autorité.",
        12,
      ),
    );
  }

  if (includesAny(text, PATTERNS.secrecy)) {
    reasons.push(
      reason(
        "scamNarrative",
        "NARRATIVE_SECRECY",
        "Secret demandé",
        "Le scénario pousse l'utilisateur à ne pas vérifier par un canal connu.",
        11,
      ),
    );
  }

  if (includesAny(text, PATTERNS.secureAccount)) {
    reasons.push(
      reason(
        "scamNarrative",
        "NARRATIVE_SAFE_ACCOUNT",
        "Compte sécurisé invoqué",
        "La narration évoque un transfert vers un prétendu compte sécurisé, signal classique de faux conseiller.",
        16,
      ),
    );
  }

  if (includesAny(text, PATTERNS.investment)) {
    reasons.push(
      reason(
        "scamNarrative",
        "NARRATIVE_INVESTMENT",
        "Promesse d'investissement",
        "Le texte contient des termes associés aux arnaques investissement ou crypto.",
        14,
      ),
    );
  }

  if (includesAny(text, PATTERNS.romance)) {
    reasons.push(
      reason(
        "scamNarrative",
        "NARRATIVE_ROMANCE",
        "Scénario romance détecté",
        "La narration contient des marqueurs d'arnaque affective ou d'urgence familiale.",
        14,
      ),
    );
  }

  if (includesAny(text, PATTERNS.technicalSupport)) {
    reasons.push(
      reason(
        "scamNarrative",
        "NARRATIVE_TECH_SUPPORT",
        "Support technique suspect",
        "La narration évoque une prise en main ou un support technique non sollicité.",
        10,
      ),
    );
  }

  if (includesAny(text, PATTERNS.administration)) {
    reasons.push(
      reason(
        "scamNarrative",
        "NARRATIVE_ADMINISTRATION",
        "Administration invoquée",
        "La narration simule une demande administrative ou fiscale sensible.",
        8,
      ),
    );
  }

  return detectorResult({
    detector: "scamNarrative",
    label: "APP Fraud & Scam Narrative Detector",
    maxScore: 26,
    dataUsed: ["narrative.text", "payment context"],
    reasonCodes: reasons,
    explanationWhenEmpty: "Aucun motif narratif de manipulation détecté par les règles de démonstration.",
  });
}
