"use client";

import { useState } from "react";
import Link from "next/link";
import { SB_SECTIONS } from "./data";

export function ForensicSidebar({
  activeAnchor,
  onNavigate,
}: {
  activeAnchor: string;
  onNavigate?: (href: string) => void;
}) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button className="sb-toggle" onClick={() => setOpen(!open)} aria-label="Menu">
        ☰ MENU
      </button>

      <aside className={`sidebar ${open ? "open" : ""}`} aria-label="Navigation produit">
        <div className="sb-head">
          <div className="sb-mark" aria-label="P2P Fraud Detective">
            <span className="corner tl" />
            <span className="corner br" />
            <svg viewBox="0 0 24 24" aria-hidden>
              <line x1="12" y1="3" x2="12" y2="9" stroke="currentColor" strokeWidth="1" />
              <line x1="12" y1="15" x2="12" y2="21" stroke="currentColor" strokeWidth="1" />
              <line x1="3" y1="12" x2="9" y2="12" stroke="currentColor" strokeWidth="1" />
              <line x1="15" y1="12" x2="21" y2="12" stroke="currentColor" strokeWidth="1" />
              <circle cx="12" cy="12" r="5.5" fill="none" stroke="currentColor" strokeWidth="1" />
              <circle cx="12" cy="12" r="2.2" fill="var(--risk)" />
            </svg>
          </div>
          <div className="sb-brand-lines">
            <div className="top">P2P FRAUD DETECTIVE</div>
            <div>FR · v2.1 · MIT</div>
          </div>
        </div>

        <div className="sb-status">
          <div>
            <div className="lbl">Risque prioritaire</div>
            <div className="val">92</div>
            <div className="sub">ALPHACOM SERVICES</div>
          </div>
          <div className="pill">CRIT</div>
        </div>

        <nav className="sb-nav">
          {SB_SECTIONS.map((sec) => (
            <div key={sec.title}>
              <div className="sb-section">
                <span>
                  §{sec.code} · {sec.title}
                </span>
                <span className="filet" />
              </div>
              {sec.items.map((it) => {
                const isHash = it.href.startsWith("#");
                const isActive = isHash && activeAnchor === it.href.slice(1);
                const className = `sb-item ${isActive ? "active" : ""}`;
                const inner = (
                  <>
                    <span className="sb-icon">{it.ic}</span>
                    <span>{it.label}</span>
                    {it.badge && (
                      <span className={`sb-badge ${it.badge}`}>
                        {it.badge === "risk" ? "RISK" : it.badge === "live" ? "LIVE" : "NEW"}
                      </span>
                    )}
                  </>
                );

                if (isHash) {
                  return (
                    <a
                      key={it.href}
                      href={it.href}
                      className={className}
                      title={it.hint}
                      onClick={(e) => {
                        e.preventDefault();
                        const el = document.getElementById(it.href.slice(1));
                        if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
                        setOpen(false);
                        onNavigate?.(it.href);
                      }}
                    >
                      {inner}
                    </a>
                  );
                }

                return (
                  <Link
                    key={it.href}
                    href={it.href}
                    className={className}
                    title={it.hint}
                    onClick={() => {
                      setOpen(false);
                      onNavigate?.(it.href);
                    }}
                  >
                    {inner}
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>

        <div className="sb-foot">
          <Link href="/sandbox" className="quick">
            ▶ Lancer la sandbox
          </Link>
          <div className="meta">
            <span>
              <span className="dot">●</span> RGPD-ready
            </span>
            <span>Ed25519 ✓</span>
          </div>
        </div>
      </aside>
    </>
  );
}
