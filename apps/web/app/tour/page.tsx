"use client";

import Link from "next/link";
import { useState } from "react";
import { ForensicPage } from "@/components/forensic-page";

const TOTAL_STEPS = 5;

type Step = {
  title: string;
  body: string;
  glyph: string;
  cta: { label: string; href: string }[];
  proof?: string;
};

const STEPS: Step[] = [
  {
    title: "Une plateforme d'audit P2P orientée décision",
    glyph: "▣",
    body: "P2P Fraud Detective FR centralise les signaux de fraude fournisseurs : BEC, fractionnement sous seuil, doublons, sanctions, PEP, anneaux IBAN et anomalies ML. L'objectif n'est pas d'empiler des alertes, mais de prioriser les pertes potentielles et de documenter chaque décision.",
    cta: [{ label: "Voir la méthodologie", href: "/methodology" }],
    proof: "Données synthétiques ou sources publiques, sans dépendance à un fichier client pour la démo.",
  },
  {
    title: "Cockpit : l'exposition financière avant le bruit",
    glyph: "Σ",
    body: "Le cockpit met en avant l'exposition totale, l'exposition critique, les cases ouverts et les retards SLA. Le Top fournisseurs trie par impact financier pour parler aux DAF, auditeurs et équipes conformité.",
    cta: [{ label: "Ouvrir le cockpit", href: "/dashboard" }],
    proof: "Les métriques sont conçues pour déclencher une action, pas seulement informer.",
  },
  {
    title: "Fournisseur 360 : comprendre le risque",
    glyph: "◫",
    body: "Chaque fournisseur doit rassembler identité, SIREN, paiements, findings, timeline et justification de score. C'est le point de bascule entre détection automatique et investigation humaine.",
    cta: [{ label: "Voir les fournisseurs", href: "/vendors" }],
  },
  {
    title: "Graphes : repérer les liens invisibles",
    glyph: "◇",
    body: "Les anneaux de fraude révèlent les relations entre fournisseurs, IBAN, bénéficiaires et patterns récurrents. Le graphe rend les clusters suspects lisibles pour les équipes non techniques.",
    cta: [
      { label: "Explorer les anneaux", href: "/rings" },
      { label: "Voir le score", href: "/score" },
    ],
  },
  {
    title: "Preuve d'audit : signer et exporter",
    glyph: "✓",
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
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Démo guidée · {TOTAL_STEPS} étapes</div>
          <h1 style={{ marginTop: 9 }}>
            Tour <span className="italic">guidé</span>
          </h1>
          <p className="sub">
            Comprendre la plateforme en 5 étapes et passer naturellement vers un scénario
            de fraude synthétique.
          </p>
        </div>
        <div className="fx-head-actions">
          <button type="button" className="fx-btn-ghost sm" onClick={() => setDone(true)}>
            Passer
          </button>
        </div>
      </div>

      <Progress current={step} total={TOTAL_STEPS} />

      <div className="fx-panel mt-5">
        <div className="fx-panel-head">
          <div>
            <div className="fx-eyebrow">Étape {step} sur {TOTAL_STEPS}</div>
            <h2 style={{ marginTop: 4 }}>{current.title}</h2>
          </div>
          <span className="glyph">{current.glyph}</span>
        </div>
        <div className="fx-panel-body">
          <p style={{ fontSize: 14, lineHeight: 1.7, color: "var(--fg-2)" }}>
            {current.body}
          </p>
          {current.proof ? (
            <div
              style={{
                marginTop: 16,
                background: "var(--bg-2)",
                border: "1px solid var(--border)",
                borderLeft: "2px solid var(--verified)",
                padding: "12px 14px",
              }}
            >
              <span className="fx-mono" style={{ fontSize: 12, color: "var(--verified)", lineHeight: 1.6 }}>
                ✓ {current.proof}
              </span>
            </div>
          ) : null}
          {current.cta.length > 0 ? (
            <div className="mt-5 flex flex-wrap gap-2">
              {current.cta.map((c) => (
                <Link key={c.href} href={c.href} className="fx-btn-ghost sm">
                  {c.label} →
                </Link>
              ))}
            </div>
          ) : null}
        </div>
      </div>

      <div className="mt-5 flex items-center justify-between">
        <button
          type="button"
          className="fx-btn-ghost sm"
          onClick={goPrev}
          disabled={step === 1}
        >
          ← Précédent
        </button>
        <span className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>
          {Math.round((step / TOTAL_STEPS) * 100)} % complété
        </span>
        <button type="button" className="fx-btn sm" onClick={goNext}>
          {step === TOTAL_STEPS ? "Terminer" : "Suivant →"}
        </button>
      </div>
    </ForensicPage>
  );
}

function Progress({ current, total }: { current: number; total: number }) {
  return (
    <div className="mt-4">
      <div className="fx-bar" style={{ height: 4 }}>
        <i style={{ width: `${(current / total) * 100}%`, transition: "width .3s" }} />
      </div>
    </div>
  );
}

function TourDone({ onRestart }: { onRestart: () => void }) {
  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Démo guidée · terminée</div>
          <h1 style={{ marginTop: 9 }}>
            Tour <span className="italic">terminé</span>
          </h1>
          <p className="sub">
            Le prochain pas naturel est de lancer un scénario préchargé pour voir le cockpit,
            la fiche fournisseur et les preuves d&apos;audit en contexte.
          </p>
        </div>
      </div>
      <div className="fx-card-accent">
        <div className="fx-eyebrow" style={{ marginBottom: 12 }}>Prochaines étapes</div>
        <div className="flex flex-wrap gap-3">
          <Link href="/sandbox" className="fx-btn">
            Analyser un scénario ↗
          </Link>
          <button type="button" className="fx-btn-ghost" onClick={onRestart}>
            ↻ Recommencer
          </button>
        </div>
      </div>
    </ForensicPage>
  );
}
