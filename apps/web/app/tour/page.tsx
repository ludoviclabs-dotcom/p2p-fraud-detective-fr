"use client";

import Link from "next/link";
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  ArrowLeft,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  FileCheck2,
  GitBranch,
  RefreshCw,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";

const TOTAL_STEPS = 5;

type Step = {
  title: string;
  body: string;
  Icon: LucideIcon;
  cta: { label: string; href: string }[];
  proof?: string;
};

const STEPS: Step[] = [
  {
    title: "Une plateforme d'audit P2P orientée décision",
    Icon: ShieldCheck,
    body: "P2P Fraud Detective FR centralise les signaux de fraude fournisseurs : BEC, fractionnement sous seuil, doublons, sanctions, PEP, anneaux IBAN et anomalies ML. L'objectif n'est pas d'empiler des alertes, mais de prioriser les pertes potentielles et de documenter chaque décision.",
    cta: [{ label: "Voir la méthodologie", href: "/methodology" }],
    proof: "Données synthétiques ou sources publiques, sans dépendance à un fichier client pour la démo.",
  },
  {
    title: "Cockpit : l'exposition financière avant le bruit",
    Icon: BarChart3,
    body: "Le cockpit met en avant l'exposition totale, l'exposition critique, les cases ouverts et les retards SLA. Le Top fournisseurs trie par impact financier pour parler aux DAF, auditeurs et équipes conformité.",
    cta: [{ label: "Ouvrir le cockpit", href: "/dashboard" }],
    proof: "Les métriques sont conçues pour déclencher une action, pas seulement informer.",
  },
  {
    title: "Fournisseur 360 : comprendre le risque",
    Icon: FileCheck2,
    body: "Chaque fournisseur doit rassembler identité, SIREN, paiements, findings, timeline et justification de score. C'est le point de bascule entre détection automatique et investigation humaine.",
    cta: [{ label: "Voir les fournisseurs", href: "/vendors" }],
  },
  {
    title: "Graphes : repérer les liens invisibles",
    Icon: GitBranch,
    body: "Les anneaux de fraude révèlent les relations entre fournisseurs, IBAN, bénéficiaires et patterns récurrents. Le graphe rend les clusters suspects lisibles pour les équipes non techniques.",
    cta: [
      { label: "Explorer les anneaux", href: "/rings" },
      { label: "Voir le score", href: "/score" },
    ],
  },
  {
    title: "Preuve d'audit : signer et exporter",
    Icon: CheckCircle2,
    body: "Chaque mutation peut rejoindre une piste d'audit vérifiable, avec hash et signature. Les exports doivent être exploitables pour un dossier de contrôle, une revue CAC ou une investigation interne.",
    cta: [
      { label: "Vérifier l'audit trail", href: "/audit" },
      { label: "Préparer l'export", href: "/exports" },
    ],
    proof: "La transparence technique devient un élément de réassurance business.",
  },
];

export default function TourPage() {
  const [step, setStep] = useState(1);
  const [done, setDone] = useState(false);

  const current = STEPS[step - 1];
  const CurrentIcon = current.Icon;

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
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-[#08111f] dark:text-white">
            Démo guidée
          </h1>
          <p className="mt-2 text-sm leading-6 text-[#667085]">
            Comprendre la plateforme en 5 étapes et passer naturellement vers
            un scénario de fraude synthétique.
          </p>
        </div>
        <Button variant="ghost" size="sm" onClick={() => setDone(true)}>
          Passer
        </Button>
      </div>

      <Progress current={step} total={TOTAL_STEPS} />

      <Card className="mt-5 overflow-hidden">
        <CardHeader className="bg-[#08111f] text-white">
          <div className="flex items-start gap-4">
            <div className="grid h-12 w-12 place-items-center rounded-md bg-white/10 text-white">
              <CurrentIcon size={24} />
            </div>
            <div>
              <div className="text-xs font-semibold uppercase tracking-wider text-white/42">
                Étape {step} sur {TOTAL_STEPS}
              </div>
              <CardTitle className="mt-1 text-xl text-white">
                {current.title}
              </CardTitle>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm leading-7 text-[#111827] dark:text-white/82">
            {current.body}
          </p>
          {current.proof ? (
            <div className="mt-5 rounded-md border border-[#e8f8f1] bg-[#f3fbf7] p-4 text-sm leading-6 text-[#176b4c]">
              {current.proof}
            </div>
          ) : null}
          {current.cta.length > 0 ? (
            <div className="mt-5 flex flex-wrap gap-2">
              {current.cta.map((c) => (
                <Link
                  key={c.href}
                  href={c.href}
                  className="inline-flex h-9 items-center gap-2 rounded-md border border-[#2f6bff] bg-white px-3 text-sm font-semibold text-[#2f6bff] transition-colors hover:bg-[#eaf1ff] dark:bg-white/[0.04]"
                >
                  {c.label}
                  <ArrowRight size={14} />
                </Link>
              ))}
            </div>
          ) : null}
        </CardContent>
      </Card>

      <div className="mt-5 flex items-center justify-between">
        <Button
          variant="outline"
          onClick={goPrev}
          disabled={step === 1}
          type="button"
        >
          <ArrowLeft size={14} /> Précédent
        </Button>
        <span className="text-xs font-medium text-[#667085]">
          {Math.round((step / TOTAL_STEPS) * 100)} % complété
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
    <div className="mt-6">
      <div className="h-2 w-full overflow-hidden rounded-full bg-[#e6ebf2]">
        <div
          className="h-full bg-[#2f6bff] transition-all duration-300"
          style={{ width: `${(current / total) * 100}%` }}
        />
      </div>
    </div>
  );
}

function TourDone({ onRestart }: { onRestart: () => void }) {
  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="rounded-md bg-[#08111f] p-8 text-white shadow-2xl shadow-[#08111f]/15">
        <h1 className="text-3xl font-bold">Démo guidée terminée</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-white/65">
          Le prochain pas naturel est de lancer un scénario préchargé pour
          voir le cockpit, la fiche fournisseur et les preuves d'audit en
          contexte.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href="/sandbox"
            className="inline-flex h-10 items-center gap-2 rounded-md bg-white px-4 text-sm font-semibold text-[#08111f] transition-colors hover:bg-[#eaf1ff]"
          >
            Analyser un scénario
            <ArrowRight size={14} />
          </Link>
          <Button onClick={onRestart} variant="outline">
            <RefreshCw size={14} /> Recommencer
          </Button>
        </div>
      </div>
    </div>
  );
}
