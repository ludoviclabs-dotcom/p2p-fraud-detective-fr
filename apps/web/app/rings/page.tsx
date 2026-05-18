import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GraphExplorer } from "@/components/p2p-graph-explorer";
import { getP2PDataset } from "@/data/get-dataset";
import { formatDate, formatEuro, formatNumber } from "@/lib/p2p-demo-format";

export default function RingsPage() {
  const dataset = getP2PDataset();

  return (
    <div className="px-8 py-10">
      <div className="mb-1 text-xs uppercase tracking-wider text-[#5a6478]">
        Détection ML · démo statique
      </div>
      <h1 className="mb-1 text-3xl font-bold text-[#0f1b33] dark:text-white">
        Anneaux de fraude
      </h1>
      <p className="mb-6 text-sm text-[#5a6478]">
        Graphe vendor ↔ IBAN ↔ finding généré depuis le détecteur Python
        NetworkX. Les IBAN sont masqués avant publication; la page reste
        utilisable sur Vercel sans backend FastAPI.
      </p>

      <Card className="mb-4">
        <CardContent className="grid gap-3 md:grid-cols-5">
          <Metric label="Généré le" value={formatDate(dataset.generatedAt)} />
          <Metric label="Nœuds" value={formatNumber(dataset.nodes.length)} />
          <Metric label="Liens" value={formatNumber(dataset.edges.length)} />
          <Metric label="Findings" value={formatNumber(dataset.findings.length)} />
          <Metric label="Exposition" value={formatEuro(dataset.metrics.exposureEur)} />
        </CardContent>
      </Card>

      <Card className="mb-4 overflow-hidden">
        <CardHeader>
          <CardTitle>Graphe interactif WebGL</CardTitle>
        </CardHeader>
        <GraphExplorer dataset={dataset} />
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
            <span className="inline-block h-3 w-3 rounded-full bg-[#3E7CB1]" />
            IBAN masqué
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 rounded-full bg-[#a23e48]" />
            Finding critique
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wider text-[#5a6478]">{label}</div>
      <div className="mt-1 font-mono text-sm font-semibold text-[#0f1b33] dark:text-white">
        {value}
      </div>
    </div>
  );
}
