"use client";

import Link from "next/link";
import { Fragment, useEffect, useMemo, useState } from "react";
import { CaseGraph } from "./case-graph";
import { SCENARIOS } from "./data";

const LEDE =
  "Pas une anomalie statistique exotique. Un changement de RIB que personne n'a contre-signé. " +
  "Cet outil détecte sous 24h 100% des modifications fournisseur à risque — avec preuve signée par votre CAC.";

export function Hero() {
  const [activeId, setActiveId] = useState<string>(SCENARIOS[0].id);
  const [revealedCount, setRevealedCount] = useState(0);
  const [animScore, setAnimScore] = useState(0);
  const [clock, setClock] = useState<Date | null>(null);

  const scenario = useMemo(
    () => SCENARIOS.find((s) => s.id === activeId) ?? SCENARIOS[0],
    [activeId],
  );

  // Reveal findings progressively after a scenario change.
  useEffect(() => {
    setRevealedCount(0);
    const total = scenario.findings.length;
    let i = 0;
    const id = setInterval(() => {
      i += 1;
      setRevealedCount(i);
      if (i >= total) clearInterval(id);
    }, 320);
    return () => clearInterval(id);
  }, [activeId, scenario.findings.length]);

  // Animate the risk score from 0 to its target.
  useEffect(() => {
    setAnimScore(0);
    const target = scenario.score;
    let raf = 0;
    const start = performance.now();
    const dur = 900;
    const tick = (now: number) => {
      const k = Math.min(1, (now - start) / dur);
      const eased = 1 - Math.pow(1 - k, 4);
      setAnimScore(Math.round(target * eased));
      if (k < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [activeId, scenario.score]);

  // Live wall clock — client only, to avoid an SSR/hydration mismatch.
  useEffect(() => {
    setClock(new Date());
    const id = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const timeStr = clock ? clock.toTimeString().slice(0, 8) : "--:--:--";
  const dateStr = clock
    ? clock.toLocaleDateString("fr-FR", { day: "2-digit", month: "short", year: "numeric" })
    : "—";

  const showIbanScan = scenario.id === "iban-swap" || scenario.id === "sanction";

  return (
    <section className="hero" id="hero">
      <div className="container">
        <div className="hero-grid">
          {/* LEFT — copy */}
          <div>
            <div className="hero-id">
              <span className="tag">Dossier · N° 2026/041</span>
              <span className="filet" />
              <span className="tag">v2 · {dateStr}</span>
            </div>

            <h1 className="hero-title">
              80% des fraudes P2P passent par <span className="italic">un IBAN.</span>
            </h1>

            <p className="hero-lede">{LEDE}</p>

            <div className="cta-row">
              <a href="#acte-i" className="btn-primary">
                Ouvrir un dossier <span>↗</span>
              </a>
              <a href="#pipeline" className="btn-ghost">
                Voir la cascade <span>↓</span>
              </a>
            </div>

            <div className="hero-foot">
              <span>
                <span className="dot" />1 247 fournisseurs surveillés
              </span>
              <span>· 10 détecteurs en cascade ·</span>
              <span>Piste d&apos;audit Ed25519</span>
            </div>

            <div
              style={{
                marginTop: 18,
                border: "1px solid var(--border)",
                borderLeft: "2px solid var(--risk)",
                padding: "12px 14px",
                fontFamily: "var(--font-mono)",
                fontSize: 11,
                lineHeight: 1.8,
                color: "var(--muted)",
              }}
            >
              <span style={{ color: "var(--fg)" }}>FNC-RF</span> (Banque de France · mai 2026)
              filtre les IBAN déjà signalés, côté banque. <span style={{ color: "var(--fg)" }}>VoP</span>{" "}
              (oct. 2025) vérifie le nom au moment du virement.{" "}
              <span style={{ color: "var(--fg)" }}>
                Cet outil agit en amont — au changement du master data
              </span>
              , avec une preuve Ed25519 qu&apos;un tiers vérifie sans accès à la plateforme.{" "}
              <Link href="/fnc-rf-fraude-iban" style={{ color: "var(--risk)", textDecoration: "none" }}>
                Les 3 couches →
              </Link>
            </div>
          </div>

          {/* RIGHT — live console */}
          <div className="console" role="region" aria-label="Console forensique">
            <div className="console-head">
              <div className="console-head-left">
                <span className="live">● LIVE</span>
                <span>FRAUD-OPS · CMD CENTER</span>
              </div>
              <div className="console-head-right">{timeStr} · CET</div>
            </div>

            <div className="scenarios" role="tablist">
              {SCENARIOS.map((s, i) => (
                <button
                  key={s.id}
                  className={`scenario-tab ${activeId === s.id ? "active" : ""}`}
                  onClick={() => setActiveId(s.id)}
                  role="tab"
                  aria-selected={activeId === s.id}
                >
                  <span className="num">[{String(i + 1).padStart(2, "0")}]</span>
                  {s.code}
                </button>
              ))}
            </div>

            <div className="console-main">
              <div className="console-stage">
                <div className="case-id">
                  <div>
                    <div className="left">
                      DOSSIER · {scenario.code} · {scenario.severity}
                    </div>
                    <div className="vendor">
                      {scenario.vendor} · SIREN {scenario.siren}
                    </div>
                  </div>
                  <div className="score-wrap">
                    <div className="score-label">Risk Score</div>
                    <div className="score-value">{animScore}</div>
                  </div>
                </div>

                {showIbanScan && (
                  <div className="iban-scan">
                    <div className="scan-line" />
                    <div className="label">IBAN bénéficiaire — VÉRIFICATION</div>
                    <div className="iban-row">
                      <div>
                        <div className="iban-value">
                          {scenario.iban.current
                            .replace(scenario.iban.changedSeg, "__SEG__")
                            .split("__SEG__")
                            .map((part, i, arr) => (
                              <Fragment key={i}>
                                {part}
                                {i < arr.length - 1 && (
                                  <span className="changed">{scenario.iban.changedSeg}</span>
                                )}
                              </Fragment>
                            ))}
                        </div>
                        {scenario.iban.previous !== scenario.iban.current && (
                          <div className="iban-prev">précédent · {scenario.iban.previous}</div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                <div className="graph-wrap">
                  <CaseGraph kind={scenario.graph} />
                </div>
              </div>

              <div className="rail">
                <div className="rail-title">
                  <span>Findings</span>
                  <span className="count">
                    {revealedCount}/{scenario.findings.length}
                  </span>
                </div>
                {scenario.findings.slice(0, revealedCount).map((f, i) => (
                  <div
                    className="finding"
                    key={`${activeId}-${i}`}
                    style={{ animationDelay: `${i * 60}ms` }}
                  >
                    <div
                      className={`mark ${
                        f.level === "warn" ? "warn" : f.level === "info" ? "info" : ""
                      }`}
                    >
                      {f.mark}
                    </div>
                    <div className="body">
                      <div className="ttl">{f.title}</div>
                      <div className="fd-det">{f.det}</div>
                    </div>
                    <div className="conf">{f.conf}</div>
                  </div>
                ))}
                {revealedCount < scenario.findings.length && (
                  <div className="finding" style={{ opacity: 0.5, animation: "none" }}>
                    <div className="mark" style={{ background: "var(--dim)" }}>
                      ·
                    </div>
                    <div className="body">
                      <div className="fd-det" style={{ color: "var(--muted)" }}>
                        analyse en cours…
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="console-foot">
              <div className="metric">
                <div className="lbl">Exposition</div>
                <div className="val">{scenario.exposure}</div>
                <div className="delta up">↑ {Math.round(scenario.confidence * 100)}%</div>
              </div>
              <div className="metric">
                <div className="lbl">Confiance modèle</div>
                <div className="val">{scenario.confidence.toFixed(2)}</div>
                <div className="delta">p · combinée</div>
              </div>
              <div className="metric">
                <div className="lbl">Dossiers</div>
                <div className="val">{scenario.cases}</div>
                <div className="delta">à traiter</div>
              </div>
              <div className="metric">
                <div className="lbl">SLA dépassé</div>
                <div className="val">{scenario.sla}</div>
                <div className={`delta ${scenario.sla > 0 ? "up" : "dn"}`}>
                  {scenario.sla > 0 ? "intervention" : "OK"}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
