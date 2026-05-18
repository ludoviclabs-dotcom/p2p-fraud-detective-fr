"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import {
  BarChart3,
  Command,
  FileSearch,
  Home,
  Menu,
  Moon,
  Play,
  Search,
  ShieldCheck,
  Sun,
} from "lucide-react";
import { Sidebar } from "@/components/sidebar";
import { useLocale, type Locale } from "@/components/locale-provider";
import { cn } from "@/lib/utils";

const MOBILE_NAV = [
  { href: "/", label: "Accueil", Icon: Home },
  { href: "/dashboard", label: "Cockpit", Icon: BarChart3 },
  { href: "/sandbox", label: "Démo", Icon: Play },
  { href: "/cases", label: "Cases", Icon: FileSearch },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex min-h-dvh bg-[#f7f9fc] text-[#111827] dark:bg-[#08111f] dark:text-white">
      <Sidebar className="hidden lg:flex" />
      {mobileOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            aria-label="Fermer la navigation"
            className="absolute inset-0 bg-[#08111f]/45"
            onClick={() => setMobileOpen(false)}
          />
          <Sidebar
            className="relative h-full shadow-2xl"
            onNavigate={() => setMobileOpen(false)}
          />
        </div>
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar onMenu={() => setMobileOpen(true)} />
        <main className="min-w-0 flex-1 overflow-y-auto pb-20 lg:pb-0">
          {children}
        </main>
        <MobileBottomNav />
      </div>
    </div>
  );
}

function Topbar({ onMenu }: { onMenu: () => void }) {
  const { locale, setLocale } = useLocale();
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const isDark = mounted && resolvedTheme === "dark";

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <header className="sticky top-0 z-40 border-b border-[#e6ebf2]/90 bg-white/88 px-4 py-3 backdrop-blur-xl dark:border-white/10 dark:bg-[#08111f]/88 lg:px-8">
      <div className="flex items-center gap-3">
        <button
          type="button"
          aria-label="Ouvrir la navigation"
          onClick={onMenu}
          className="focus-ring inline-flex h-10 w-10 items-center justify-center rounded-md border border-[#e6ebf2] bg-white text-[#111827] lg:hidden"
        >
          <Menu size={18} />
        </button>

        <div className="hidden min-w-0 flex-1 items-center gap-3 rounded-md border border-[#e6ebf2] bg-[#f7f9fc] px-3 py-2 text-sm text-[#667085] shadow-inner dark:border-white/10 dark:bg-white/[0.04] md:flex">
          <Search size={16} />
          <span className="truncate">
            Rechercher un SIREN, fournisseur, IBAN, case ou alerte...
          </span>
          <span className="ml-auto inline-flex items-center gap-1 rounded border border-[#d7deea] bg-white px-1.5 py-0.5 font-mono text-[11px] text-[#667085] dark:border-white/10 dark:bg-white/5">
            <Command size={11} /> K
          </span>
        </div>

        <div className="ml-auto hidden items-center gap-2 rounded-md border border-[#d7deea] bg-white px-3 py-2 text-xs font-medium text-[#12a876] dark:border-white/10 dark:bg-white/[0.04] sm:flex">
          <ShieldCheck size={14} />
          Sources publiques actives
        </div>

        <LangSwitch locale={locale} setLocale={setLocale} />

        <button
          type="button"
          onClick={() => setTheme(isDark ? "light" : "dark")}
          className="focus-ring inline-flex h-10 w-10 items-center justify-center rounded-md border border-[#e6ebf2] bg-white text-[#667085] transition-colors hover:text-[#111827] dark:border-white/10 dark:bg-white/[0.04] dark:text-white/70"
          aria-label="Changer de thème"
        >
          {isDark ? <Sun size={16} /> : <Moon size={16} />}
        </button>

        <Link
          href="/sandbox"
          className="focus-ring hidden h-10 items-center gap-2 rounded-md bg-[#2f6bff] px-4 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-[#2457d6] sm:inline-flex"
        >
          <Play size={15} />
          Demander une démo
        </Link>
      </div>
    </header>
  );
}

function LangSwitch({
  locale,
  setLocale,
}: {
  locale: Locale;
  setLocale: (locale: Locale) => void;
}) {
  return (
    <div className="hidden rounded-md border border-[#e6ebf2] bg-white p-1 text-xs font-semibold dark:border-white/10 dark:bg-white/[0.04] sm:flex">
      {(["fr", "en"] as const).map((item) => (
        <button
          key={item}
          type="button"
          onClick={() => setLocale(item)}
          className={cn(
            "rounded px-2 py-1 transition-colors",
            locale === item
              ? "bg-[#08111f] text-white dark:bg-white dark:text-[#08111f]"
              : "text-[#667085] hover:text-[#111827] dark:text-white/65",
          )}
        >
          {item.toUpperCase()}
        </button>
      ))}
    </div>
  );
}

function MobileBottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-[#e6ebf2] bg-white/94 px-2 py-2 backdrop-blur-xl dark:border-white/10 dark:bg-[#08111f]/94 lg:hidden">
      <div className="grid grid-cols-4 gap-1">
        {MOBILE_NAV.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex flex-col items-center gap-1 rounded-md px-2 py-1.5 text-[11px] font-medium transition-colors",
                active
                  ? "bg-[#eaf1ff] text-[#2f6bff] dark:bg-white/10"
                  : "text-[#667085] hover:bg-[#f7f9fc] dark:text-white/65",
              )}
            >
              <item.Icon size={16} />
              {item.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
