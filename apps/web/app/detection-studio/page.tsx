"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { RISK_SCENARIOS } from "@/data/risk-scenarios";
import { scoreTransaction } from "@/lib/risk/scoreEngine";
import type { DetectorId, DetectorScore } from "@/types/risk";
import { Badge, SeverityBadge } from "@/components/ui/badge";
import { ForensicPage } from "@/components/forensic-page";
import { RuleStudioPanel } from "@/components/rule-studio-panel";

const MODULES: {
  id: DetectorId;
  title: string;
  status: "active" | "demo" | "mock";
  dataUsed: string;
  glyph: string;
}[] = [
  {
    id: "beneficiaryTrust",
    title: "Beneficiary / IBAN Trust Check",
    status: "active",
    dataUsed: "Nom bénéficiaire, IBAN, historique, pays, changement RIB.",
    glyph: "▣",
  },
  {
    id: "scamNarrative",
    title: "APP Fraud & Scam Narrative Detector",
    status: "active",
    dataUsed: "Texte narratif, urgence, autorité, secret, investissement.",
    glyph: "§",
  },
  {
    id: "velocity",
    title: "Velocity Checks",
    status: "active",
    dataUsed: "Montant, 24h, seuil, instant payment, fractionnement.",
    glyph: "∿",
  },
  {
    id: "qrRisk",
    title: "QR Code Fraud Analyzer",
    status: "demo",
    dataUsed: "Payload textuel, URL, IBAN extrait, domaine attendu.",
    glyph: "◇",
  },
  {
    id: "deviceSession",
    title: "Device & Session Risk Lite",
    status: "demo",
    dataUsed: "Nouvel appareil, pays IP, remote access, impossible travel.",
    glyph: "□",
  },
  {
    id: "graphRisk",
    title: "Mule Account / Fraud Graph",
    status: "demo",
    dataUsed: "Clusters, IBAN partagé, appareils, payeurs reliés.",
    glyph: "◫",
  },
  {
    id: "documentRibRisk",
    title: "Document / RIB / Invoice Fraud Check",
    status: "demo",
    dataUsed: "Facture, RIB, IBAN attendu, nom fournisseur, format.",
    glyph: "△",
  },
  {
    id: "sanctionsRisk",
    title: "Sanctions / PEP / AML Screening",
    status: "mock",
    dataUsed: "Match sanctions/PEP synthétique, pays sensible.",
    glyph: "▲",
  },
];

