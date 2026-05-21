"use client";

import { useEffect, useState, type ReactNode } from "react";
import { useTheme } from "next-themes";

// Wraps a forensic-skinned inner page: re-scopes the forensic design system
// (dark by default, follows next-themes) inside the legacy AppShell <main>.
// Removed once every inner page has been migrated.
export function ForensicPage({ children }: { children: ReactNode }) {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const theme = mounted && resolvedTheme === "light" ? "light" : "dark";

  return (
    <div className="forensic" data-theme={theme} data-grain="off">
      <div className="fx-page">{children}</div>
    </div>
  );
}
