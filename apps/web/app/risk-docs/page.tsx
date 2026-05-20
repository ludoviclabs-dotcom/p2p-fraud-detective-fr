import Link from "next/link";
import {
  ArrowRight,
  BookOpen,
  Braces,
  FileCheck2,
  GitBranch,
  Info,
  Library,
  ShieldCheck,
  TerminalSquare,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const glossary = [
  ["APP fraud", "Authorized Push Payment fraud: la victime autorise elle-même le paiement sous manipulation."],
  ["Reason code", "Code explicable qui documente pourquoi un score augmente."],
  ["Risk decision", "Recommandation de traitement: ALLOW, MONITOR, MANUAL_REVIEW ou BLOCK_RECOMMENDED."],
  ["Risk level", "Niveau lisible: LOW, MEDIUM, HIGH ou CRITICAL."],
  ["VoP simulée", "Vérification nom/IBAN de démonstration: match, close_match, no_match ou unavailable."],
  ["Mule account", "Compte relais utilisé pour recevoir ou disperser des fonds frauduleux."],
  ["Evidence pack", "Dossier exportable contenant transaction, score, raisons, graphe, timeline et notes."],
  ["Source locale de démo", "Scénarios synthétiques intégrés utilisés si la source Hugging Face n'est pas configurée ou indisponible."],
];

const reasonFamilies = [
  ["Beneficiary / IBAN", "NEW_BENEFICIARY, IBAN_NAME_MISMATCH, SUPPLIER_RIB_RECENT_CHANGE"],
  ["Narrative APP", "NARRATIVE_URGENCY, NARRATIVE_SAFE_ACCOUNT, NARRATIVE_INVESTMENT"],
  ["Velocity", "UNUSUAL_AMOUNT, NEW_BENEFICIARY_INSTANT_PAYMENT, SPLIT_PAYMENTS"],
  ["Device", "NEW_DEVICE, UNUSUAL_IP_COUNTRY, REMOTE_ACCESS_FLAG"],
  ["QR", "QR_IBAN_MISMATCH, QR_TYPOSQUATTED_DOMAIN, QR_SUSPICIOUS_URL"],
  ["Graph", "GRAPH_HIGH_RISK_CLUSTER, GRAPH_MULE_LINKED_PAYERS, GRAPH_SHARED_IBAN"],
  ["AML", "SANCTIONS_POSSIBLE_HIT, PEP_POSSIBLE_HIT, HIGH_RISK_COUNTRY"],
];

export default function RiskDocsPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#667085]">
            Documentation produit
          </p>
          <h1 className="mt-2 text-3xl font-bold text-[#08111f] dark:text-white">
            Docs & glossaire du Workbench
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-[#667085]">
            Guide de test, API, modèle de scoring, glossaire et limites de la
            démonstration. Cette page aide un recruteur ou un évaluateur à tester
            l'outil sans contexte préalable.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            href="/risk-test-lab"
            className="inline-flex h-10 w-full items-center justify-center gap-2 rounded-md bg-[#2f6bff] px-4 text-sm font-semibold text-white sm:w-auto"
          >
            Ouvrir le Test Lab
            <ArrowRight size={15} />
          </Link>
          <Link
            href="/p2p-scenarios"
            className="inline-flex h-10 w-full items-center justify-center gap-2 rounded-md border border-[#2f6bff] bg-white px-4 text-sm font-semibold text-[#2f6bff] sm:w-auto"
          >
            Scénarios guidés
            <ArrowRight size={15} />
          </Link>
        </div>
      </div>

      <section className="mt-6 grid gap-4 md:grid-cols-3">
        <QuickCard
          title="Tester en 3 minutes"
          icon={TerminalSquare}
          body="Choisir un scénario, cliquer Scorer via API, ouvrir Fraud Case 360, exporter l'evidence pack."
          href="/risk-test-lab"
        />
        <QuickCard
          title="Lire le modèle"
          icon={BookOpen}
          body="Comprendre score 0-100, niveaux de risque, décisions, typologies et reason codes."
          href="#model"
        />
        <QuickCard
          title="Voir les limites"
          icon={ShieldCheck}
          body="Données synthétiques, décision humaine, pas de détection bancaire réelle."
          href="#limits"
        />
      </section>

      <section className="mt-6 grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
        <Card id="model">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <GitBranch size={18} className="text-[#2f6bff]" />
              Modèle de scoring
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm leading-7 text-[#667085]">
            <p>
              Le moteur `risk-engine-demo-v1` agrège huit détecteurs déterministes.
              Chaque détecteur produit un score partiel, des signaux et des reason
              codes. Le score final est borné entre 0 et 100.
            </p>
            <div className="grid gap-3 sm:grid-cols-4">
              <Scale label="LOW" value="0-24" />
              <Scale label="MEDIUM" value="25-49" />
              <Scale label="HIGH" value="50-74" />
              <Scale label="CRITICAL" value="75-100" />
            </div>
            <div className="rounded-md bg-[#08111f] p-4 text-white">
              <div className="text-xs uppercase tracking-wider text-white/45">
                Décisions
              </div>
              <div className="mt-2 grid gap-2 text-sm sm:grid-cols-2">
                <span>ALLOW</span>
                <span>MONITOR</span>
                <span>MANUAL_REVIEW</span>
                <span>BLOCK_RECOMMENDED</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Braces size={18} className="text-[#2f6bff]" />
              API de test
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3">
              <Endpoint method="POST" path="/api/risk/score" body="Score une transaction synthétique." />
              <Endpoint method="GET" path="/api/risk/scenarios" body="Retourne les scénarios locaux ou Hugging Face." />
              <Endpoint method="POST" path="/api/risk/cases" body="Crée un case simulé et retourne son lien." />
              <Endpoint method="POST" path="/api/evidence/export" body="Génère JSON + HTML imprimable." />
            </div>
            <pre className="mt-4 overflow-auto rounded-md bg-[#08111f] p-4 text-xs leading-6 text-white">
{`{
  "score": 91,
  "level": "CRITICAL",
  "decision": "BLOCK_RECOMMENDED",
  "typology": "APP_FRAUD_BANK_IMPERSONATION",
  "modelVersion": "risk-engine-demo-v1"
}`}
            </pre>
          </CardContent>
        </Card>
      </section>

      <section className="mt-6 grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Library size={18} className="text-[#2f6bff]" />
              Glossaire
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {glossary.map(([term, definition]) => (
              <div key={term} className="rounded-md border border-[#e6ebf2] bg-[#f7f9fc] p-3 dark:border-white/10 dark:bg-white/[0.03]">
                <div className="font-semibold text-[#111827] dark:text-white">{term}</div>
                <p className="mt-1 text-sm leading-6 text-[#667085]">{definition}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileCheck2 size={18} className="text-[#2f6bff]" />
              Familles de reason codes
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {reasonFamilies.map(([family, codes]) => (
              <div key={family} className="rounded-md border border-[#e6ebf2] bg-white p-3 dark:border-white/10 dark:bg-white/[0.04]">
                <div className="flex items-center justify-between gap-3">
                  <div className="font-semibold text-[#111827] dark:text-white">{family}</div>
                  <Badge severity="neutral">demo</Badge>
                </div>
                <p className="mt-2 font-mono text-xs leading-6 text-[#667085]">{codes}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>

      <section className="mt-6 grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TerminalSquare size={18} className="text-[#2f6bff]" />
              Tests & validation
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm leading-7 text-[#667085]">
            <p>
              Parcours conseillé : choisir un scénario, lancer l'analyse, ouvrir
              Fraud Case 360, ajouter une note analyste puis exporter l'evidence pack.
            </p>
            <div className="grid gap-2">
              {[
                "GET /api/risk/scenarios doit retourner 6 scénarios synthétiques.",
                "POST /api/risk/score doit retourner score, décision, typologie, reason codes et détecteurs.",
                "POST /api/evidence/export doit retourner evidencePack et printableHtml.",
                "Les routes visibles ne doivent pas mener à une 404.",
              ].map((item) => (
                <div key={item} className="rounded-md bg-[#f7f9fc] p-3 dark:bg-white/[0.03]">
                  {item}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck size={18} className="text-[#027a48]" />
              Configuration Hugging Face / Vercel
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm leading-7 text-[#667085]">
            <p>
              La source Hugging Face reste optionnelle. Sans variable serveur valide,
              l'application affiche un fallback local explicite et ne bloque pas la démo.
            </p>
            <pre className="overflow-auto rounded-md bg-[#08111f] p-4 text-xs leading-6 text-white">
{`HF_SYNTHETIC_SCENARIOS_URL=https://...
HF_TOKEN=hf_... # uniquement si dataset privé`}
            </pre>
            <p>
              Le token ne doit jamais être exposé au navigateur. Les datasets doivent
              rester synthétiques.
            </p>
          </CardContent>
        </Card>
      </section>

      <Card id="limits" className="mt-6 border-l-4 border-l-[#b42318]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Info size={18} className="text-[#b42318]" />
            Limites et gouvernance
          </CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 text-sm leading-7 text-[#667085] md:grid-cols-2">
          <p>
            Données synthétiques uniquement. Aucune donnée personnelle réelle ne
            doit être saisie dans la démo publique.
          </p>
          <p>
            Pas de décision bancaire réelle, pas de certification conformité, pas
            de fingerprinting réel, pas de dark web scraping. La décision finale
            reste humaine.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

function QuickCard({
  title,
  body,
  href,
  icon: Icon,
}: {
  title: string;
  body: string;
  href: string;
  icon: typeof BookOpen;
}) {
  return (
    <Link
      href={href}
      className="rounded-md border border-[#e6ebf2] bg-white p-5 shadow-sm transition-colors hover:border-[#2f6bff] dark:border-white/10 dark:bg-white/[0.04]"
    >
      <Icon size={20} className="text-[#2f6bff]" />
      <div className="mt-3 font-semibold text-[#111827] dark:text-white">{title}</div>
      <p className="mt-2 text-sm leading-6 text-[#667085]">{body}</p>
    </Link>
  );
}

function Scale({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-[#e6ebf2] bg-white p-3 dark:border-white/10 dark:bg-white/[0.04]">
      <div className="text-xs font-semibold text-[#667085]">{label}</div>
      <div className="mt-1 font-mono text-sm font-bold text-[#111827] dark:text-white">
        {value}
      </div>
    </div>
  );
}

function Endpoint({ method, path, body }: { method: string; path: string; body: string }) {
  return (
    <div className="rounded-md border border-[#e6ebf2] bg-[#f7f9fc] p-3 dark:border-white/10 dark:bg-white/[0.03]">
      <div className="flex flex-wrap items-center gap-2">
        <Badge severity={method === "GET" ? "low" : "medium"}>{method}</Badge>
        <code className="text-xs font-semibold text-[#2f6bff]">{path}</code>
      </div>
      <p className="mt-2 text-sm leading-6 text-[#667085]">{body}</p>
    </div>
  );
}
