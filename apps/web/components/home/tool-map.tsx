"use client";

import Link from "next/link";
import { TOOL_GROUPS } from "./data";
import { SectionHead } from "./sections";

export function ToolMap() {
  return (
    <section className="toolmap container" id="toolmap" data-anchor="toolmap">
      <SectionHead
        num="06"
        kicker="Cartographie · 26 outils"
        title={
          <>
            Trois <span className="italic">intentions</span>, un seul produit.
          </>
        }
      />

      <div className="tm-grid">
        {TOOL_GROUPS.map((g) => (
          <div className="tm-section" key={g.code}>
            <div className="tm-head">
              <div className="tm-num">VOIE · {g.code}</div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--muted)" }}>
                {g.tools.length} outils
              </div>
            </div>
            <div className="tm-title" style={{ marginBottom: 12 }}>
              {g.title}
            </div>
            <div className="tm-intent">{g.intent}</div>
            <div className="tm-tools">
              {g.tools.map((t) => (
                <Link className="tm-tool" key={t.href} href={t.href}>
                  <span className="ic">{t.ic}</span>
                  <span className="lab">{t.lab}</span>
                  <span className="tm-arrow">↗</span>
                </Link>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
