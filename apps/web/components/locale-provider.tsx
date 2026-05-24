"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import {
  isLocale,
  LOCALE_STORAGE_KEY,
  translate,
  type Locale,
} from "@/lib/i18n";

export type { Locale } from "@/lib/i18n";

type LocaleContextValue = {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
};

const LocaleContext = createContext<LocaleContextValue | null>(null);

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("fr");

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const stored = window.localStorage.getItem(LOCALE_STORAGE_KEY);
      if (isLocale(stored)) setLocaleState(stored);
    } catch {
      // Ignore storage failures so the language switch still works in memory.
    }
  }, []);

  useEffect(() => {
    if (typeof document !== "undefined") {
      document.documentElement.lang = locale;
    }
  }, [locale]);

  const setLocale = (nextLocale: Locale) => {
    setLocaleState(nextLocale);
    if (typeof window !== "undefined") {
      try {
        window.localStorage.setItem(LOCALE_STORAGE_KEY, nextLocale);
      } catch {
        // Keep the selected locale for this session even if persistence fails.
      }
    }
  };

  const t = (key: string, params?: Record<string, string | number>): string =>
    translate(key, locale, params);

  return (
    <LocaleContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </LocaleContext.Provider>
  );
}

export function useLocale(): LocaleContextValue {
  const ctx = useContext(LocaleContext);
  if (!ctx) {
    return {
      locale: "fr",
      setLocale: () => {},
      t: (key: string, params?: Record<string, string | number>) =>
        translate(key, "fr", params),
    };
  }
  return ctx;
}
