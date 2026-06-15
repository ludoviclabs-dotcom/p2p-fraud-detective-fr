"use client";

import { useEffect, useState, type RefObject } from "react";

export interface AnchoredRect {
  left: number;
  top: number;
  width: number;
  height: number;
}

/**
 * Duree (ms) pendant laquelle on re-mesure l'ancre image par image apres un
 * changement de scene : couvre l'animation d'entree de la camera
 * (`cinematicSceneCut` + `cameraSettle`) et la cascade des items, pour que le
 * reticule reste colle a l'element pendant qu'il bouge.
 */
const SETTLE_MS = 1100;
const EPS = 0.5;

function diff(a: AnchoredRect | null, b: AnchoredRect | null): boolean {
  if (!a || !b) return a !== b;
  return (
    Math.abs(a.left - b.left) > EPS ||
    Math.abs(a.top - b.top) > EPS ||
    Math.abs(a.width - b.width) > EPS ||
    Math.abs(a.height - b.height) > EPS
  );
}

/**
 * Mesure en continu la position d'un element `[data-demo-anchor="<anchor>"]`
 * dans le repere local du `stage`. On lit `getBoundingClientRect` (qui inclut
 * deja la transformation `translate3d/scale` de la camera) puis on soustrait le
 * rect du stage : le resultat tombe pile sur l'element quel que soit le
 * pan/zoom ou le reflow responsive. C'est ce qui corrige les decalages des
 * anciens carres positionnes en pourcentage.
 */
export function useAnchoredRect(
  stageRef: RefObject<HTMLElement | null>,
  anchor: string | undefined,
  token: unknown,
): AnchoredRect | null {
  const [rect, setRect] = useState<AnchoredRect | null>(null);

  useEffect(() => {
    if (!anchor) {
      setRect(null);
      return;
    }
    const stage = stageRef.current;
    if (!stage) return;

    let stopped = false;
    let raf = 0;
    let last: AnchoredRect | null = null;

    const findTarget = () =>
      stage.querySelector<HTMLElement>(`[data-demo-anchor="${anchor}"]`);

    const measure = (): AnchoredRect | null => {
      const target = findTarget();
      if (!target) return null;
      const a = target.getBoundingClientRect();
      const s = stage.getBoundingClientRect();
      return {
        left: a.left - s.left,
        top: a.top - s.top,
        width: a.width,
        height: a.height,
      };
    };

    const apply = (force = false) => {
      const next = measure();
      if (next && (force || diff(last, next))) {
        last = next;
        setRect(next);
      }
    };

    apply(true);

    const start = performance.now();
    const loop = (now: number) => {
      if (stopped) return;
      apply();
      if (now - start < SETTLE_MS) {
        raf = requestAnimationFrame(loop);
      }
    };
    raf = requestAnimationFrame(loop);

    const onChange = () => apply(true);
    const ro = new ResizeObserver(onChange);
    ro.observe(stage);
    const target = findTarget();
    if (target) ro.observe(target);
    window.addEventListener("resize", onChange);
    window.addEventListener("scroll", onChange, true);

    return () => {
      stopped = true;
      cancelAnimationFrame(raf);
      ro.disconnect();
      window.removeEventListener("resize", onChange);
      window.removeEventListener("scroll", onChange, true);
    };
  }, [anchor, token, stageRef]);

  return rect;
}