export default function DetectionStudioPage() {
  const [scenarioId, setScenarioId] = useState(RISK_SCENARIOS[0]?.id ?? "");
  const [tested, setTested] = useState<DetectorId>("beneficiaryTrust");
  const scenario = RISK_SCENARIOS.find((item) => item.id === scenarioId) ?? RISK_SCENARIOS[0];
  const result = useMemo(() => scoreTransaction(scenario.transaction), [scenario]);
  const selectedDetector = result.detectorScores.find((item) => item.detector === tested);

  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">P2P Fraud Detection Workbench</div>
          <h1 style={{ marginTop: 9 }}>
            Detection <span className="italic">Studio</span>
          </h1>
          <p className="sub">
            Authoring de règles de détection : français → YAML déterministe →
            tests → backtest → activation 4-eyes. Versions journalisées dans la
            piste d&apos;audit signée.
          </p>
        </div>
        <div className="fx-head-actions">
          <Link href="/p2p-scenarios" className="fx-btn">
            Lancer les scénarios ↗
          </Link>
        </div>
      </div>

      <RuleStudioPanel />

      <div className="fx-card-accent" style={{ marginBottom: 16 }}>
        <div className="fx-eyebrow">◇ Section démonstration</div>
        <p className="fx-mono" style={{ marginTop: 6, fontSize: 11, lineHeight: 1.65, color: "var(--muted)" }}>
          Les modules ci-dessous illustrent des détecteurs « paiement
          particulier » avec un scoring 100&nbsp;% client-side, déconnecté du
          moteur Procure-to-Pay réel (ADR-0007). Ils servent de vitrine — le
          moteur de production est celui du studio de règles ci-dessus.
        </p>
      </div>

      <section className="grid gap-4 lg:grid-cols-[0.72fr_1.28fr]">
        <div className="fx-panel">
          <div className="fx-panel-head">
            <h2>Transaction de test</h2>
            <span className="glyph">◷</span>
          </div>
          <div className="fx-panel-body space-y-4">
            <div>
              <label
                htmlFor="detection-studio-scenario"
                className="fx-eyebrow"
                style={{ display: "block", marginBottom: 6 }}
              >
                Scénario
              </label>
              <select
                id="detection-studio-scenario"
                value={scenarioId}
                onChange={(event) => setScenarioId(event.target.value)}
                style={{
                  height: 38,
                  width: "100%",
                  background: "var(--bg)",
                  border: "1px solid var(--border)",
                  padding: "0 12px",
                  fontFamily: "var(--font-mono)",
                  fontSize: 12,
                  color: "var(--fg)",
                  outline: "none",
                }}
              >
                {RISK_SCENARIOS.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.title}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ background: "var(--bg-2)", border: "1px solid var(--border)", padding: "14px 16px" }}>
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="fx-eyebrow">Score global</div>
                  <div
                    style={{ fontFamily: "var(--font-display)", fontSize: 36, lineHeight: 1, color: "var(--fg)", marginTop: 6 }}
                  >
                    {result.score}/100
                  </div>
                </div>
                <SeverityBadge value={result.level} />
              </div>
              <div className="fx-mono" style={{ marginTop: 10, fontSize: 11, color: "var(--muted)" }}>
                {result.typology}
              </div>
              <div className="fx-mono" style={{ marginTop: 4, fontSize: 12, color: "var(--fg)" }}>
                {result.decision}
              </div>
            </div>

            <div className="fx-card-accent">
              <div className="fx-eyebrow" style={{ marginBottom: 6 }}>★ Décision humaine finale</div>
              <p className="fx-mono" style={{ fontSize: 11, lineHeight: 1.65, color: "var(--muted)", marginTop: 6 }}>
                Le moteur est un démonstrateur explicable. Il documente les signaux, mais
                ne prend aucune décision bancaire réelle.
              </p>
            </div>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          {MODULES.map((module) => {
            const score = result.detectorScores.find((item) => item.detector === module.id);
            return (
              <ModuleCard
                key={module.id}
                module={module}
                score={score}
                active={tested === module.id}
                onTest={() => setTested(module.id)}
              />
            );
          })}
        </div>
      </section>

      {selectedDetector ? (
        <div className="fx-panel mt-6">
          <div className="fx-panel-head">
            <div>
              <h2>Résultat du test module</h2>
            </div>
            <Badge severity={selectedDetector.score > 0 ? "high" : "low"}>
              {selectedDetector.status}
            </Badge>
          </div>
          <div className="fx-panel-body grid gap-4 lg:grid-cols-[0.8fr_1.2fr]">
            <div>
              <div className="fx-mono" style={{ fontSize: 13, color: "var(--fg)", fontWeight: 500 }}>
                {selectedDetector.label}
              </div>
              <div
                style={{ fontFamily: "var(--font-display)", fontSize: 42, lineHeight: 1, color: "var(--info)", marginTop: 10 }}
              >
                {selectedDetector.score}/{selectedDetector.maxScore}
              </div>
              <p className="fx-mono" style={{ marginTop: 12, fontSize: 12, lineHeight: 1.6, color: "var(--muted)" }}>
                {selectedDetector.explanation}
              </p>
            </div>
            <div style={{ background: "var(--bg-2)", border: "1px solid var(--border)", padding: "14px 16px" }}>
              <div className="fx-eyebrow" style={{ marginBottom: 12 }}>Signaux et reason codes générés</div>
              {selectedDetector.signals.length || selectedDetector.dataUsed.length ? (
                <div className="mb-4 grid gap-3 sm:grid-cols-2">
                  <div style={{ background: "var(--panel)", border: "1px solid var(--border)", padding: "10px 12px" }}>
                    <div className="fx-eyebrow" style={{ marginBottom: 8 }}>Signaux détectés</div>
                    <div className="flex flex-wrap gap-2">
                      {selectedDetector.signals.length ? (
                        selectedDetector.signals.map((signal) => (
                          <Badge key={signal} severity="medium">
                            {signal}
                          </Badge>
                        ))
                      ) : (
                        <span className="fx-mono" style={{ fontSize: 12, color: "var(--muted)" }}>Aucun signal.</span>
                      )}
                    </div>
                  </div>
                  <div style={{ background: "var(--panel)", border: "1px solid var(--border)", padding: "10px 12px" }}>
                    <div className="fx-eyebrow" style={{ marginBottom: 8 }}>Données utilisées</div>
                    <ul style={{ margin: 0, padding: 0, listStyle: "none" }} className="space-y-1">
                      {selectedDetector.dataUsed.map((item) => (
                        <li key={item} className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>{item}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ) : null}
              {selectedDetector.reasonCodes.length ? (
                <div className="space-y-2">
                  {selectedDetector.reasonCodes.map((reasonCode) => (
                    <div
                      key={reasonCode.code}
                      style={{ background: "var(--panel)", border: "1px solid var(--border)", padding: "10px 12px" }}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <code className="fx-mono" style={{ fontSize: 11, color: "var(--info)" }}>
                          {reasonCode.code}
                        </code>
                        <span className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>
                          +{reasonCode.weight}
                        </span>
                      </div>
                      <p style={{ marginTop: 4, fontSize: 13, color: "var(--fg-2)" }}>
                        {reasonCode.label}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="fx-mono" style={{ fontSize: 12, color: "var(--muted)" }}>
                  Aucun reason code pour ce module sur ce scénario.
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </ForensicPage>
  );
}

function ModuleCard({
  module,
  score,
  active,
  onTest,
}: {
  module: (typeof MODULES)[number];
  score?: DetectorScore;
  active: boolean;
  onTest: () => void;
}) {
  const statusTone = module.status === "active" ? "ok" : module.status === "demo" ? "warn" : "";
  return (
    <div
      className={`fx-stat ${statusTone}`}
      style={active ? { borderColor: "var(--risk)", borderLeftColor: "var(--risk)" } : undefined}
    >
      <div className="fx-stat-top">
        <span className="glyph">{module.glyph}</span>
        <span className="fx-tag" style={{ fontSize: 10 }}>{module.status}</span>
      </div>
      <div className="fx-mono" style={{ marginTop: 12, fontSize: 13, color: "var(--fg)", fontWeight: 500, lineHeight: 1.3 }}>
        {module.title}
      </div>
      <p className="fx-mono" style={{ marginTop: 6, fontSize: 11, color: "var(--muted)", lineHeight: 1.5 }}>
        {module.dataUsed}
      </p>
      <div style={{ marginTop: 12, background: "var(--bg-2)", border: "1px solid var(--border)", padding: "8px 10px" }}>
        <div className="fx-eyebrow">Score partiel</div>
        <div className="fx-mono" style={{ fontSize: 16, color: "var(--fg)", marginTop: 4, fontWeight: 500 }}>
          {score ? `${score.score}/${score.maxScore}` : "n/a"}
        </div>
      </div>
      <button
        type="button"
        className={active ? "fx-btn sm" : "fx-btn-ghost sm"}
        style={{ marginTop: 12 }}
        onClick={onTest}
      >
        Tester le module
      </button>
    </div>
  );
}
