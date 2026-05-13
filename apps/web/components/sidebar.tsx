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

type NavItem = {
  href: string;
  label: string;
  Icon: typeof LayoutDashboard;
};

type NavSection = {
  title: string;
  items: NavItem[];
};

const SECTIONS: NavSection[] = [
  {
    title: "🧭 Pilotage",
    items: [
      { href: "/dashboard", label: "Cockpit", Icon: LayoutDashboard },
      { href: "/tour", label: "Tour guidé", Icon: GraduationCap },
      { href: "/sandbox", label: "Sandbox", Icon: Play },
      { href: "/cases", label: "File d'investigation", Icon: Inbox },
      { href: "/alerts", label: "Alertes & monitoring", Icon: Bell },
      { href: "/collab", label: "Collaboration", Icon: Users },
    ],
  },
  {
    title: "🗂️ Données",
    items: [
      { href: "/upload", label: "Import des données", Icon: Upload },
      { href: "/master-history", label: "Référentiel — historique", Icon: History },
      { href: "/sirene", label: "Contrôle Sirene", Icon: CheckCircle2 },
    ],
  },
  {
    title: "🧮 Contrôles statistiques",
    items: [
      { href: "/benford", label: "Loi de Benford", Icon: BarChart3 },
      { href: "/duplicates", label: "Doublons", Icon: Copy },
      { href: "/structuring", label: "Fractionnement", Icon: Minus },
      { href: "/sanctions", label: "Sanctions & PEP", Icon: Scale },
      { href: "/decp-rbe", label: "DECP & RBE INPI", Icon: Scale },
    ],
  },
  {
    title: "🤖 Détection ML",
    items: [
      { href: "/anomalies", label: "Anomalies (ML)", Icon: Brain },
      { href: "/rings", label: "Anneaux de fraude", Icon: Network },
      { href: "/score", label: "Explorateur de score", Icon: Lightbulb },
    ],
  },
  {
    title: "🔎 Investigation",
    items: [
      { href: "/vendors", label: "Fiche fournisseur 360°", Icon: UserCircle2 },
      { href: "/exports", label: "Synthèse — export", Icon: FileText },
      { href: "/audit", label: "Piste d'audit", Icon: Fingerprint },
    ],
  },
  {
    title: "📚 Gouvernance",
    items: [
      { href: "/methodology", label: "Méthodologie", Icon: BookOpen },
      { href: "/governance", label: "Gouvernance", Icon: ShieldCheck },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
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
      <nav className="flex-1 overflow-y-auto px-2 py-3 text-sm">
        {SECTIONS.map((section) => (
          <div key={section.title} className="mb-4">
            <div className="px-3 pb-1 text-[0.7rem] uppercase tracking-wider text-[#9aa3b2]">
              {section.title}
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
                      <span className="truncate">{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>
      <div className="border-t border-[#1f3a6e] px-4 py-3 text-[0.7rem] text-[#9aa3b2]">
        v0.5.0 · Migration v2 Phase 1
      </div>
    </aside>
  );
}
