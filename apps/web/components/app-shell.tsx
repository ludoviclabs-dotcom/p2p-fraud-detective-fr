"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { useTheme } from "next-themes";
import { BarChart3, Command, FileSearch, Home, Moon, Play, Search, ShieldCheck, Sun } from "lucide-react";
import { RISK_SCENARIOS } from "@/data/risk-scenarios";
import { Sidebar } from "@/components/sidebar";
import { useLocale, type Locale } from "@/components/locale-provider";
import { P2PDemoLauncher } from "@/components/demo-p2p/P2PDemoLauncher";

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
  const pathname = usePathname();
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // The home route ("/") renders the forensic landing page, which ships its
  // own sidebar and shell — bypass the legacy app chrome there.
  if (pathname === "/") {
    return <>{children}</>;
  }

  const theme = mounted && resolvedTheme === "light" ? "light" : "dark";

  return (
    <div className="forensic flex" data-theme={theme} data-grain="off">
      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[70] focus:bg-[#c8392c] focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-white"
        >
          Aller au contenu principal
        </a>
        <Topbar />
        <main
          id="main-content"
          tabIndex={-1}
          className="min-w-0 flex-1 overflow-y-auto bg-[#f7f9fc] pb-20 text-[#111827] dark:bg-[#08111f] dark:text-white lg:pb-0"
          style={{ fontFamily: "var(--font-inter), system-ui, sans-serif" }}
        >
          {children}
        </main>
        <MobileBottomNav />
      </div>
    </div>
  );
}

function Topbar() {
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
    <header className="topbar">
      <div className="topbar-inner">
        <form onSubmit={submitSearch} role="search" className="topbar-search">
          <label htmlFor="global-command-search" className="sr-only">
            {t("shell.search_label")}
          </label>
          <div className="topbar-search-box">
            <Search size={15} aria-hidden />
            <input
              ref={inputRef}
              id="global-command-search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onFocus={() => setFocused(true)}
              onBlur={() => window.setTimeout(() => setFocused(false), 120)}
              placeholder={t("shell.search_placeholder")}
            />
            <span className="topbar-kbd">
              <Command size={10} aria-hidden /> K
            </span>
          </div>
          {focused && normalizedQuery ? (
            <div className="topbar-results">
              {matches.length ? (
                matches.map((item) => (
                  <Link
                    key={`${item.href}-${item.title}`}
                    href={item.href}
                    className="topbar-result"
                    onClick={() => {
                      setFocused(false);
                      setQuery("");
                    }}
                  >
                    <span>{item.title}</span>
                    <span className="cat">{item.category}</span>
                  </Link>
                ))
              ) : (
                <div className="topbar-empty">{t("shell.search_no_results")}</div>
              )}
            </div>
          ) : null}
        </form>

        <div style={{ display: "flex", alignItems: "center", gap: 12, marginLeft: "auto" }}>
          <div className="topbar-badge">
            <ShieldCheck size={13} aria-hidden />
            {t("shell.public_sources")}
          </div>

          <LangSwitch locale={locale} setLocale={setLocale} />

          <button
            type="button"
            onClick={() => setTheme(isDark ? "light" : "dark")}
            className="topbar-btn"
            aria-label={t("shell.toggle_theme")}
          >
            {isDark ? <Sun size={15} /> : <Moon size={15} />}
          </button>

          <P2PDemoLauncher variant="topbar" />
        </div>
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
    <div className="topbar-lang">
      {(["fr", "en"] as const).map((item) => (
        <button
          key={item}
          type="button"
          onClick={() => setLocale(item)}
          className={locale === item ? "active" : ""}
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
    <nav className="bottomnav">
      {MOBILE_NAV.map((item) => {
        const active = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={active ? "active" : ""}
            aria-label={t(item.labelKey)}
          >
            <item.Icon size={16} aria-hidden />
            <span className="lbl">{t(item.mobileLabelKey)}</span>
          </Link>
        );
      })}
    </nav>
  );
}
