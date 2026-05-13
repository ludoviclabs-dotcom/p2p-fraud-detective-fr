"use client";

import { useQuery } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import { useState } from "react";
import { api } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Schemas } from "@p2pfd/shared-types";

type RingsGraph = Schemas["RingsGraph"];

// Sigma.js exige le DOM/WebGL → dynamic import sans SSR
const RingsGraphView = dynamic(
  () => import("@/components/rings-graph").then((m) => m.RingsGraphView),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-[600px] items-center justify-center text-sm text-[#5a6478]">
        Chargement du graphe WebGL…
      </div>
    ),
  },
);

const SCENARIOS = [
  { name: "anneau_fraude", label: "🔴 Anneau de fraude (IBAN partagés)" },
  { name: "doublons_fournisseurs", label: "🟡 Doublons fournisseurs" },
  { name: "bec_iban_swap", label: "🔴 BEC IBAN swap" },
  { name: "fractionnement", label: "🟠 Fractionnement" },
  { name: "sanctions_ue", label: "🔴 Sanctions UE" },
];

export default function RingsPage() {
  const [scenario, setScenario] = useState("anneau_fraude");
  const [selected, setSelected] = useState<string | null>(null);

  const query = useQuery({
    queryKey: ["rings-graph", scenario],
    queryFn: () =>
      api.get<RingsGraph>(
        `/api/v1/rings?scenario=${encodeURIComponent(scenario)}`,
      ),
  });

  return (
    <div className="px-8 py-10">
      <div className="mb-1 text-xs uppercase tracking-wider text-[#5a6478]">
        Détection ML
      </div>
      <h1 className="mb-1 text-3xl font-bold text-[#0f1b33] dark:text-white">
        Anneaux de fraude
      </h1>
      <p className="mb-6 text-sm text-[#5a6478]">
        Graphe vendor ↔ IBAN — détection des anneaux par IBAN partagé entre
        fournisseurs. Rendu WebGL via <strong>sigma.js + graphology</strong>,
        layout ForceAtlas2 100 itérations.
      </p>

      <Card className="mb-4">
        <CardContent className="flex flex-wrap items-center gap-3">
          <label className="text-xs text-[#5a6478]">Scénario</label>
          <select
            value={scenario}
            onChange={(e) => {
              setScenario(e.target.value);
              setSelected(null);
            }}
            className="h-10 rounded-md border border-[#e1e5ee] bg-white px-3 text-sm"
          >
            {SCENARIOS.map((s) => (
              <option key={s.name} value={s.name}>
                {s.label}
              </option>
            ))}
          </select>
          {query.data ? (
            <div className="ml-auto flex gap-4 text-sm text-[#5a6478]">
              <span>
                <strong className="text-[#0f1b33]">{query.data.nodes.length}</strong>{" "}
                nœuds
              </span>
              <span>
                <strong className="text-[#0f1b33]">{query.data.edges.length}</strong>{" "}
                arêtes
              </span>
              <span>
                <strong className="text-[#a23e48]">
                  {query.data.n_shared_iban_rings}
                </strong>{" "}
                anneaux
              </span>
              <span>
                Plus grand cluster :{" "}
                <strong className="text-[#0f1b33]">
                  {query.data.largest_cluster_size}
                </strong>
              </span>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card className="mb-4 overflow-hidden">
        <CardHeader>
          <CardTitle>🕸️ Graphe interactif (WebGL)</CardTitle>
        </CardHeader>
        {query.isLoading ? (
          <div className="flex h-[600px] items-center justify-center text-sm text-[#5a6478]">
            Génération du graphe NetworkX côté backend…
          </div>
        ) : query.error ? (
          <div className="p-4 text-sm text-[#a23e48]">
            API indisponible : {(query.error as Error).message}
          </div>
        ) : query.data && query.data.nodes.length === 0 ? (
          <div className="p-4 text-sm text-[#5a6478]">
            Aucun anneau détecté pour ce scénario. Essayer « Anneau de fraude ».
          </div>
        ) : query.data ? (
          <RingsGraphView data={query.data} onSelect={setSelected} />
        ) : null}
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Légende</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 rounded-full bg-[#1f3a6e]" />
            Fournisseur (vendor_name)
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 rounded-full bg-[#e5a93a]" />
            IBAN partagé
          </div>
          {selected ? (
            <div className="ml-auto rounded bg-[#f4f6fa] px-3 py-1 font-mono text-xs">
              Sélection : {selected}
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
