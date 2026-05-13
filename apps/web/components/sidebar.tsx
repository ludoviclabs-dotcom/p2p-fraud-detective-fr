"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Play,
  Inbox,
  Bell,
  Users,
  Upload,
  History,
  CheckCircle2,
  BarChart3,
  Copy,
  Minus,
  Scale,
  Brain,
  Network,
  Lightbulb,
  UserCircle2,
  FileText,
  Fingerprint,
  BookOpen,
  ShieldCheck,
  GraduationCap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useLocale, type Locale } from "@/components/locale-provider";

type NavItem = {
  href: string;
  labelKey: string;
  Icon: typeof LayoutDashboard;
};

type NavSection = {
  titleKey: string;
  items: NavItem[];
};

const SECTIONS: NavSection[] = [
  {
    titleKey: "nav.section_pilotage",
    items: [
      { href: "/dashboard", labelKey: "nav.cockpit", Icon: LayoutDashboard },
      { href: "/tour", labelKey: "nav.tour", Icon: GraduationCap },
      { href: "/sandbox", labelKey: "nav.sandbox", Icon: Play },
      { href: "/cases", labelKey: "nav.cases", Icon: Inbox },
      { href: "/alerts", labelKey: "nav.alerts", Icon: Bell },
      { href: "/collab", labelKey: "nav.collab", Icon: Users },
    ],
  },
  {
    titleKey: "nav.section_donnees",
    items: [
      { href: "/upload", labelKey: "nav.upload", Icon: Upload },
      { href: "/master-history", labelKey: "nav.master_history", Icon: History },
      { href: "/sirene", labelKey: "nav.sirene", Icon: CheckCircle2 },
    ],
  },
  {
    titleKey: "nav.section_controles",
    items: [
      { href: "/benford", labelKey: "nav.benford", Icon: BarChart3 },
      { href: "/duplicates", labelKey: "nav.duplicates", Icon: Copy },
      { href: "/structuring", labelKey: "nav.structuring", Icon: Minus },
      { href: "/sanctions", labelKey: "nav.sanctions", Icon: Scale },
      { href: "/decp-rbe", labelKey: "nav.decp_rbe", Icon: Scale },
    ],
  },
  {
    titleKey: "nav.section_ml",
    items: [
      { href: "/anomalies", labelKey: "nav.anomalies", Icon: Brain },
      { href: "/rings", labelKey: "nav.rings", Icon: Network },
      { href: "/score", labelKey: "nav.score", Icon: Lightbulb },
      { href: "/findings", labelKey: "nav.findings", Icon: BarChart3 },
    ],
  },
  {
    titleKey: "nav.section_investigation",
    items: [
      { href: "/vendors", labelKey: "nav.vendors", Icon: UserCircle2 },
      { href: "/exports", labelKey: "nav.exports", Icon: FileText },
      { href: "/audit", labelKey: "nav.audit", Icon: Fingerprint },
    ],
  },
  {
    titleKey: "nav.section_gouvernance",
    items: [
      { href: "/methodology", labelKey: "nav.methodology", Icon: BookOpen },
      { href: "/governance", labelKey: "nav.governance", Icon: ShieldCheck },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { t, locale, setLocale } = useLocale();

  return (
    <aside className="flex h-screen w-64 flex-col bg-[#0f1b33] text-[#e6eaf2]">
      <div className="flex items-center gap-2 border-b border-[#1f3a6e] px-4 py-4">
        <div className="h-8 w-8 rounded bg-[#e5a93a] text-[#0f1b33] grid place-items-center font-bold">
          P
        </div>
        <div className="text-sm font-semibold leading-tight">
          P2P Fraud
          <br />
          Detective FR
        </div>
      </div>

      {/* Sélecteur de langue */}
      <div className="flex items-center gap-1 border-b border-[#1f3a6e] px-3 py-2 text-xs">
        <span className="text-[#9aa3b2]">{t("common.language")} :</span>
        <LangButton current={locale} target="fr" onClick={setLocale}>
          🇫🇷 FR
        </LangButton>
        <LangButton current={locale} target="en" onClick={setLocale}>
          🇬🇧 EN
        </LangButton>
      </div>

      <nav className="flex-1 overflow-y-auto px-2 py-3 text-sm">
        {SECTIONS.map((section) => (
          <div key={section.titleKey} className="mb-4">
            <div className="px-3 pb-1 text-[0.7rem] uppercase tracking-wider text-[#9aa3b2]">
              {t(section.titleKey)}
            </div>
            <ul className="space-y-0.5">
              {section.items.map((item) => {
                const active = pathname === item.href;
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={cn(
                        "flex items-center gap-2 rounded px-3 py-1.5 transition-colors",
                        active
                          ? "bg-[#1f3a6e] text-[#e5a93a]"
                          : "hover:bg-[#162847] hover:text-white",
                      )}
                    >
                      <item.Icon size={14} aria-hidden />
                      <span className="truncate">{t(item.labelKey)}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>
      <div className="border-t border-[#1f3a6e] px-4 py-3 text-[0.7rem] text-[#9aa3b2]">
        v0.5.0 · Migration v2 Phase 7
      </div>
    </aside>
  );
}

function LangButton({
  current,
  target,
  onClick,
  children,
}: {
  current: Locale;
  target: Locale;
  onClick: (l: Locale) => void;
  children: string;
}) {
  const active = current === target;
  return (
    <button
      type="button"
      onClick={() => onClick(target)}
      className={cn(
        "rounded px-1.5 py-0.5 transition-colors",
        active
          ? "bg-[#1f3a6e] text-[#e5a93a]"
          : "text-[#9aa3b2] hover:text-white",
      )}
    >
      {children}
    </button>
  );
}
