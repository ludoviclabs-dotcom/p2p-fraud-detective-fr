"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import type { DemoContent } from "./p2p-demo-content";
import {
  DEMO_ALERTS,
  DEMO_SCENES,
  FINAL_DEMO_SCENE,
  type P2PConsoleEventId,
  type P2PDemoScene,
} from "./p2p-demo-data";
import { P2PCalloutLayer } from "./P2PCalloutLayer";
import { P2PCameraFrame } from "./P2PCameraFrame";
import { P2PCaseFile360 } from "./P2PCaseFile360";
import { P2PCasePacket } from "./P2PCasePacket";
import { P2PCommandCockpit } from "./P2PCommandCockpit";
import { P2PCommandConsole } from "./P2PCommandConsole";
import { P2PDataLineageBeam } from "./P2PDataLineageBeam";
import { P2PEvidenceDrawer } from "./P2PEvidenceDrawer";
import { P2PFocusSpotlight } from "./P2PFocusSpotlight";
import { P2PForensicOverlay } from "./P2PForensicOverlay";
import { P2PInvestigationMap } from "./P2PInvestigationMap";
import { P2PPreflightBrief } from "./P2PPreflightBrief";
import { P2PRecommendationPanel } from "./P2PRecommendationPanel";
import { P2PRegulatoryAlert } from "./P2PRegulatoryAlert";
import { P2PSceneCaption } from "./P2PSceneCaption";
import { P2PScoreBreakdown } from "./P2PScoreBreakdown";

const SEARCH_QUERY = "V00474";
const FINAL_SCENE_INDEX = DEMO_SCENES.findIndex((scene) => scene.id === FINAL_DEMO_SCENE);

export function P2PDemoSceneDirector({
  content,
  onClose,
}: {
  content: DemoContent;
  onClose: () => void;
}) {
  const router = useRouter();
  const [sceneIndex, setSceneIndex] = useState(0);
  const [typed, setTyped] = useState("");
  const [runId, setRunId] = useState(0);
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
    setRunId((value) => value + 1);
    setSceneIndex(0);
    setTyped("");

    const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      setTyped(SEARCH_QUERY);
      setSceneIndex(FINAL_SCENE_INDEX);
      return;
    }

    let elapsed = 0;
    DEMO_SCENES.forEach((scene, index) => {
      if (index > 0) {
        schedule(() => setSceneIndex(index), elapsed);
      }

      if (scene.id === "search-zoom") {
        let typeDelay = elapsed + 280;
        let nextValue = "";
        for (const ch of SEARCH_QUERY) {
          typeDelay += 135;
          schedule(() => {
            nextValue += ch;
            setTyped(nextValue);
          }, typeDelay);
        }
      }

      if (scene.id === "supplier-row") {
        schedule(() => setTyped(SEARCH_QUERY), elapsed + 100);
      }

      elapsed += scene.durationMs;
    });
  }, [clearTimers, schedule]);

  useEffect(() => {
    startTimeline();
    return () => clearTimers();
  }, [startTimeline, clearTimers]);

  const currentScene = DEMO_SCENES[sceneIndex] ?? DEMO_SCENES[0]!;
  const isFinal = currentScene.id === FINAL_DEMO_SCENE;

  const consoleEvents = useMemo(() => {
    const seen = new Set<P2PConsoleEventId>();
    const events: P2PConsoleEventId[] = [];
    for (const scene of DEMO_SCENES.slice(0, sceneIndex + 1)) {
      for (const event of scene.consoleEvents) {
        if (!seen.has(event)) {
          seen.add(event);
          events.push(event);
        }
      }
    }
    return events;
  }, [sceneIndex]);

  const handleSkip = useCallback(() => {
    if (isFinal) {
      onClose();
      return;
    }
    clearTimers();
    setTyped(SEARCH_QUERY);
    setSceneIndex(FINAL_SCENE_INDEX);
  }, [clearTimers, isFinal, onClose]);

  const handleReplay = useCallback(() => {
    startTimeline();
  }, [startTimeline]);

  const go = useCallback(
    (href: string) => {
      onClose();
      router.push(href);
    },
    [onClose, router],
  );

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        handleSkip();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [handleSkip]);

  return (
    <P2PForensicOverlay
      scene={currentScene.id}
      sceneIndex={sceneIndex}
      sceneCount={DEMO_SCENES.length}
      content={content}
      onSkip={handleSkip}
      isFinal={isFinal}
    >
      <div className="p2p-demo-directed-stage" key={`${runId}-${currentScene.id}`}>
        <P2PCameraFrame preset={currentScene.camera} scene={currentScene.id}>
          {renderScene(currentScene.id)}
        </P2PCameraFrame>
        <P2PFocusSpotlight spotlight={currentScene.spotlight} />
        <P2PCalloutLayer ids={currentScene.callouts} content={content} />
        <P2PSceneCaption scene={currentScene.id} content={content} />
        <P2PCommandConsole events={consoleEvents} content={content} />
      </div>
    </P2PForensicOverlay>
  );

  function renderScene(scene: P2PDemoScene) {
    if (scene === "cold-open") {
      return <P2PCommandCockpit content={content} phase="cockpit" typed={typed} />;
    }

    if (scene === "command-launch") {
      return (
        <div className="p2p-demo-command-grid">
          <P2PPreflightBrief content={content} />
          <P2PInvestigationMap content={content} activeIndex={0} />
        </div>
      );
    }

    if (scene === "cockpit-wide" || scene === "search-zoom" || scene === "supplier-row") {
      const mode = DEMO_SCENES[sceneIndex]?.cockpitMode ?? "cockpit";
      return <P2PCommandCockpit content={content} phase={mode} typed={typed} />;
    }

    if (scene === "data-cascade") {
      return (
        <div className="p2p-demo-cascade-grid">
          <P2PCommandCockpit content={content} phase="loading" typed={SEARCH_QUERY} />
          <P2PDataLineageBeam content={content} />
        </div>
      );
    }

    if (scene === "case-file-open") {
      return <P2PCaseFile360 content={content} gaugeActive />;
    }

    if (scene === "score-breakdown") {
      return <P2PScoreBreakdown content={content} />;
    }

    if (scene === "evidence-build") {
      return (
        <div className="p2p-demo-case-grid">
          <P2PCaseFile360 content={content} gaugeActive />
          <P2PEvidenceDrawer content={content} />
        </div>
      );
    }

    if (scene === "alert-sequence") {
      return (
        <div className="p2p-demo-alert-sequence">
          <div className="p2p-demo-eyebrow">{content.labels.findings}</div>
          {DEMO_ALERTS.map((alert, index) => {
            const copy = content.alerts[alert.id];
            if (!copy) return null;
            return (
              <P2PRegulatoryAlert
                key={alert.id}
                delayMs={index * 140}
                title={copy.title}
                text={copy.text}
                observation={copy.observation}
                why={copy.why}
                proof={copy.proof}
                action={copy.action}
                labels={content.labels}
                badges={copy.badges}
                cta={copy.cta}
                severity={alert.severity}
              />
            );
          })}
        </div>
      );
    }

    if (scene === "review-path") {
      return (
        <div className="p2p-demo-command-grid">
          <P2PRecommendationPanel content={content} />
          <P2PInvestigationMap content={content} activeIndex={5} />
        </div>
      );
    }

    return (
      <P2PCasePacket
        content={content}
        onExplore={() => go("/dashboard")}
        onScenarios={() => go("/sandbox")}
        onReplay={handleReplay}
      />
    );
  }
}
