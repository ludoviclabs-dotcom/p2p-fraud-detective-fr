"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Bell,
  BookOpen,
  BriefcaseBusiness,
  CircleDollarSign,
  Database,
  FileCheck2,
  FileSearch,
  Gauge,
  GitBranch,
  Home,
  Landmark,
  Network,
  Play,
  Scale,
  ShieldCheck,
  Upload,
  Users,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useLocale } from "@/components/locale-provider";

type NavItem = {
  href: string;
  labelKey: string;
  Icon: LucideIcon;
  badge?: "demo" | "risk" | "new";
};

type NavSection = {
  titleKey: string;
  items: NavItem[];
};

const SECTIONS: NavSection[] = [
  {
    titleKey: "nav.section_command",
    items: [
      { href: "/", labelKey: "nav.home", Icon: Home },
      { href: "/dashboard", labelKey: "nav.cockpit", Icon: Gauge, badge: "demo" },
      { href: "/sandbox", labelKey: "nav.sandbox", Icon: Play, badge: "new" },
      { href: "/tour", labelKey: "nav.tour", Icon: BookOpen },
    ],
  },
  {
    titleKey: "nav.section_investigation",
    items: [
      { href: "/cases", labelKey: "nav.cases", Icon: FileSearch, badge: "risk" },
      { href: "/vendors", labelKey: "nav.vendors", Icon: BriefcaseBusiness },
      { href: "/alerts", labelKey: "nav.alerts", Icon: Bell },
      { href: "/collab", labelKey: "nav.collab", Icon: Users },
    ],
  },
  {
    titleKey: "nav.section_controls",
    items: [
      { href: "/anomalies", labelKey: "nav.anomalies", Icon: BarChart3 },
      { href: "/duplicates", labelKey: "nav.duplicates", Icon: FileCheck2 },
      { href: "/structuring", labelKey: "nav.structuring", Icon: CircleDollarSign },
      { href: "/sanctions", labelKey: "nav.sanctions", Icon: Scale, badge: "risk" },
      { href: "/rings", labelKey: "nav.rings", Icon: Network },
      { href: "/score", labelKey: "nav.score", Icon: GitBranch },
    ],
  },
  {
    titleKey: "nav.section_data",
    items: [
      { href: "/upload", labelKey: "nav.upload", Icon: Upload },
      { href: "/sirene", labelKey: "nav.sirene", Icon: ShieldCheck, badge: "demo" },
      { href: "/decp-rbe", labelKey: "nav.decp_rbe", Icon: Landmark, badge: "demo" },
      { href: "/master-history", labelKey: "nav.master_history", Icon: Database },
    ],
  },
  {
    titleKey: "nav.section_governance",
    items: [
      { href: "/methodology", labelKey: "nav.methodology", Icon: BookOpen },
      { href: "/audit", labelKey: "nav.audit", Icon: FileCheck2 },
      { href: "/exports", labelKey: "nav.exports", Icon: FileSearch },
      { href: "/governance", labelKey: "nav.governance", Icon: ShieldCheck },
    ],
  },
];

export function Sidebar({
  className,
  onNavigate,
}: {
  className?: string;
  onNavigate?: () => void;
}) {
  const pathname = usePathname();
  const { t } = useLocale();

  return (
    <aside
      className={cn(
        "flex h-dvh w-72 shrink-0 flex-col border-r border-white/10 bg-[#08111f] text-white",
        className,
      )}
    >
      <Link
        href="/"
        onClick={onNavigate}
        className="flex items-center gap-3 border-b border-white/10 px-5 py-5"
      >
        <div className="grid h-10 w-10 place-items-center rounded-md bg-[#2f6bff] text-sm font-black text-white shadow-lg shadow-[#2f6bff]/25">
          FD
        </div>
        <div className="min-w-0">
          <div className="text-sm font-semibold leading-tight">
            P2P Fraud Detective
          </div>
          <div className="mt-0.5 text-xs text-white/50">Command Center</div>
        </div>
      </Link>

      <div className="border-b border-white/10 px-4 py-3">
        <div className="rounded-md border border-white/10 bg-white/[0.04] p-3">
          <div className="text-[11px] font-medium uppercase tracking-wider text-white/45">
            Scenario demo
          </div>
          <div className="mt-2 flex items-end justify-between gap-3">
            <div>
              <div className="text-2xl font-bold leading-none">87</div>
              <div className="mt-1 text-xs text-white/55">Score synthetique</div>
            </div>
            <div className="rounded bg-[#fff0f1] px-2 py-1 text-xs font-semibold text-[#e5484d]">
              CRITICAL
            </div>
          </div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4 text-sm">
        {SECTIONS.map((section) => (
          <div key={section.titleKey} className="mb-5">
            <div className="px-2 pb-2 text-[11px] font-semibold uppercase tracking-wider text-white/38">
              {t(section.titleKey)}
            </div>
            <ul className="space-y-1">
              {section.items.map((item) => {
                const active =
                  pathname === item.href ||
                  (item.href !== "/" && pathname.startsWith(`${item.href}/`));
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      onClick={onNavigate}
                      className={cn(
                        "group flex items-center gap-3 rounded-md px-3 py-2.5 text-white/68 transition-colors",
                        active
                          ? "bg-white text-[#08111f] shadow-sm"
                          : "hover:bg-white/[0.07] hover:text-white",
                      )}
                    >
                      <item.Icon
                        size={17}
                        strokeWidth={2}
                        className={cn(
                          active ? "text-[#2f6bff]" : "text-white/42",
                        )}
                        aria-hidden
                      />
                      <span className="min-w-0 flex-1 truncate">
                        {t(item.labelKey)}
                      </span>
                      {item.badge ? <NavBadge value={item.badge} active={active} /> : null}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t border-white/10 p-4">
        <Link
          href="/sandbox"
          onClick={onNavigate}
          className="flex items-center justify-center gap-2 rounded-md bg-[#2f6bff] px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-[#2f6bff]/20 transition-colors hover:bg-[#2457d6]"
        >
          <Play size={15} />
          Lancer la demo
        </Link>
        <div className="mt-3 grid grid-cols-2 gap-2 text-[11px] text-white/48">
          <span>Donnees demo</span>
          <span className="text-right">Signature off</span>
        </div>
      </div>
    </aside>
  );
}

function NavBadge({ value, active }: { value: "demo" | "risk" | "new"; active: boolean }) {
  const label = value === "risk" ? "Risque" : "Demo";
  return (
    <span
      className={cn(
        "rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
        active
          ? "bg-[#eaf1ff] text-[#2f6bff]"
          : value === "risk"
            ? "bg-[#fff0f1] text-[#e5484d]"
            : "bg-[#eaf1ff] text-[#2f6bff]",
      )}
    >
      {label}
    </span>
  );
}
