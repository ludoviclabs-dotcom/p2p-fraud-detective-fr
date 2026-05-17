"use client";

import { ControlPage } from "@/components/control-page";

export default function DecpRbePage() {
  return (
    <ControlPage
      config={{
        surtitle: "Contrôles statistiques",
        title: "DECP & RBE INPI",
        kicker: "Marchés publics DECP · Bénéficiaires effectifs RBE/INPI · Sapin 2 art. 17",
        description:
          "Croisement des fournisseurs avec deux référentiels critiques : DECP (Données Essentielles des Contrats de la Commande Publique) et RBE/INPI via Pappers quand le backend est configuré. En demo publique, les lignes sont synthétiques et doivent être distinguées des sources live. Le mode live s'active via `ENRICHMENT_MODE=live` et les clés nécessaires.",
        ruleIdMatchers: [
          "DECP_VENDOR_IN_PUBLIC_MARKET",
          "RBE_BENEFICIAL_OWNER_MATCH",
          "RBE_OPAQUE_STRUCTURE",
        ],
        titleMatchers: ["decp", "rbe", "marché public", "bénéficiaire"],
        regulations: [
          {
            label: "Sapin 2 art. 17",
            ref: "Procédures d'évaluation des tiers + cartographie risques corruption",
          },
          {
            label: "AMLD6",
            ref: "Vérification BO ≥ 25 % + PEP screening",
          },
          {
            label: "Directive Marchés Publics 2014/24/UE",
            ref: "Conflits d'intérêts dans la commande publique",
          },
        ],
        sources: [
          {
            name: "DECP v3",
            url: "data.economie.gouv.fr/decp_augmente",
            license: "ODbL 1.0 — mise à jour quotidienne",
          },
          {
            name: "Pappers (proxy RBE)",
            url: "api.pappers.fr/v2/entreprise",
            license: "Commercial (clé PAPPERS_API_KEY)",
          },
          {
            name: "INPI RNE (Etalab)",
            url: "data.inpi.fr/rne/rbe",
            license: "Etalab Open Licence — fallback Pappers",
          },
        ],
      }}
    />
  );
}
