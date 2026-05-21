"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { HOME_ANCHORS } from "./data";
import { Dossier } from "./dossier";
import { ForensicSidebar } from "./forensic-sidebar";
import { Hero } from "./hero";
import { Footer, HashBand, Referentials, Ticker, Trust } from "./sections";
import { ToolMap } from "./tool-map";

function ScrollProgress() {
  const [pct, setPct] = useState(0);
  useEffect(() => {
    const onScroll = () => {
      const h = document.documentElement;
      const total = h.scrollHeight - h.clientHeight;
      setPct(total > 0 ? h.scrollTop / total : 0);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  return <div className="scroll-progress" style={{ transform: `scaleX(${pct})` }} />;
}

function useScrollSpy(ids: string[]) {
  const [active, setActive] = useState(ids[0]);
  useEffect(() => {
    const onScroll = () => {
      const off = 120;
      let current = ids[0];
      for (const id of ids) {
        const el = document.getElementById(id);
        if (!el) continue;
        const r = el.getBoundingClientRect();
        if (r.top - off <= 0) current = id;
      }
      setActive(current);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [ids]);
  return active;
}

export function ForensicHome() {
  const active = useScrollSpy(HOME_ANCHORS);
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  // Reflect the next-themes choice onto the forensic skin's own attribute.
  // Defaults to dark (the "salle d'enquête" identity) before hydration.
  const theme = mounted && resolvedTheme === "light" ? "light" : "dark";

  return (
    <div className="forensic" data-theme={theme} data-grain="on" data-density="default">
      <ScrollProgress />
      <div className="shell">
        <ForensicSidebar activeAnchor={active} />
        <main className="shell-main">
          <Hero />
          <Ticker />
          <Dossier />
          <ToolMap />
          <Referentials />
          <Trust />
          <HashBand />
          <Footer />
        </main>
      </div>
    </div>
  );
}
