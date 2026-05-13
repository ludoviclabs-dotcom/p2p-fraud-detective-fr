"use client";

import Link from "next/link";
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  ArrowLeft,
  ArrowRight,
  Github,
  GraduationCap,
  RefreshCw,
} from "lucide-react";

const TOTAL_STEPS = 5;

type Step = {
  emoji: string;
  title: string;
  body: string;
  cta: { label: string; href: string }[];
  hint?: string;
};

const STEPS: Step[] = [
  {
    emoji: "🎯",
    title: "Qu'est-ce que P2P Fraud Detective FR ?",
    body: "Démonstrateur d'audit du cycle Procure-to-Pay orienté détection de fraude (BEC, sous-seuils, doublons, sanctions, anneaux IBAN). Aligné sur les méthodologies AML/CFT et les contrôles attendus en audit P2P public : ISA 240, AS 2401, Sapin 2 art. 17, LCB-FT, DORA art. 28, AMLD6.\n\nPertinent pour ETI 500 M€ – 2 Md€, cabinets d'audit mid-tier, fonctions publiques et organismes de contrôle (DGFiP, Tracfin, IGF, Cour des comptes, CRC régionales).\n\nDonnées 100 % synthétiques (Faker fr_FR) ou issues de sources publiques (Sirene, DECP, OpenSanctions). Conformité RGPD garantie.",
    cta: [
      { label: "Voir la méthodologie complète", href: "/methodology" },
    ],
  },
  {
    emoji: "🎯",
    title: "Le Cockpit — pilotage par exposition financière",
    body: "Le Cockpit affiche 4 KPI principaux (exposition totale €, CRITICAL, cases ouverts, retards SLA) avec sparklines de tendance 30 jours.\n\nLe Top 10 fournisseurs trie par risque financier, pas par score brut — c'est la métrique qui parle à un DAF/CFO. Cliquer sur un vendor → drill-down direct vers la Fiche fournisseur 360°.\n\nL'audit log Ed25519 (P5-5) journalise toute action : créations, assignations, clôtures motivées. Toute mutation est cryptographiquement signée et vérifiable depuis /audit.",
    cta: [
      { label: "Ouvrir le Cockpit", href: "/dashboard" },
      { label: "Voir l'audit trail", href: "/audit" },
    ],
    hint: "Le Cockpit est la page d'accueil par défaut.",
  },
  {
    emoji: "🪪",
    title: "Fiche fournisseur 360° + LLM streaming",
    body: "Pour chaque vendor : 4 KPI (Nom, SIREN, Paiements, Cases) + sparkline trend exposition 30 jours (Recharts AreaChart) + tabs Profil/Timeline/Findings.\n\nBouton « Générer narration audit (Claude) » → streaming SSE via Vercel AI SDK + endpoint /api/v1/llm/narrative côté FastAPI. La narration suit la doctrine ISA 240 + AMLD6 et peut être copy-pasted dans le dossier audit final.\n\nFiltres timeline ≥ 30j, vendor sanctioned/PEP banner si applicable.",
    cta: [
      { label: "Voir la liste des fournisseurs", href: "/vendors" },
    ],
  },
  {
    emoji: "🕸️",
    title: "Anneaux de fraude — WebGL sigma.js",
    body: "Graphe vendor ↔ IBAN partagé rendu en WebGL via sigma.js + graphology. Layout ForceAtlas2 100 itérations.\n\nDétection backend NetworkX : un IBAN partagé entre ≥ 3 vendors → anneau suspect. Le scénario \"anneau_fraude\" génère 5 vendors partageant 3 IBAN par paires → graphe cyclique évident.\n\nSélecteur de scénarios (5 disponibles), stats live (nodes, edges, anneaux, plus grand cluster), zoom/pan WebGL natif.",
    cta: [
      { label: "Ouvrir Anneaux de fraude", href: "/rings" },
      { label: "Score waterfall", href: "/score" },
    ],
  },
  {
    emoji: "📜",
    title: "Audit trail cryptographique Ed25519",
    body: "Toutes les mutations sont journalisées dans un audit log chaîné par hash SHA-256, signé Ed25519 (RFC 8032) quand P2PFD_ED25519_PRIVATE_KEY est défini.\n\nLa clé publique est exposée par GET /security/public-key — n'importe quel tiers (CAC, ACPR, Cour des comptes, magistrat) peut vérifier indépendamment chaque entrée sans accès au backend.\n\nEn sortie : dossier d'enquête PDF (weasyprint) ou synthèse Excel/Parquet pour archivage légal Sapin 2 (10 ans).",
    cta: [
      { label: "Vérifier l'audit trail", href: "/audit" },
      { label: "Exports PDF & CSV", href: "/exports" },
    ],
    hint: "Sur la page /audit, le bouton « Recalculer la chaîne » lance la vérification cryptographique complète.",
  },
];

