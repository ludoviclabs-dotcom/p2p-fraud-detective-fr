import Link from "next/link";
import {
  ArrowRight,
  BadgeCheck,
  Bell,
  CheckCircle2,
  Database,
  FileCheck2,
  Github,
  GitBranch,
  LockKeyhole,
  Network,
  Play,
  ShieldCheck,
  Sparkles,
  TimerReset,
  TrendingUp,
} from "lucide-react";

const TRUST_POINTS = [
  { label: "Donnees synthetiques", detail: "demo sans fichier client" },
  { label: "Connecteurs prepares", detail: "Sirene, DECP, OpenSanctions" },
  { label: "Audit verifiable", detail: "hash chain; Ed25519 en pilote" },
  { label: "Donnees minimales", detail: "provenance et tracabilite" },
];

const MINI_CASES = [
  {
    title: "Doublon critique détecté",
    detail: "Deux factures rapprochées, même IBAN, montants quasi identiques.",
    risk: "92",
  },
  {
    title: "Fournisseur sous sanction",
    detail: "Correspondance fuzzy avec snapshot demo et justification exportable.",
    risk: "88",
  },
  {
    title: "Fractionnement sous seuil",
    detail: "Paiements séquencés sous délégation, pic sur 14 jours.",
    risk: "81",
  },
];

const MODULES = [
  {
    title: "Priorisation finance",
    body: "Classez les alertes par exposition financière, retard SLA et criticité audit.",
    Icon: TrendingUp,
  },
  {
    title: "Investigation explicable",
    body: "Ouvrez un dossier fournisseur 360 avec sources, timeline et facteurs de score.",
    Icon: FileCheck2,
  },
  {
    title: "Graphe relationnel",
    body: "Repérez les anneaux IBAN et les clusters fournisseurs à risque.",
    Icon: Network,
  },
  {
    title: "Conformité documentée",
    body: "Preparez une piste d'audit verifiable; signatures activees en pilote.",
    Icon: ShieldCheck,
  },
];

