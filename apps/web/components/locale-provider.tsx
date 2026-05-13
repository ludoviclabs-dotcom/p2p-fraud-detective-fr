"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export type Locale = "fr" | "en";

const STORAGE_KEY = "p2pfd_locale";

type Translations = Record<string, Record<Locale, string>>;

// Catalogue minimal Phase 7 — extension progressive aux pages au fil du besoin.
const TRANSLATIONS: Translations = {
  "common.app_name": { fr: "P2P Fraud Detective FR", en: "P2P Fraud Detective FR" },
  "common.demo_banner": {
    fr: "DÉMONSTRATEUR · v0.5 / v2",
    en: "DEMONSTRATOR · v0.5 / v2",
  },
  "common.language": { fr: "Langue", en: "Language" },
  "nav.section_pilotage": { fr: "🧭 Pilotage", en: "🧭 Steering" },
  "nav.section_donnees": { fr: "🗂️ Données", en: "🗂️ Data" },
  "nav.section_controles": {
    fr: "🧮 Contrôles statistiques",
    en: "🧮 Statistical controls",
  },
  "nav.section_ml": { fr: "🤖 Détection ML", en: "🤖 ML detection" },
  "nav.section_investigation": { fr: "🔎 Investigation", en: "🔎 Investigation" },
  "nav.section_gouvernance": { fr: "📚 Gouvernance", en: "📚 Governance" },
  "nav.cockpit": { fr: "Cockpit", en: "Cockpit" },
  "nav.tour": { fr: "Tour guidé", en: "Guided tour" },
  "nav.sandbox": { fr: "Sandbox commerciale", en: "Commercial sandbox" },
  "nav.cases": { fr: "File d'investigation", en: "Investigation queue" },
  "nav.alerts": { fr: "Alertes & monitoring", en: "Alerts & monitoring" },
  "nav.collab": { fr: "Collaboration", en: "Collaboration" },
  "nav.upload": { fr: "Import des données", en: "Data import" },
  "nav.master_history": { fr: "Référentiel — historique", en: "Master data history" },
  "nav.sirene": { fr: "Contrôle Sirene", en: "Sirene check" },
  "nav.benford": { fr: "Loi de Benford", en: "Benford's Law" },
  "nav.duplicates": { fr: "Doublons", en: "Duplicates" },
  "nav.structuring": { fr: "Fractionnement", en: "Structuring" },
  "nav.sanctions": { fr: "Sanctions & PEP", en: "Sanctions & PEP" },
  "nav.decp_rbe": { fr: "DECP & RBE INPI", en: "DECP & RBE INPI" },
  "nav.anomalies": { fr: "Anomalies (ML)", en: "Anomalies (ML)" },
  "nav.rings": { fr: "Anneaux de fraude", en: "Fraud rings" },
  "nav.score": { fr: "Explorateur de score", en: "Score explorer" },
  "nav.findings": { fr: "Findings", en: "Findings" },
  "nav.vendors": { fr: "Fiche fournisseur 360°", en: "Vendor 360°" },
  "nav.exports": { fr: "Synthèse — export", en: "Summary export" },
  "nav.audit": { fr: "Piste d'audit", en: "Audit trail" },
  "nav.methodology": { fr: "Méthodologie", en: "Methodology" },
  "nav.governance": { fr: "Gouvernance", en: "Governance" },
};

type LocaleContextValue = {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: string) => string;
};

const LocaleContext = createContext<LocaleContextValue | null>(null);

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("fr");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === "fr" || stored === "en") setLocaleState(stored);
  }, []);

  const setLocale = (l: Locale) => {
    setLocaleState(l);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, l);
    }
  };

  const t = (key: string): string => {
    const entry = TRANSLATIONS[key];
    if (!entry) return key;
    return entry[locale] ?? entry.fr ?? key;
  };

  return (
    <LocaleContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </LocaleContext.Provider>
  );
}

export function useLocale(): LocaleContextValue {
  const ctx = useContext(LocaleContext);
  if (!ctx) {
    // Fallback en dev si le provider n'est pas encore monté
    return {
      locale: "fr",
      setLocale: () => {},
      t: (key: string) => TRANSLATIONS[key]?.fr ?? key,
    };
  }
  return ctx;
}
