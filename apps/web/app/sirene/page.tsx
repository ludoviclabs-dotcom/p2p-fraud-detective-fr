"use client";

import { ControlPage } from "@/components/control-page";

export default function SirenePage() {
  return (
    <ControlPage
      config={{
        surtitle: "Données",
        title: "Contrôle Sirene",
        kicker: "Validation INSEE configurable — clé Luhn + statut actif/radié",
        description:
          "Croisement des SIREN fournisseurs avec le référentiel Sirene v3 de l'INSEE quand le backend dispose d'un token. En demo publique, les cas affichés sont synthétiques. Détections : SIREN invalide, entreprise radiée, dénomination différente, code APE absent ou incohérent. Cache `requests-cache` 30 jours côté FastAPI pour respecter les quotas API Sirene v3.",
        ruleIdMatchers: ["SIRENE", "SIREN_INVALID", "RADIE"],
        titleMatchers: ["sirene", "radié", "luhn"],
        regulations: [
          {
            label: "INSEE Sirene v3",
            ref: "api.insee.fr/entreprises/sirene/V3",
          },
          {
            label: "ODbL Open Database License",
            ref: "Licence des données Sirene",
          },
        ],
        sources: [
          {
            name: "INSEE Sirene v3",
            url: "api.insee.fr/entreprises/sirene/V3",
            license: "ODbL 1.0 — mise à jour quotidienne",
          },
        ],
      }}
    />
  );
}
