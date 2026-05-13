"use client";

import { ControlPage } from "@/components/control-page";

export default function DuplicatesPage() {
  return (
    <ControlPage
      config={{
        surtitle: "Contrôles statistiques",
        title: "Doublons fournisseurs",
        kicker: "Bucketing montant ± 0.01 € + fenêtre date + RapidFuzz token_set_ratio",
        description:
          "Détection des paiements en double : montant identique (±0.01 €), date proche (fenêtre paramétrable, 30 jours par défaut) + fournisseurs fuzzy-matchés (RapidFuzz token_set_ratio ≥ 92). Pattern classique de fraude P2P — une facture est traitée et payée deux fois (par exemple via deux entrées master fournisseurs proches). L'enrichissement INPI-SIRENE croise les SIREN pour réduire les faux positifs (PME du même groupe avec dénominations légèrement différentes).",
        ruleIdMatchers: ["DUPLICATE", "DOUBLON"],
        titleMatchers: ["doublon", "duplicate"],
        regulations: [
          { label: "ISA 240", ref: "Detection of duplicate payments" },
          {
            label: "ACPR Lignes directrices LCB-FT",
            ref: "Vigilance constante sur les transactions",
          },
        ],
      }}
    />
  );
}
