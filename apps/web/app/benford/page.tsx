"use client";

import { ControlPage } from "@/components/control-page";

export default function BenfordPage() {
  return (
    <ControlPage
      config={{
        surtitle: "Contrôles statistiques",
        title: "Loi de Benford",
        kicker: "Scoping orienté risque — Newcomb-Benford F1D / F2D / LD",
        description:
          "La loi de Benford (Newcomb-Benford) prédit la distribution naturelle des premiers chiffres significatifs dans un ensemble de montants financiers : 1 apparaît ~30 %, 9 seulement ~4.6 %. Un écart significatif (test du χ² ou Kolmogorov-Smirnov, p < 0.05) signale une potentielle manipulation des montants. L'analyse F1D (premier chiffre), F2D (deux premiers chiffres) et LD (dernier chiffre) augmente la précision. Recommandé minimum 1 000 factures pour avoir une puissance statistique exploitable.",
        ruleIdMatchers: ["BENFORD", "F1D", "F2D"],
        titleMatchers: ["benford"],
        regulations: [
          { label: "ISA 240", ref: "Responsabilités de l'auditeur — fraude" },
          {
            label: "AS 2401",
            ref: "PCAOB — Consideration of Fraud in a Financial Statement Audit",
          },
          {
            label: "Sapin 2 art. 17",
            ref: "Procédures d'évaluation des tiers",
          },
        ],
      }}
    />
  );
}
