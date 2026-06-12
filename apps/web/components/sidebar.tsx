"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLocale } from "@/components/locale-provider";
import { P2PDemoLauncher } from "@/components/demo-p2p/P2PDemoLauncher";

type Badge = "live" | "risk" | "new";
type NavItem = { href: string; labelKey: string; glyph: string; badge?: Badge };
type NavSection = { code: string; titleKey: string; items: NavItem[] };

const SECTIONS: NavSection[] = [
  {
    code: "01",
    titleKey: "nav.section_command",
    items: [
      { href: "/", labelKey: "nav.home", glyph: "◉" },
      { href: "/dashboard", labelKey: "nav.cockpit", glyph: "▤" },
      { href: "/sandbox", labelKey: "nav.sandbox", glyph: "▶", badge: "new" },
      { href: "/tour", labelKey: "nav.tour", glyph: "→" },
    ],
  },
  {
    code: "02",
    titleKey: "nav.section_workbench",
    items: [
      { href: "/p2p-scenarios", labelKey: "nav.p2p_scenarios", glyph: "⊞", badge: "new" },
      { href: "/risk-test-lab", labelKey: "nav.risk_test_lab", glyph: "⊟", badge: "new" },
      { href: "/risk-lab-sepa", labelKey: "nav.risk_lab_sepa", glyph: "§", badge: "new" },
      { href: "/detection-studio", labelKey: "nav.detection_studio", glyph: "✦", badge: "new" },
      { href: "/fraud-case-360/CASE-APP-BANK-001", labelKey: "nav.case_360", glyph: "◎", badge: "new" },
      { href: "/risk-docs", labelKey: "nav.risk_docs", glyph: "≡", badge: "new" },
    ],
  },
  {
    code: "03",
    titleKey: "nav.section_investigation",
    items: [
      { href: "/cases", labelKey: "nav.cases", glyph: "▣", badge: "risk" },
      { href: "/vendors", labelKey: "nav.vendors", glyph: "◫" },
      { href: "/alerts", labelKey: "nav.alerts", glyph: "!" },
      { href: "/collab", labelKey: "nav.collab", glyph: "⌘" },
    ],
  },
  {
    code: "04",
    titleKey: "nav.section_controls",
    items: [
      { href: "/anomalies", labelKey: "nav.anomalies", glyph: "△" },
      { href: "/duplicates", labelKey: "nav.duplicates", glyph: "□" },
      { href: "/structuring", labelKey: "nav.structuring", glyph: "⌒" },
      { href: "/sanctions", labelKey: "nav.sanctions", glyph: "✕", badge: "risk" },
      { href: "/rings", labelKey: "nav.rings", glyph: "◇" },
      { href: "/score", labelKey: "nav.score", glyph: "Σ" },
    ],
  },
  {
    code: "05",
    titleKey: "nav.section_data",
    items: [
      { href: "/upload", labelKey: "nav.upload", glyph: "↥" },
      { href: "/sirene", labelKey: "nav.sirene", glyph: "✓", badge: "live" },
      { href: "/decp-rbe", labelKey: "nav.decp_rbe", glyph: "✓", badge: "live" },
      { href: "/master-history", labelKey: "nav.master_history", glyph: "↺" },
    ],
  },
  {
    code: "06",
    titleKey: "nav.section_governance",
    items: [
      { href: "/methodology", labelKey: "nav.methodology", glyph: "§" },
      { href: "/audit", labelKey: "nav.audit", glyph: "✓" },
      { href: "/exports", labelKey: "nav.exports", glyph: "↓" },
      { href: "/governance", labelKey: "nav.governance", glyph: "★" },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { t } = useLocale();
  const [open, setOpen] = useState(false);

  const close = () => setOpen(false);

  return (
    <>
      <button className="sb-toggle" onClick={() => setOpen(!open)} aria-label="Menu">
        ☰ MENU
      </button>

      <aside className={`sidebar ${open ? "open" : ""}`} aria-label="Navigation produit">
        <Link href="/" className="sb-head" onClick={close}>
          <div className="sb-mark" aria-hidden>
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
        </Link>

        <div className="sb-status">
          <div>
            <div className="lbl">{t("shell.priority_risk")}</div>
            <div className="val">92</div>
            <div className="sub">ALPHACOM SERVICES</div>
          </div>
          <div className="pill">CRIT</div>
        </div>

        <nav className="sb-nav">
          {SECTIONS.map((sec) => (
            <div key={sec.code}>
              <div className="sb-section">
                <span>
                  §{sec.code} · {t(sec.titleKey)}
                </span>
                <span className="filet" />
              </div>
              {sec.items.map((it) => {
                const active =
                  pathname === it.href ||
                  (it.href !== "/" && pathname.startsWith(`${it.href}/`));
                return (
                  <Link
                    key={it.href}
                    href={it.href}
                    className={`sb-item ${active ? "active" : ""}`}
                    title={t(it.labelKey)}
                    onClick={close}
                  >
                    <span className="sb-icon">{it.glyph}</span>
                    <span>{t(it.labelKey)}</span>
                    {it.badge && (
                      <span className={`sb-badge ${it.badge}`}>
                        {it.badge === "risk"
                          ? t("shell.badge_risk")
                          : it.badge === "live"
                            ? t("shell.badge_live")
                            : t("shell.badge_new")}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>

        <div className="sb-foot">
          <P2PDemoLauncher variant="sidebar" />
          <div className="meta">
            <span>
              <span className="dot">●</span> RGPD-ready
            </span>
            <span>{t("shell.audit_signed")}</span>
          </div>
        </div>
      </aside>
    </>
  );
}
