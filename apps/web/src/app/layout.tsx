import type { Metadata } from "next";
import Link from "next/link";
import { BarChart3, Database, Fingerprint, Network } from "lucide-react";

import "./globals.css";

export const metadata: Metadata = {
  title: "P2P Fraud Detective FR",
  description: "Investigation graph for vendor and payment integrity.",
};

const navItems = [
  { href: "/dashboard", label: "Cockpit", icon: BarChart3 },
  { href: "/rings", label: "Anneaux de fraude", icon: Network },
];

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="fr">
      <body>
        <div className="p2p-shell">
          <aside className="p2p-sidebar">
            <Link href="/dashboard" className="flex items-center gap-3">
              <span className="grid h-10 w-10 place-items-center rounded-md bg-[#E5A93A] text-lg font-black text-[#0F1B33]">
                P
              </span>
              <span>
                <span className="block text-sm font-semibold uppercase tracking-[0.16em] text-[#E5A93A]">
                  P2P Fraud
                </span>
                <span className="block text-lg font-semibold">Detective FR</span>
              </span>
            </Link>

            <nav className="p2p-nav mt-10 space-y-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium text-[#E9EDF5] transition hover:bg-white/10"
                  >
                    <Icon aria-hidden className="h-4 w-4 text-[#E5A93A]" />
                    {item.label}
                  </Link>
                );
              })}
            </nav>

            <div className="p2p-sidebar-card mt-10 rounded-md border border-white/12 bg-white/6 p-4 text-sm text-[#CAD2E1]">
              <div className="flex items-center gap-2 text-[#E5A93A]">
                <Fingerprint aria-hidden className="h-4 w-4" />
                <span className="font-semibold">Audit-grade demo</span>
              </div>
              <p className="mt-2 leading-6">
                Données statiques, IBAN masqués, graphe prêt pour Vercel.
              </p>
            </div>

            <div className="p2p-sidebar-card mt-4 rounded-md border border-white/12 bg-white/6 p-4 text-sm text-[#CAD2E1]">
              <div className="flex items-center gap-2 text-[#E5A93A]">
                <Database aria-hidden className="h-4 w-4" />
                <span className="font-semibold">Source Python</span>
              </div>
              <p className="mt-2 leading-6">
                Le détecteur NetworkX reste la source de vérité.
              </p>
            </div>
          </aside>
          <main className="p2p-main">{children}</main>
        </div>
      </body>
    </html>
  );
}
