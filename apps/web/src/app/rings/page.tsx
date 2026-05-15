import { getP2PDataset } from "@/data/get-dataset";
import { formatDate } from "@/lib/format";
import { GraphExplorer } from "@/components/graph/graph-explorer";

export default function RingsPage() {
  const dataset = getP2PDataset();

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-6">
      <header>
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#1F3A6E]">
          Détection ML
        </p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight text-[#141927]">
          Anneaux de fraude
        </h1>
        <p className="mt-4 max-w-3xl text-base leading-7 text-[#5A6478]">
          Graphe vendor ↔ IBAN ↔ finding. Les coordonnées bancaires sont masquées
          avant publication; le calcul reste produit par le moteur Python NetworkX.
        </p>
        <p className="mono mt-3 text-xs text-[#5A6478]">
          Dataset statique généré le {formatDate(dataset.generatedAt)}
        </p>
      </header>

      <GraphExplorer dataset={dataset} />
    </div>
  );
}
