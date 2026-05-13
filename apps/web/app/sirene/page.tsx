"use client";

import { ControlPage } from "@/components/control-page";

export default function SirenePage() {
  return (
    <ControlPage
      config={{
        surtitle: "Données",
        title: "Contrôle Sirene",
        kicker: "Validation INSEE en temps réel — clé Luhn + statut actif/radié",
        description:
          "Croisement des SIREN fournisseurs avec le référentiel Sirene v3 de l'INSEE. Détections : SIREN invalide (clé de Luhn KO), entreprise radiée, dénomination Sirene différente de celle saisie dans le master (potentiel doublon ou erreur de saisie), code APE absent ou non cohérent avec le compte de tiers. Cache `requests-cache` 30 jours pour respecter les quotas API Sirene v3 (30 req/s).",
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
