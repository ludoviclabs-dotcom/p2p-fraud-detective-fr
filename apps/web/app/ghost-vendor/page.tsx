"use client";

import { ControlPage } from "@/components/control-page";

export default function GhostVendorPage() {
  return (
    <ControlPage
      config={{
        surtitle: "Contrôles master data",
        title: "Ghost vendor — fournisseur fantôme",
        kicker:
          "Faisceau : création récente + 1re facture immédiate + sans PO + self-approved + SIREN invérifiable",
        description:
          "Détection des fiches fournisseurs créées pour capter des paiements : première facture émise quelques jours après la création de la fiche, aucune commande rattachée, fiche créée et approuvée par le même utilisateur, SIREN absent du répertoire Sirene. Chaque signal isolé est faible — le détecteur agrège le faisceau (GV_COMBO) et l'escalade en CRITICAL au-delà de 3 signaux cumulés. Couvre la création initiale frauduleuse, angle mort des contrôles limités au changement d'IBAN (ACFE Fraud Tree : Billing schemes → Shell company).",
        ruleIdMatchers: ["GV_", "GHOST"],
        titleMatchers: ["fantôme", "ghost", "faux fournisseur"],
        regulations: [
          { label: "ISA 240", ref: "Fictitious vendors — journal entry & master data testing" },
          { label: "Sapin 2 art. 17", ref: "Cartographie des risques de corruption" },
          { label: "Code pénal 432-14", ref: "Favoritisme (secteur public)" },
        ],
        sources: [
          {
            name: "INSEE Sirene v3",
            url: "api.insee.fr/entreprises/sirene/V3",
            license: "ODbL 1.0",
          },
          {
            name: "Bodacc (procédures collectives)",
            url: "bodacc-datadila.opendatasoft.com",
            license: "Licence Ouverte 2.0",
          },
        ],
      }}
    />
  );
}
