import type { Metadata } from "next";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export const metadata: Metadata = {
  title: "Méthodologie — P2P Fraud Detective FR",
};

export default function MethodologyPage() {
  return (
    <div className="px-8 py-10">
      <div className="mb-1 text-xs uppercase tracking-wider text-[#5a6478]">
        Gouvernance
      </div>
      <h1 className="mb-1 text-3xl font-bold text-[#0f1b33] dark:text-white">
        Méthodologie
      </h1>
      <p className="mb-4 text-sm text-[#5a6478]">
        Documentation transparente de l'approche analytique, des seuils de
        détection, des métriques de validation et des limites connues.
        Conforme aux exigences de transparence <strong>AI Act art. 50</strong>.
      </p>

      <div className="mb-6 rounded-md border border-[#f0dca0] bg-[#fff8e1] px-4 py-3 text-xs text-[#7a5d12]">
        <strong>Métriques calculées sur dataset synthétique étiqueté</strong>{" "}
        (générateur reproductible{" "}
        <code className="rounded bg-white/60 px-1">p2p_fraud.synthetic</code>,
        échantillon public{" "}
        <code className="rounded bg-white/60 px-1">data/samples/sample_5k.csv</code>).
        Aucune validation rétrospective sur données client réelles n'est
        publiée à ce jour : tout claim de performance en production nécessite
        un benchmark client préalable.
      </div>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>🎯 Objectifs et périmètre</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm leading-relaxed">
          <p>
            <strong>P2P Fraud Detective FR</strong> est un démonstrateur
            d'audit du cycle Procure-to-Pay orienté détection de fraude :
            sous-seuils, doublons, BEC (Business Email Compromise), sanctions,
            anneaux IBAN. Aligné sur les méthodologies AML/CFT et les contrôles
            attendus en audit P2P public : <strong>ISA 240</strong>,{" "}
            <strong>AS 2401</strong>, <strong>Sapin 2</strong>, <strong>LCB-FT</strong>,{" "}
            <strong>DORA art. 28</strong>, <strong>AMLD6</strong>.
          </p>
          <p>
            Pertinent pour les ETI 500 M€-2 Md€, cabinets d'audit mid-tier,
            fonctions publiques et organismes de contrôle (DGFiP, Tracfin, IGF,
            Cour des comptes, CRC régionales).
          </p>
        </CardContent>
      </Card>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>📡 Sources de données publiques</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#e1e5ee] text-left text-xs text-[#5a6478]">
                <th className="py-2">Source</th>
                <th className="py-2">Endpoint</th>
                <th className="py-2">Licence</th>
                <th className="py-2">Fréquence</th>
              </tr>
            </thead>
            <tbody className="text-xs">
              {[
                ["INSEE Sirene v3", "api.insee.fr/entreprises/sirene/V3", "ODbL 1.0", "Quotidienne"],
                ["DECP v3", "data.economie.gouv.fr/decp_augmente", "ODbL 1.0", "Quotidienne"],
                ["Pappers (RBE)", "api.pappers.fr/v2/entreprise", "Commercial", "Temps réel"],
                ["OpenSanctions Yente", "api.opensanctions.org/match/sanctions", "CC-BY 4.0", "Hebdomadaire"],
                ["UE consolidée", "via Yente", "EU Open Data", "Quotidienne"],
                ["OFAC SDN", "via Yente", "US Public Domain", "Hebdomadaire"],
                ["Trésor FR (gels)", "tresor.economie.gouv.fr", "Légifrance", "Quotidienne"],
              ].map(([src, ep, lic, freq]) => (
                <tr key={src} className="border-b border-[#e1e5ee]">
                  <td className="py-2 font-medium">{src}</td>
                  <td className="py-2 font-mono">{ep}</td>
                  <td className="py-2">{lic}</td>
                  <td className="py-2">{freq}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>⚖️ Seuils statistiques</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#e1e5ee] text-left text-xs text-[#5a6478]">
                <th className="py-2">Détecteur</th>
                <th className="py-2">Seuil</th>
                <th className="py-2">Référence</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-[#e1e5ee]">
                <td className="py-2 font-medium">Benford</td>
                <td className="py-2 text-xs">KS p &lt; 0.05 · min 1 000 factures</td>
                <td className="py-2 text-xs text-[#5a6478]">ISA 240</td>
              </tr>
              <tr className="border-b border-[#e1e5ee]">
                <td className="py-2 font-medium">Doublons fuzzy</td>
                <td className="py-2 text-xs">RapidFuzz WRatio ≥ 92 · fenêtre 30 j</td>
                <td className="py-2 text-xs text-[#5a6478]">ACPR LCB-FT</td>
              </tr>
              <tr className="border-b border-[#e1e5ee]">
                <td className="py-2 font-medium">Sous-seuils COSI</td>
                <td className="py-2 text-xs">
                  900-999 €, cumul mensuel &gt; 2 000 € / 10 000 €
                </td>
                <td className="py-2 text-xs text-[#5a6478]">
                  D. 561-31-1 / R. 561-31-2 CMF
                </td>
              </tr>
              <tr className="border-b border-[#e1e5ee]">
                <td className="py-2 font-medium">Isolation Forest</td>
                <td className="py-2 text-xs">
                  contamination 0.05 · n_estimators 200
                </td>
                <td className="py-2 text-xs text-[#5a6478]">scikit-learn 1.5</td>
              </tr>
              <tr className="border-b border-[#e1e5ee]">
                <td className="py-2 font-medium">Anneaux IBAN</td>
                <td className="py-2 text-xs">
                  Cluster ≥ 3 vendors partageant un IBAN
                </td>
                <td className="py-2 text-xs text-[#5a6478]">NetworkX 3.3</td>
              </tr>
              <tr className="border-b border-[#e1e5ee]">
                <td className="py-2 font-medium">Sanctions matching</td>
                <td className="py-2 text-xs">RapidFuzz WRatio ≥ 90</td>
                <td className="py-2 text-xs text-[#5a6478]">OpenSanctions Yente</td>
              </tr>
            </tbody>
          </table>
        </CardContent>
      </Card>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>🧪 Métriques F1 (validation sur ground truth)</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#e1e5ee] text-left text-xs text-[#5a6478]">
                <th className="py-2">Détecteur</th>
                <th className="py-2">F1</th>
                <th className="py-2">Précision</th>
                <th className="py-2">Rappel</th>
                <th className="py-2">Dataset</th>
              </tr>
            </thead>
            <tbody className="text-xs">
              {[
                ["BEC (master_data)", "0.91", "0.94", "0.88", "Synthetic master_data_events"],
                ["Doublons fuzzy", "0.87", "0.92", "0.83", "AMLSim 50k (synthétique)"],
                ["Sous-seuils", "0.84", "0.89", "0.80", "Synthetic structuring"],
                ["Anneaux IBAN", "1.0", "1.0", "1.0", "Synthetic anneau_fraude"],
                ["Sanctions", "0.95", "0.97", "0.93", "Snapshot listes publiques 2024-2026"],
              ].map(([d, f1, p, r, ds]) => (
                <tr key={d} className="border-b border-[#e1e5ee]">
                  <td className="py-2 font-medium">{d}</td>
                  <td className="py-2 font-mono text-[#3e7c5a]">{f1}</td>
                  <td className="py-2 font-mono">{p}</td>
                  <td className="py-2 font-mono">{r}</td>
                  <td className="py-2 text-[#5a6478]">{ds}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-3 text-xs text-[#5a6478]">
            Voir <code>docs/benchmark_results.json</code> pour les métriques
            détaillées par configuration de seuil.
          </p>
        </CardContent>
      </Card>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>⚠️ Limites connues</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <ul className="list-disc space-y-1 pl-5">
            <li>
              Loi de Benford : non fiable sous 1 000 factures (puissance
              statistique insuffisante)
            </li>
            <li>
              Liste PEP open-source : couverture élus locaux français estimée
              60-70 %
            </li>
            <li>
              DECP : seuils minimaux légaux (25 k€ TTC marchés, 90 k€ DSP) —
              petits marchés non couverts
            </li>
            <li>
              Pappers free tier : ~ 100 requêtes/jour — pilote ETI avec
              10 000 fournisseurs nécessite plan payant ou self-host RNE
            </li>
            <li>
              Streamlit Cloud (legacy v0.5) : limité à une session — pour
              multi-user persistant, utiliser FastAPI + PostgreSQL Aiven
            </li>
            <li>
              Pas de connecteur ERP natif (SAP/Sage/Cegid) — extraction CSV
              manuelle requise
            </li>
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>🏗️ Architecture (v2 Next.js + FastAPI)</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="overflow-x-auto rounded bg-[#f4f6fa] p-3 text-xs">
            {`                  ┌────────────────────────────────────┐
                  │  VISITEUR (recruteur / pilote ETI) │
                  └──────────────────┬─────────────────┘
                                     │ HTTPS
                                     ▼
              ┌──────────────────────────────────────┐
              │  Vercel free (Next.js 15)            │
              │  ├─ App Router : 21 routes           │
              │  ├─ shadcn-style UI + Tailwind v4    │
              │  ├─ Recharts + sigma.js + visx       │
              │  ├─ TanStack Query/Table             │
              │  ├─ /api/auth/* (OIDC proxy)         │
              │  └─ /api/uploads (multipart proxy)   │
              └──────────────┬───────────────────────┘
                             │ REST + SSE
                             ▼
            ┌──────────────────────────────────────┐
            │ HF Spaces (FastAPI Docker free 16GB) │
            │ ├─ src/p2p_fraud/** (Python pur)     │
            │ ├─ 26 endpoints /api/v1/*            │
            │ ├─ NetworkX + Pandas + scikit-learn  │
            │ ├─ Audit log SHA-256 + Ed25519       │
            │ ├─ OIDC discovery + JWKS             │
            │ └─ weasyprint PDF                    │
            └──────────┬───────────────────────────┘
                       │ SQLAlchemy
                       ▼
              ┌────────────────────────┐
              │ Neon free (PG 16,      │
              │  0.5 GB, scale-to-zero)│
              └────────────────────────┘`}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
}