export default function TourPage() {
  const [step, setStep] = useState(1);
  const [done, setDone] = useState(false);

  const current = STEPS[step - 1];

  const goNext = () => {
    if (step >= TOTAL_STEPS) {
      setDone(true);
    } else {
      setStep((s) => s + 1);
    }
  };
  const goPrev = () => setStep((s) => Math.max(1, s - 1));
  const restart = () => {
    setStep(1);
    setDone(false);
  };

  if (done) {
    return <TourDone onRestart={restart} />;
  }

  return (
    <div className="px-8 py-10">
      <div className="mb-1 flex items-center justify-between">
        <div className="text-xs uppercase tracking-wider text-[#5a6478]">
          Pilotage
        </div>
        <Button variant="ghost" size="sm" onClick={() => setDone(true)}>
          Passer le tour →
        </Button>
      </div>
      <h1 className="mb-1 flex items-center gap-2 text-3xl font-bold text-[#0f1b33] dark:text-white">
        <GraduationCap size={28} /> Tour guidé
      </h1>
      <p className="mb-6 text-sm text-[#5a6478]">
        Découverte de la plateforme en 5 étapes — moins de 3 minutes.
      </p>

      <Progress current={step} total={TOTAL_STEPS} />

      <Card className="mt-4">
        <CardHeader>
          <CardTitle className="text-xl">
            <span className="mr-2">{current.emoji}</span>
            {current.title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="prose prose-sm max-w-none whitespace-pre-wrap text-[#1a1f2c]">
            {current.body}
          </div>
          {current.hint ? (
            <div className="mt-4 rounded border-l-4 border-[#e5a93a] bg-[#fff8ec] p-3 text-xs text-[#5a6478]">
              💡 {current.hint}
            </div>
          ) : null}
          {current.cta.length > 0 ? (
            <div className="mt-4 flex flex-wrap gap-2">
              {current.cta.map((c) => (
                <Link
                  key={c.href}
                  href={c.href}
                  className="inline-flex items-center gap-1 rounded border border-[#1f3a6e] bg-white px-3 py-1.5 text-xs font-medium text-[#1f3a6e] transition-colors hover:bg-[#f4f6fa]"
                >
                  ➡️ {c.label}
                </Link>
              ))}
            </div>
          ) : null}
        </CardContent>
      </Card>

      <div className="mt-4 flex items-center justify-between">
        <Button
          variant="outline"
          onClick={goPrev}
          disabled={step === 1}
          type="button"
        >
          <ArrowLeft size={14} /> Précédent
        </Button>
        <span className="text-xs text-[#5a6478]">
          Étape {step} / {TOTAL_STEPS}
        </span>
        <Button onClick={goNext} type="button">
          {step === TOTAL_STEPS ? "Terminer" : "Suivant"} <ArrowRight size={14} />
        </Button>
      </div>
    </div>
  );
}

function Progress({ current, total }: { current: number; total: number }) {
  return (
    <div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-[#e1e5ee]">
        <div
          className="h-full bg-[#1f3a6e] transition-all duration-300"
          style={{ width: `${(current / total) * 100}%` }}
        />
      </div>
    </div>
  );
}

function TourDone({ onRestart }: { onRestart: () => void }) {
  return (
    <div className="px-8 py-10">
      <div className="mb-1 text-xs uppercase tracking-wider text-[#5a6478]">
        Pilotage
      </div>
      <h1 className="mb-1 text-3xl font-bold text-[#0f1b33] dark:text-white">
        🎉 Tour terminé !
      </h1>
      <p className="mb-6 text-sm text-[#5a6478]">
        Vous connaissez maintenant les 5 piliers de la plateforme.
      </p>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>🚀 Pour aller plus loin</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2">
          {[
            {
              href: "/upload",
              title: "Importer vos données",
              body: "Glisser-déposer un CSV/XLSX → détection auto en arrière-plan.",
            },
            {
              href: "/dashboard",
              title: "Ouvrir le Cockpit",
              body: "4 KPI exposition € + sparklines 30j + Top 10 vendors.",
            },
            {
              href: "/methodology",
              title: "Méthodologie complète",
              body: "Sources publiques + seuils + métriques F1 + limites connues.",
            },
            {
              href: "/governance",
              title: "Gouvernance",
              body: "AI Act + RGPD + RBAC + AMLD6 + Sapin 2 + Ed25519.",
            },
          ].map((c) => (
            <Link
              key={c.href}
              href={c.href}
              className="block rounded-md border border-[#e1e5ee] bg-white p-4 transition-shadow hover:shadow-md"
            >
              <div className="font-semibold text-[#0f1b33]">{c.title}</div>
              <div className="mt-1 text-sm text-[#5a6478]">{c.body}</div>
            </Link>
          ))}
        </CardContent>
      </Card>

      <div className="flex flex-wrap gap-3">
        <Button onClick={onRestart} variant="outline">
          <RefreshCw size={14} /> Recommencer le tour
        </Button>
        <a
          href="https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr"
          target="_blank"
          rel="noreferrer"
          className="inline-flex h-10 items-center gap-2 rounded-md border border-[#e1e5ee] bg-white px-4 text-sm font-medium text-[#5a6478] transition-colors hover:border-[#1f3a6e] hover:text-[#1f3a6e]"
        >
          <Github size={14} /> Code source
        </a>
      </div>
    </div>
  );
}
