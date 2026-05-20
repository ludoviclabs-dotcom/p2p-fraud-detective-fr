import { NextResponse } from "next/server";

import { buildDemoTopVendors } from "@/lib/demo-cockpit";
import { proxyApiV1Request } from "@/lib/api-v1-proxy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const upstream = await proxyApiV1Request(request, "/api/v1/scenarios");
  if (upstream) {
    const payload = await readJson(upstream);
    if (upstream.ok && Array.isArray(payload) && payload.length > 0) {
      return NextResponse.json(payload);
    }
  }

  return NextResponse.json(buildDemoScenarioMeta());
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.clone().json();
  } catch {
    return null;
  }
}

function buildDemoScenarioMeta() {
  const vendors = buildDemoTopVendors(undefined, 6);
  const vendor = (index: number) => vendors[index % vendors.length]?.vendor_id ?? "V00444";

  return [
    {
      name: "demo_shared_iban_ring",
      title: "Anneau IBAN partage",
      short: "Plusieurs fournisseurs synthétiques convergent vers un même IBAN.",
      severity: "critical",
      pillar: "Graphe fraude",
      detectors: ["network_rings", "master_data_changes"],
      target_vendor: vendor(0),
      storyline:
        "Le graphe détecte un IBAN utilisé par plusieurs fournisseurs sans lien métier évident. La revue attendue consiste à ouvrir le fournisseur 360, vérifier les connexions IBAN et documenter la décision.",
    },
    {
      name: "demo_supplier_rib_change",
      title: "Changement RIB fournisseur sensible",
      short: "Modification récente du RIB avant paiement fournisseur.",
      severity: "high",
      pillar: "Procure-to-Pay",
      detectors: ["master_data_changes", "score_explorer"],
      target_vendor: vendor(1),
      storyline:
        "Un fournisseur à exposition élevée présente une modification de coordonnées bancaires proche de la date de paiement. Le contrôle doit produire une preuve de validation quatre yeux.",
    },
    {
      name: "demo_threshold_structuring",
      title: "Fractionnement sous seuil",
      short: "Paiements rapprochés juste sous seuil d'approbation.",
      severity: "high",
      pillar: "Contrôle interne",
      detectors: ["under_thresholds", "score_explorer"],
      target_vendor: vendor(2),
      storyline:
        "Plusieurs factures synthétiques restent sous le seuil d'approbation et forment un pattern de contournement. L'auditeur vérifie l'historique et l'exposition cumulée.",
    },
    {
      name: "demo_duplicate_invoice",
      title: "Doublon facture exact ou fuzzy",
      short: "Factures proches par montant, fournisseur et date.",
      severity: "medium",
      pillar: "Comptes fournisseurs",
      detectors: ["duplicates"],
      target_vendor: vendor(3),
      storyline:
        "Un rapprochement exact ou fuzzy remonte plusieurs factures similaires. La démo montre comment ouvrir le score et qualifier le case comme confirmé ou faux positif.",
    },
    {
      name: "demo_sanctions_pep",
      title: "Sanctions / PEP fournisseur",
      short: "Signal AML synthétique sur fournisseur sensible.",
      severity: "critical",
      pillar: "Conformité",
      detectors: ["sanctions", "pep"],
      target_vendor: vendor(4),
      storyline:
        "Un fournisseur synthétique est associé à un signal sanctions ou PEP. Le parcours attendu est une escalade conformité avant toute recommandation de paiement.",
    },
    {
      name: "demo_anomaly_ml",
      title: "Anomalie ML de montant",
      short: "Montant atypique par rapport à l'historique fournisseur.",
      severity: "medium",
      pillar: "Anomalies",
      detectors: ["score_explorer"],
      target_vendor: vendor(5),
      storyline:
        "Le score remonte un paiement atypique mais non bloquant. L'objectif est de montrer une revue documentée, sans promesse de détection production-grade.",
    },
  ];
}
