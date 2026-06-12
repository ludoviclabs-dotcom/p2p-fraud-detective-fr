"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useLocale } from "@/components/locale-provider";
import { getDemoContent } from "./p2p-demo-content";
import { DEMO_ALERTS, type P2PDemoPhase } from "./p2p-demo-data";
import { P2PForensicOverlay } from "./P2PForensicOverlay";
import { P2PPreflightBrief } from "./P2PPreflightBrief";
import { P2PCommandCockpit } from "./P2PCommandCockpit";
import { P2PCaseFile360 } from "./P2PCaseFile360";
import { P2PEvidenceDrawer } from "./P2PEvidenceDrawer";
import { P2PRecommendationPanel } from "./P2PRecommendationPanel";
import { P2PRegulatoryAlert } from "./P2PRegulatoryAlert";

const SEARCH_QUERY = "V00474";

/**
 * Orchestrateur de la démo guidée. Gère la timeline (≈27 s) via des timers
 * tracés (`useRef<number[]>`) tous nettoyés au démontage / Passer / Rejouer.
 * `Escape` saute à la phase finale (puis ferme). `prefers-reduced-motion`
 * affiche directement la phase finale statique.
 */
export function P2PInvestigationDemo({ onClose }: { onClose: () => void }) {
  const { locale } = useLocale();
  const content = getDemoContent(locale);
  const router = useRouter();

  const [phase, setPhase] = useState<P2PDemoPhase>("preflight");
  const [typed, setTyped] = useState("");
  const timersRef = useRef<number[]>([]);

  const clearTimers = useCallback(() => {
    timersRef.current.forEach((id) => window.clearTimeout(id));
    timersRef.current = [];
  }, []);

  const schedule = useCallback((fn: () => void, delay: number) => {
    const id = window.setTimeout(fn, delay);
    timersRef.current.push(id);
  }, []);

  const startTimeline = useCallback(() => {
    clearTimers();
    setPhase("preflight");
    setTyped("");

    const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      setTyped(SEARCH_QUERY);
      setPhase("final");
      return;
    }

    schedule(() => setPhase("cockpit"), 1500);
    schedule(() => {
      setPhase("search");
      // Frappe caractère par caractère, délais aléatoires 80–180 ms.
      let acc = "";
      let t = 0;
      for (const ch of SEARCH_QUERY) {
        t += 80 + Math.floor(Math.random() * 100);
        schedule(() => {
          acc += ch;
          setTyped(acc);
        }, t);
      }
    }, 3000);
    schedule(() => setPhase("loading"), 6000);
    schedule(() => setPhase("results"), 8000);
    schedule(() => setPhase("case360"), 11000);
    schedule(() => setPhase("evidence"), 14000);
    schedule(() => setPhase("alerts"), 18000);
    schedule(() => setPhase("recommendations"), 24000);
    schedule(() => setPhase("final"), 27000);
  }, [clearTimers, schedule]);

  useEffect(() => {
    startTimeline();
    return () => clearTimers();
  }, [startTimeline, clearTimers]);

  const handleSkip = () => {
    if (phase === "final") {
      onClose();
      return;
    }
    clearTimers();
    setTyped(SEARCH_QUERY);
    setPhase("final");
  };

  const handleReplay = () => startTimeline();

  const go = (href: string) => {
    onClose();
    router.push(href);
  };

  // Escape : saute à la phase finale, puis ferme. Rebind à chaque rendu pour
  // capturer la phase courante dans `handleSkip`.
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        handleSkip();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  return (
    <P2PForensicOverlay
      phase={phase}
      content={content}
      onSkip={handleSkip}
      isFinal={phase === "final"}
    >
      {renderScene()}
    </P2PForensicOverlay>
  );

  function renderScene() {
    if (phase === "preflight") {
      return <P2PPreflightBrief content={content} />;
    }
    if (phase === "cockpit" || phase === "search" || phase === "loading" || phase === "results") {
      return <P2PCommandCockpit content={content} phase={phase} typed={typed} />;
    }
    if (phase === "case360") {
      return <P2PCaseFile360 content={content} gaugeActive />;
    }
    if (phase === "evidence") {
      return (
        <div
          className="p2p-demo-case-grid"
          style={{ display: "grid", gap: 16, gridTemplateColumns: "minmax(0, 1.1fr) minmax(0, 0.9fr)" }}
        >
          <P2PCaseFile360 content={content} gaugeActive />
          <P2PEvidenceDrawer content={content} />
        </div>
      );
    }
    if (phase === "alerts") {
      return (
        <div style={{ maxWidth: 760, margin: "auto", display: "flex", flexDirection: "column", gap: 10 }}>
          <div className="p2p-demo-eyebrow">{content.case360.signalsTitle}</div>
          {DEMO_ALERTS.map((a, i) => {
            const al = content.alerts[a.id];
            if (!al) return null;
            return (
              <P2PRegulatoryAlert
                key={a.id}
                delayMs={i * 220}
                title={al.title}
                text={al.text}
                badges={al.badges}
                cta={al.cta}
                severity={a.severity}
              />
            );
          })}
        </div>
      );
    }
    if (phase === "recommendations") {
      return (
        <div style={{ maxWidth: 620, margin: "auto" }}>
          <P2PRecommendationPanel content={content} />
        </div>
      );
    }
    // final
    return (
      <div
        className="p2p-demo-panel p2p-demo-spring"
        style={{ maxWidth: 600, margin: "auto", textAlign: "center", borderTop: "3px solid var(--risk)" }}
      >
        <h2 style={{ fontFamily: "var(--font-display)", fontSize: 26, color: "var(--fg)", margin: "0 0 10px", fontWeight: 400 }}>
          {content.final.title}
        </h2>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--warn)", marginBottom: 10 }}>
          {content.final.stats}
        </div>
        <p style={{ fontSize: 14, lineHeight: 1.65, color: "var(--fg-2)", margin: "0 0 18px" }}>
          {content.final.tagline}
        </p>
        <div style={{ display: "flex", gap: 10, justifyContent: "center", flexWrap: "wrap" }}>
          <button type="button" className="p2p-demo-cta primary" onClick={() => go("/dashboard")}>
            {content.controls.exploreCockpit}
          </button>
          <button type="button" className="p2p-demo-cta" onClick={() => go("/sandbox")}>
            {content.controls.viewScenarios}
          </button>
          <button type="button" className="p2p-demo-cta" onClick={handleReplay}>
            {content.controls.replay}
          </button>
        </div>
        <p style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--dim)", marginTop: 18, lineHeight: 1.6 }}>
          {content.final.disclaimer}
        </p>
      </div>
    );
  }
}
