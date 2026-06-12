"use client";

import { useState } from "react";
import { Play } from "lucide-react";
import { useLocale } from "@/components/locale-provider";
import { getDemoContent } from "./p2p-demo-content";
import { P2PInvestigationDemo } from "./P2PInvestigationDemo";

/**
 * Bouton de lancement de la démo guidée. Remplace les anciens CTA `Link
 * href="/sandbox"` (topbar, sidebar app-shell, sidebar accueil) : empêche la
 * navigation et monte l'overlay `P2PInvestigationDemo`. Conserve les classes
 * visuelles existantes (`topbar-demo` / `quick`).
 */
export function P2PDemoLauncher({
  variant,
}: {
  variant: "topbar" | "sidebar" | "home";
}) {
  const { locale } = useLocale();
  const content = getDemoContent(locale);
  const [open, setOpen] = useState(false);

  const label = content.launch[variant];
  const className = variant === "topbar" ? "topbar-demo" : "quick";

  return (
    <>
      <button
        type="button"
        className={className}
        onClick={() => setOpen(true)}
        data-testid={`demo-launch-${variant}`}
      >
        {variant === "topbar" ? <Play size={13} aria-hidden /> : <span aria-hidden>▶</span>}{" "}
        {label}
      </button>
      {open ? <P2PInvestigationDemo onClose={() => setOpen(false)} /> : null}
    </>
  );
}
