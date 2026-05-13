"use client";

import { ControlPage } from "@/components/control-page";

export default function StructuringPage() {
  return (
    <ControlPage
      config={{
        surtitle: "Contrôles statistiques",
        title: "Fractionnement / sous-seuils",
        kicker: "Détection clusters intentionnels juste sous seuils COSI",
        description:
          "Le structuring (smurfing) est le fractionnement délibéré d'une opération en plusieurs versements sous les seuils déclaratifs COSI pour échapper à la déclaration systématique à Tracfin. Seuils français : 1 000 € / opération (transmission de fonds par espèces, art. D. 561-31-1 CMF), 2 000 € cumulés / client / mois, 10 000 € cumulés / mois / compte (dépôts ou retraits espèces). Détection : cluster d'opérations 900-999 €, répétition de montants juste sous-seuils, coefficient de variation faible sur fenêtre glissante 30 jours.",
        ruleIdMatchers: ["UNDER_THRESHOLD", "STRUCTURING", "SMURFING"],
        titleMatchers: ["fractionn", "sous-seuil", "smurf", "structur"],
        regulations: [
          {
            label: "D. 561-31-1 CMF",
            ref: "COSI transmission de fonds — seuil 1 000 €",
          },
          {
            label: "R. 561-31-2 CMF",
            ref: "COSI dépôts/retraits espèces — seuil 10 000 €/mois",
          },
          {
            label: "Tracfin doctrine 2024-2025",
            ref: "Tome III — typologies persistantes",
          },
        ],
      }}
    />
  );
}
