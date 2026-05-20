"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
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
import { RISK_SCENARIOS } from "@/data/risk-scenarios";
import { Sidebar } from "@/components/sidebar";
import { useLocale, type Locale } from "@/components/locale-provider";
import { cn } from "@/lib/utils";

const MOBILE_NAV = [
  { href: "/", labelKey: "nav.home", mobileLabelKey: "nav.home", Icon: Home },
  { href: "/dashboard", labelKey: "nav.cockpit", mobileLabelKey: "nav.cockpit", Icon: BarChart3 },
  { href: "/sandbox", labelKey: "nav.sandbox", mobileLabelKey: "shell.badge_new", Icon: Play },
  { href: "/cases", labelKey: "nav.cases", mobileLabelKey: "nav.cases_mobile", Icon: FileSearch },
];

type SearchTarget = {
  title: string;
  href: string;
  category: string;
  keywords: string;
};

const SEARCH_TARGETS: SearchTarget[] = [
  { title: "Accueil", href: "/", category: "Page", keywords: "home accueil command center" },
  { title: "Cockpit risque P2P", href: "/dashboard", category: "Page", keywords: "dashboard cockpit kpi risque" },
  { title: "Scenarios fraude", href: "/sandbox", category: "Demo", keywords: "sandbox demo guidee fraude" },
  { title: "Scenarios P2P", href: "/p2p-scenarios", category: "Workbench", keywords: "p2p sepa fraude scenario" },
  { title: "Risk Test Lab", href: "/risk-test-lab", category: "Workbench", keywords: "api json score evidence pack test" },
  { title: "Detection Studio", href: "/detection-studio", category: "Workbench", keywords: "modules detecteurs reason codes" },
  { title: "Fraud Case 360", href: "/fraud-case-360/CASE-APP-BANK-001", category: "Case", keywords: "case app bank advisor evidence" },
  { title: "Docs & glossaire", href: "/risk-docs", category: "Docs", keywords: "documentation glossaire api modele" },
  { title: "File d'investigation", href: "/cases", category: "Investigation", keywords: "case management queue investigation" },
  { title: "Fournisseur 360", href: "/vendors", category: "Investigation", keywords: "vendor fournisseur iban siren" },
  { title: "Alertes & monitoring", href: "/alerts", category: "Investigation", keywords: "alertes monitoring sse" },
  { title: "Sanctions & PEP", href: "/sanctions", category: "Controle", keywords: "aml sanctions pep" },
  { title: "Anneaux de fraude", href: "/rings", category: "Graphe", keywords: "graphe mule account réseau iban" },
  { title: "Explorateur de score", href: "/score", category: "Controle", keywords: "score invoice reason" },
  { title: "Import des donnees", href: "/upload", category: "Data", keywords: "upload csv excel fichier" },
  { title: "Historique referentiel", href: "/master-history", category: "Audit", keywords: "master data rib historique audit" },
  { title: "Piste d'audit", href: "/audit", category: "Gouvernance", keywords: "audit trail preuves ed25519" },
  { title: "Exports", href: "/exports", category: "Gouvernance", keywords: "export synthese evidence" },
  { title: "Fournisseur V00444", href: "/vendors/V00444", category: "Fournisseur", keywords: "vendor fournisseur V00444" },
  { title: "Fournisseur V00167", href: "/vendors/V00167", category: "Fournisseur", keywords: "vendor fournisseur V00167" },
  ...RISK_SCENARIOS.map((scenario) => ({
    title: scenario.title,
    href: `/fraud-case-360/${encodeURIComponent(scenario.caseId)}`,
    category: "Scenario P2P",
    keywords: `${scenario.caseId} ${scenario.description} ${scenario.expectedTypology}`,
  })),
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { t } = useLocale();

  return (
    <div className="flex min-h-dvh bg-[#f7f9fc] text-[#111827] dark:bg-[#08111f] dark:text-white">
      <Sidebar className="hidden lg:flex" />
      {mobileOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            aria-label={t("shell.close_nav")}
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
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[60] focus:rounded-md focus:bg-[#08111f] focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-white focus:shadow-lg"
        >
          Aller au contenu principal
        </a>
        <Topbar onMenu={() => setMobileOpen(true)} />
        <main id="main-content" tabIndex={-1} className="min-w-0 flex-1 overflow-y-auto pb-20 lg:pb-0">
          {children}
        </main>
        <MobileBottomNav />
      </div>
    </div>
  );
}

function Topbar({ onMenu }: { onMenu: () => void }) {
  const { locale, setLocale, t } = useLocale();
  const { resolvedTheme, setTheme } = useTheme();
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [mounted, setMounted] = useState(false);
  const [query, setQuery] = useState("");
  const [focused, setFocused] = useState(false);
  const isDark = mounted && resolvedTheme === "dark";
  const normalizedQuery = query.trim().toLowerCase();
  const matches = useMemo(() => {
    if (!normalizedQuery) return [];
    return SEARCH_TARGETS.filter((item) =>
      `${item.title} ${item.category} ${item.keywords}`.toLowerCase().includes(normalizedQuery),
    ).slice(0, 6);
  }, [normalizedQuery]);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        inputRef.current?.focus();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const target = matches[0];
    if (!target) return;
    setFocused(false);
    setQuery("");
    router.push(target.href);
  }

  return (
    <header className="sticky top-0 z-40 border-b border-[#e6ebf2]/90 bg-white/88 px-4 py-3 backdrop-blur-xl dark:border-white/10 dark:bg-[#08111f]/88 lg:px-8">
      <div className="flex items-center gap-3">
        <button
          type="button"
          aria-label={t("shell.open_nav")}
          onClick={onMenu}
          className="focus-ring inline-flex h-10 w-10 items-center justify-center rounded-md border border-[#e6ebf2] bg-white text-[#111827] lg:hidden"
        >
          <Menu size={18} />
        </button>

        <form
          onSubmit={submitSearch}
          role="search"
          className="relative hidden min-w-0 flex-1 md:block"
        >
          <label htmlFor="global-command-search" className="sr-only">
            {t("shell.search_label")}
          </label>
          <div className="flex items-center gap-3 rounded-md border border-[#e6ebf2] bg-[#f7f9fc] px-3 py-2 text-sm text-[#667085] shadow-inner transition-colors focus-within:border-[#2f6bff] focus-within:bg-white dark:border-white/10 dark:bg-white/[0.04]">
            <Search size={16} aria-hidden />
            <input
              ref={inputRef}
              id="global-command-search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onFocus={() => setFocused(true)}
              onBlur={() => window.setTimeout(() => setFocused(false), 120)}
              placeholder={t("shell.search_placeholder")}
              className="min-w-0 flex-1 bg-transparent text-sm text-[#111827] outline-none placeholder:text-[#667085] dark:text-white"
            />
            <span className="ml-auto inline-flex shrink-0 items-center gap-1 rounded border border-[#d7deea] bg-white px-1.5 py-0.5 font-mono text-[11px] text-[#667085] dark:border-white/10 dark:bg-white/5">
              <Command size={11} aria-hidden /> K
            </span>
          </div>
          {focused && normalizedQuery ? (
            <div className="absolute left-0 right-0 top-12 z-50 rounded-md border border-[#e6ebf2] bg-white p-2 shadow-xl dark:border-white/10 dark:bg-[#0c1729]">
              {matches.length ? (
                <div className="space-y-1">
                  {matches.map((item) => (
                    <Link
                      key={`${item.href}-${item.title}`}
                      href={item.href}
                      className="focus-ring flex items-center justify-between gap-3 rounded px-3 py-2 text-sm hover:bg-[#f7f9fc] dark:hover:bg-white/[0.06]"
                      onClick={() => {
                        setFocused(false);
                        setQuery("");
                      }}
                    >
                      <span className="min-w-0 truncate font-medium text-[#111827] dark:text-white">
                        {item.title}
                      </span>
                      <span className="shrink-0 text-xs font-semibold uppercase tracking-wide text-[#667085]">
                        {item.category}
                      </span>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="rounded px-3 py-2 text-sm text-[#667085]">
                  {t("shell.search_no_results")}
                </div>
              )}
            </div>
          ) : null}
        </form>

        <div className="ml-auto hidden items-center gap-2 rounded-md border border-[#d7deea] bg-white px-3 py-2 text-xs font-medium text-[#027a48] dark:border-white/10 dark:bg-white/[0.04] sm:flex">
          <ShieldCheck size={14} />
          {t("shell.public_sources")}
        </div>

        <LangSwitch locale={locale} setLocale={setLocale} />

        <button
          type="button"
          onClick={() => setTheme(isDark ? "light" : "dark")}
          className="focus-ring inline-flex h-10 w-10 items-center justify-center rounded-md border border-[#e6ebf2] bg-white text-[#667085] transition-colors hover:text-[#111827] dark:border-white/10 dark:bg-white/[0.04] dark:text-white/70"
          aria-label={t("shell.toggle_theme")}
        >
          {isDark ? <Sun size={16} /> : <Moon size={16} />}
        </button>

        <Link
          href="/sandbox"
          className="focus-ring hidden h-10 items-center gap-2 rounded-md bg-[#2f6bff] px-4 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-[#2457d6] sm:inline-flex"
        >
          <Play size={15} />
          {t("shell.request_demo")}
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
  const { t } = useLocale();

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
                "flex min-w-0 flex-col items-center gap-1 rounded-md px-1.5 py-1.5 text-[11px] font-medium transition-colors",
                active
                  ? "bg-[#eaf1ff] text-[#2f6bff] dark:bg-white/10"
                  : "text-[#667085] hover:bg-[#f7f9fc] dark:text-white/65",
              )}
              aria-label={t(item.labelKey)}
            >
              <item.Icon size={16} aria-hidden />
              <span className="max-w-full truncate">{t(item.mobileLabelKey)}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