export default function Home() {
  return (
    <div className="app-surface">
      <section className="mx-auto grid max-w-7xl gap-10 px-4 py-10 sm:px-6 lg:grid-cols-[0.92fr_1.08fr] lg:px-8 lg:py-16">
        <div className="flex flex-col justify-center">
          <h1 className="max-w-3xl text-4xl font-bold leading-tight tracking-normal text-[#08111f] dark:text-white sm:text-5xl lg:text-[3.25rem]">
            Détectez les fraudes P2P avant qu'elles ne deviennent des pertes
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-[#667085] sm:text-lg">
            Analysez factures, fournisseurs, sanctions et signaux faibles dans
            un cockpit d'audit explicable, prêt pour les équipes finance, audit
            et conformité.
          </p>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link
              href="/sandbox"
              className="focus-ring inline-flex h-12 items-center justify-center gap-2 rounded-md bg-[#2f6bff] px-6 text-sm font-semibold text-white shadow-lg shadow-[#2f6bff]/20 transition-colors hover:bg-[#2457d6]"
            >
              <Play size={17} />
              Analyser un scénario maintenant
            </Link>
            <Link
              href="/vendors"
              className="focus-ring inline-flex h-12 items-center justify-center gap-2 rounded-md border border-[#d7deea] bg-white px-6 text-sm font-semibold text-[#111827] transition-colors hover:border-[#2f6bff] hover:text-[#2f6bff] dark:border-white/10 dark:bg-white/[0.04] dark:text-white"
            >
              Voir un cas fournisseur à risque
              <ArrowRight size={17} />
            </Link>
          </div>

          <div className="mt-5 flex flex-wrap gap-3 text-sm text-[#667085]">
            <span className="inline-flex items-center gap-2">
              <CheckCircle2 size={16} className="text-[#12a876]" />
              Aucun fichier requis
            </span>
            <span className="inline-flex items-center gap-2">
              <TimerReset size={16} className="text-[#2f6bff]" />
              Démo guidée en 60 secondes
            </span>
          </div>
        </div>

        <FraudOperationsPreview />
      </section>

      <section className="border-y border-[#e6ebf2] bg-white/80 px-4 py-4 backdrop-blur dark:border-white/10 dark:bg-white/[0.03] sm:px-6 lg:px-8">
        <div className="mx-auto grid max-w-7xl gap-3 md:grid-cols-4">
          {TRUST_POINTS.map((item) => (
            <div key={item.label} className="flex items-start gap-3">
              <BadgeCheck className="mt-0.5 text-[#12a876]" size={18} />
              <div>
                <div className="text-sm font-semibold text-[#111827] dark:text-white">
                  {item.label}
                </div>
                <div className="text-xs text-[#667085]">{item.detail}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-6 px-4 py-12 sm:px-6 lg:grid-cols-[0.78fr_1.22fr] lg:px-8">
        <div>
          <h2 className="text-2xl font-bold text-[#08111f] dark:text-white">
            Un outil pensé pour les décisions d'audit, pas pour accumuler des
            alertes
          </h2>
          <p className="mt-3 text-sm leading-6 text-[#667085]">
            La première valeur doit être comprise immédiatement : où se trouve
            le risque financier, pourquoi il est remonté, et quelle action
            l'équipe doit lancer.
          </p>
          <Link
            href="/tour"
            className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-[#2f6bff]"
          >
            Voir la démo guidée <ArrowRight size={16} />
          </Link>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {MINI_CASES.map((item) => (
            <article
              key={item.title}
              className="premium-panel rounded-md p-5 transition-transform hover:-translate-y-0.5"
            >
              <div className="flex items-start justify-between gap-3">
                <Bell size={18} className="text-[#e5484d]" />
                <span className="rounded bg-[#fff0f1] px-2 py-1 text-xs font-bold text-[#e5484d]">
                  {item.risk}
                </span>
              </div>
              <h3 className="mt-4 font-semibold text-[#111827] dark:text-white">
                {item.title}
              </h3>
              <p className="mt-2 text-sm leading-6 text-[#667085]">
                {item.detail}
              </p>
            </article>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-12 sm:px-6 lg:px-8">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {MODULES.map((item) => (
            <article key={item.title} className="premium-panel rounded-md p-5">
              <div className="grid h-10 w-10 place-items-center rounded-md bg-[#eaf1ff] text-[#2f6bff]">
                <item.Icon size={20} />
              </div>
              <h3 className="mt-4 font-semibold text-[#111827] dark:text-white">
                {item.title}
              </h3>
              <p className="mt-2 text-sm leading-6 text-[#667085]">
                {item.body}
              </p>
            </article>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-14 sm:px-6 lg:px-8">
        <div className="overflow-hidden rounded-md bg-[#08111f] p-6 text-white shadow-2xl shadow-[#08111f]/15 lg:flex lg:items-center lg:justify-between lg:p-8">
          <div>
            <h2 className="text-2xl font-bold">
              Prêt à tester un cas de fraude synthétique ?
            </h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-white/65">
              Lancez la sandbox, choisissez une typologie et suivez le chemin
              jusqu'au cockpit, au fournisseur 360 et à la piste d'audit.
            </p>
          </div>
          <Link
            href="/sandbox"
            className="mt-5 inline-flex h-11 items-center justify-center gap-2 rounded-md bg-white px-5 text-sm font-semibold text-[#08111f] transition-colors hover:bg-[#eaf1ff] lg:mt-0"
          >
            Voir un cas synthetique
            <ArrowRight size={16} />
          </Link>
        </div>
      </section>

      <footer className="border-t border-[#e6ebf2] bg-white px-4 py-8 dark:border-white/10 dark:bg-white/[0.02] sm:px-6 lg:px-8">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 text-sm text-[#667085] md:flex-row md:items-center md:justify-between">
          <div>
            <div className="font-semibold text-[#111827] dark:text-white">
              P2P Fraud Detective FR
            </div>
            <div>Audit P2P, conformité AML/CFT, investigation fournisseur.</div>
          </div>
          <div className="flex flex-wrap gap-4">
            <Link href="/governance" className="hover:text-[#2f6bff]">
              Trust Center
            </Link>
            <Link href="/methodology" className="hover:text-[#2f6bff]">
              Méthodologie
            </Link>
            <a
              href="https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 hover:text-[#2f6bff]"
            >
              <Github size={15} />
              Transparence technique
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}

function FraudOperationsPreview() {
  return (
    <div className="premium-panel relative overflow-hidden rounded-md bg-white p-4 dark:bg-[#0c1729]">
      <div className="absolute right-5 top-5 rounded bg-[#e8f8f1] px-2 py-1 text-xs font-semibold text-[#12a876]">
        Donnees demo
      </div>
      <div className="rounded-md border border-[#e6ebf2] bg-[#08111f] p-4 text-white shadow-xl shadow-[#08111f]/20 dark:border-white/10">
        <div className="flex items-center justify-between gap-4">
          <div>
            <div className="text-xs font-medium uppercase tracking-wider text-white/45">
              Fraud Operations
            </div>
            <div className="mt-1 text-xl font-semibold">
              Command Center P2P
            </div>
          </div>
          <div className="rounded-md bg-[#fff0f1] px-3 py-2 text-right text-[#e5484d]">
            <div className="text-[11px] font-semibold uppercase">Risque</div>
            <div className="text-2xl font-bold leading-none">87</div>
          </div>
        </div>

        <div className="mt-5 grid gap-3 md:grid-cols-3">
          {[
            ["Exposition", "2,4 M€", "#2f6bff"],
            ["Cases ouverts", "34", "#f5a524"],
            ["SLA en retard", "7", "#e5484d"],
          ].map(([label, value, color]) => (
            <div key={label} className="rounded-md bg-white/[0.06] p-3">
              <div className="text-xs text-white/45">{label}</div>
              <div className="mt-2 flex items-end justify-between">
                <span className="text-2xl font-semibold">{value}</span>
                <span
                  className="h-2 w-14 rounded-full"
                  style={{ backgroundColor: color }}
                />
              </div>
            </div>
          ))}
        </div>

        <div className="mt-5 grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-md bg-white p-3 text-[#111827]">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-sm font-semibold">Fournisseurs à traiter</span>
              <span className="text-xs text-[#667085]">Top exposition</span>
            </div>
            {[
              ["VND-0421", "Sanctions + IBAN partagé", "CRITICAL"],
              ["VND-0188", "Fractionnement sous seuil", "HIGH"],
              ["VND-0330", "Doublon facture", "HIGH"],
            ].map(([vendor, reason, severity]) => (
              <div
                key={vendor}
                className="flex items-center gap-3 border-t border-[#e6ebf2] py-3 first:border-t-0"
              >
                <div className="grid h-8 w-8 place-items-center rounded bg-[#eaf1ff] text-[#2f6bff]">
                  <Database size={15} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="font-mono text-xs font-semibold">{vendor}</div>
                  <div className="truncate text-xs text-[#667085]">{reason}</div>
                </div>
                <span className="rounded bg-[#fff0f1] px-2 py-1 text-[10px] font-bold text-[#e5484d]">
                  {severity}
                </span>
              </div>
            ))}
          </div>

          <div className="rounded-md bg-white p-3 text-[#111827]">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
              <GitBranch size={16} className="text-[#2f6bff]" />
              Réseau IBAN
            </div>
            <svg viewBox="0 0 240 160" className="h-40 w-full" aria-hidden>
              <line x1="58" y1="42" x2="120" y2="78" stroke="#d7deea" strokeWidth="2" />
              <line x1="120" y1="78" x2="186" y2="42" stroke="#d7deea" strokeWidth="2" />
              <line x1="120" y1="78" x2="70" y2="124" stroke="#d7deea" strokeWidth="2" />
              <line x1="120" y1="78" x2="176" y2="122" stroke="#d7deea" strokeWidth="2" />
              <circle cx="120" cy="78" r="24" fill="#2f6bff" />
              <circle cx="58" cy="42" r="17" fill="#eaf1ff" stroke="#2f6bff" />
              <circle cx="186" cy="42" r="17" fill="#fff0f1" stroke="#e5484d" />
              <circle cx="70" cy="124" r="17" fill="#eaf1ff" stroke="#2f6bff" />
              <circle cx="176" cy="122" r="17" fill="#e8f8f1" stroke="#12a876" />
              <LockKeyhole x="112" y="70" width="16" height="16" color="#fff" />
            </svg>
          </div>
        </div>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <div className="rounded-md border border-[#e6ebf2] bg-white p-3">
          <Sparkles size={16} className="text-[#2f6bff]" />
          <div className="mt-2 text-sm font-semibold">Score explicable</div>
          <div className="text-xs text-[#667085]">5 facteurs principaux</div>
        </div>
        <div className="rounded-md border border-[#e6ebf2] bg-white p-3">
          <ShieldCheck size={16} className="text-[#12a876]" />
          <div className="mt-2 text-sm font-semibold">Preuve d'audit</div>
          <div className="text-xs text-[#667085]">Chaîne vérifiable</div>
        </div>
        <div className="rounded-md border border-[#e6ebf2] bg-white p-3">
          <TimerReset size={16} className="text-[#f5a524]" />
          <div className="mt-2 text-sm font-semibold">Next action</div>
          <div className="text-xs text-[#667085]">Assigner un reviewer</div>
        </div>
      </div>
    </div>
  );
}
