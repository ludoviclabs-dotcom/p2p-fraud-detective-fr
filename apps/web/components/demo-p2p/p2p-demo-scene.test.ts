import { describe, expect, it } from "vitest";

import { getDemoContent } from "./p2p-demo-content";
import {
  CAMERA_PRESETS,
  DEMO_FORBIDDEN_TERMS,
  DEMO_SCENES,
  DEMO_SCENE_IDS,
  DEMO_TOTAL_DURATION_MS,
} from "./p2p-demo-data";

const LOCALES = ["fr", "en"] as const;

describe("cinematic P2P demo scene contract", () => {
  it("keeps the guided walkthrough close to a 60 second product demo", () => {
    expect(DEMO_SCENES).toHaveLength(13);
    expect(DEMO_TOTAL_DURATION_MS).toBeGreaterThanOrEqual(55_000);
    expect(DEMO_TOTAL_DURATION_MS).toBeLessThanOrEqual(65_000);
  });

  it("defines a camera, caption, console stream and callouts for every scene", () => {
    for (const scene of DEMO_SCENES) {
      expect(CAMERA_PRESETS[scene.camera]).toBeDefined();
      expect(scene.durationMs).toBeGreaterThan(0);
      expect(scene.consoleEvents.length).toBeGreaterThan(0);

      for (const locale of LOCALES) {
        const content = getDemoContent(locale);
        expect(content.sceneLabels[scene.id]).toBeTruthy();
        expect(content.sceneCaptions[scene.id].title).toBeTruthy();
        expect(content.sceneCaptions[scene.id].body).toBeTruthy();

        for (const event of scene.consoleEvents) {
          expect(content.consoleEvents[event]).toBeTruthy();
        }

        for (const callout of scene.callouts) {
          expect(content.callouts[callout].title).toBeTruthy();
          expect(content.callouts[callout].body).toBeTruthy();
        }
      }
    }
  });

  it("keeps scene ids stable for e2e and review references", () => {
    expect(DEMO_SCENE_IDS).toEqual([
      "cold-open",
      "command-launch",
      "cockpit-wide",
      "search-zoom",
      "data-cascade",
      "supplier-row",
      "case-file-open",
      "score-breakdown",
      "evidence-build",
      "alert-sequence",
      "review-path",
      "export-ready",
      "final-summary",
    ]);
  });

  it("ships an explicit export-ready ending for analysis handoff", () => {
    for (const locale of LOCALES) {
      const content = getDemoContent(locale);
      expect(content.casePacket.exportTitle).toBeTruthy();
      expect(content.casePacket.exportMeta).toMatch(/PDF|JSON/i);
      expect(content.casePacket.exportFeatures).toHaveLength(4);
      expect(content.sceneCaptions["export-ready"].title).toBeTruthy();
      expect(content.callouts["export-ready"].body).toBeTruthy();
    }
  });

  it("keeps the bilingual narrative legally prudent", () => {
    for (const locale of LOCALES) {
      const content = JSON.stringify(getDemoContent(locale)).toLowerCase();
      for (const term of DEMO_FORBIDDEN_TERMS) {
        expect(content).not.toContain(term.toLowerCase());
      }
    }
  });
});
