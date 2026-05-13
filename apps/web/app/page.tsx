import Link from "next/link";
import { ArrowRight, Github } from "lucide-react";

export default function Home() {
  return (
    <div className="px-8 py-12">
      <div className="mx-auto max-w-3xl">
        <div className="mb-2 text-xs uppercase tracking-wider text-[#5a6478]">
          Pilotage
        </div>
        <h1 className="mb-4 text-4xl font-bold text-[#0f1b33] dark:text-white">
          P2P Fraud Detective FR
        </h1>
        <p className="mb-2 text-lg text-[#5a6478]">
          Démonstrateur d'audit du cycle <strong>Procure-to-Pay</strong>{" "}
          orienté détection de fraude (BEC, sous-seuils, doublons, sanctions,
          anneaux), aligné sur les méthodologies AML/CFT et les contrôles
          attendus en audit P2P public.
        </p>
        <p className="mb-8 text-sm italic text-[#5a6478]">
          Pertinent pour ETI, cabinets d'audit, fonctions publiques et
          organismes de contrôle (DGFiP, Tracfin, IGF, Cour des comptes, CRC).
        </p>

        <div className="mb-12 flex flex-wrap gap-3">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 rounded bg-[#1f3a6e] px-5 py-2.5 font-medium text-white transition-colors hover:bg-[#0f1b33]"
          >
            Ouvrir le Cockpit <ArrowRight size={16} />
          </Link>
          <Link
            href="/tour"
            className="inline-flex items-center gap-2 rounded border border-[#1f3a6e] bg-white px-5 py-2.5 font-medium text-[#1f3a6e] transition-colors hover:bg-[#f4f6fa]"
          >
            Tour guidé (3 min)
          </Link>
          <a
            href="https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded border border-[#e1e5ee] bg-white px-5 py-2.5 font-medium text-[#5a6478] transition-colors hover:border-[#1f3a6e] hover:text-[#1f3a6e]"
          >
            <Github size={16} /> GitHub
          </a>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {[
            {
              title: "🟢 Sources live",
              body:
                "DECP, Pappers, OpenSanctions Yente — appels HTTP réels aux référentiels publics.",
            },
            {
              title: "🔐 Audit trail Ed25519",
              body:
                "Signatures cryptographiques sur chaque entrée. Vérifiable indépendamment via /security/public-key.",
            },
            {
              title: "🔗 Webhook B2B",
              body:
                "Événements case.* émis en CloudEvents v1.0 vers SIEM/ERP/SOC avec signature HMAC-SHA256.",
            },
          ].map((card) => (
            <div
              key={card.title}
              className="rounded-md border border-[#e1e5ee] bg-white p-5 transition-shadow hover:shadow-md"
            >
              <div className="mb-2 font-semibold text-[#0f1b33]">
                {card.title}
              </div>
              <div className="text-sm text-[#5a6478]">{card.body}</div>
            </div>
          ))}
        </div>

        <div className="mt-12 rounded-md border border-dashed border-[#c97b1f] bg-[#fff8ec] p-4 text-sm text-[#5a6478]">
          <strong className="text-[#c97b1f]">Phase 0 — Migration v2</strong>{" "}
          en cours. La version Streamlit reste accessible à l'adresse
          d'origine (Streamlit Cloud) jusqu'à 80 % de parité fonctionnelle
          Next.js. Voir <code>docs/migration-v2.md</code>.
        </div>
      </div>
    </div>
  );
}
