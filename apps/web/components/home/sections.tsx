"use client";

import { useEffect, useState, type ReactNode } from "react";
import Link from "next/link";
import { HASH_CHAIN, REFERENTIALS, TICKER_ITEMS } from "./data";

export function SectionHead({
  num,
  kicker,
  title,
}: {
  num: string;
  kicker: string;
  title: ReactNode;
}) {
  return (
    <div className="section-head">
      <div>
        <div className="section-num">
          § {num} · {kicker}
        </div>
      </div>
      <div>
        <h2>{title}</h2>
      </div>
    </div>
  );
}

export function Ticker() {
  // Duplicate items so the marquee loops seamlessly.
  const items = [...TICKER_ITEMS, ...TICKER_ITEMS];
  return (
    <div className="ticker" aria-hidden>
      <div className="ticker-track">
        {items.map((it, i) => (
          <div className="ticker-item" key={i}>
            <span className="time">{it.t}</span>
            <span className={`sev ${it.sev}`}>
              {it.sev === "crit" ? "CRIT" : it.sev === "high" ? "HIGH" : "MED"}
            </span>
            <span>{it.txt}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function CTA({ href, label, hint }: { href: string; label: string; hint: string }) {
  return (
    <div
      style={{
        marginTop: 32,
        borderTop: "1px solid var(--border)",
        paddingTop: 22,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        flexWrap: "wrap",
        gap: 16,
      }}
    >
      <div
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: 11,
          color: "var(--muted)",
          letterSpacing: "0.08em",
          textTransform: "uppercase",
        }}
      >
        {hint}
      </div>
      <Link href={href} className="btn-ghost" style={{ padding: "11px 18px" }}>
        {label} <span>↗</span>
      </Link>
    </div>
  );
}

export function Referentials() {
  return (
    <section className="refs container" id="refs">
      <SectionHead
        num="04"
        kicker="Cartographie référentielle"
        title={
          <>
            Chaque finding pointe une <span className="italic">norme</span>.
          </>
        }
      />
      <div className="ref-list">
        {REFERENTIALS.map((r) => (
          <div className="ref-row" key={r.num}>
            <div className="ref-num">[{r.num}]</div>
            <div className="ref-name">{r.name}</div>
            <div className="ref-desc">{r.desc}</div>
            <div className="ref-tag">{r.tag}</div>
          </div>
        ))}
      </div>

      <CTA
        href="/methodology"
        hint="Mapping complet ISA 240 · Sapin 2 · DORA · LCB-FT · NIS2 · VoP · FNC-RF"
        label="Lire la méthodologie"
      />
    </section>
  );
}

export function Trust() {
  return (
    <section className="trust container" id="trust">
      <SectionHead
        num="05"
        kicker="Preuve & transparence"
        title={
          <>
            Sans <span className="italic">données client</span>. Avec preuve.
          </>
        }
      />
      <div className="trust-grid">
        <div className="trust-card">
          <div className="tk">Démo</div>
          <div className="tv">Données 100% synthétiques</div>
          <div className="td">
            Aucun fichier client n&apos;a transité. Le dataset 50k factures est généré par le
            module synthétique du repo.
          </div>
        </div>
        <div className="trust-card">
          <div className="tk">Sources</div>
          <div className="tv">Sirene · DECP · OpenSanctions</div>
          <div className="td">
            Référentiels publics français et internationaux. Cross-check API v3 avec timestamp
            signé.
          </div>
        </div>
        <div className="trust-card">
          <div className="tk">Audit log</div>
          <div className="tv">Ed25519 · hash chaîné</div>
          <div className="td">
            Chaque finding produit une entrée immuable. Vérifiable par un tiers via la clé
            publique.
          </div>
        </div>
        <div className="trust-card">
          <div className="tk">Souveraineté</div>
          <div className="tv">On-premise · RGPD</div>
          <div className="td">
            Aucune donnée fournisseur ne sort de votre SI. Pipeline Python autonome, dashboards
            Power BI.
          </div>
        </div>
      </div>
    </section>
  );
}

export function HashBand() {
  const chain = [...HASH_CHAIN, ...HASH_CHAIN];
  return (
    <div className="hash-band" aria-hidden>
      <div className="hash-track">
        {chain.map((h, i) => (
          <span className="item" key={i}>
            <span style={{ color: "var(--dim)" }}>blk·{String(8412 - i).padStart(5, "0")} </span>
            <span className="h">{h}</span>
            <span style={{ color: "var(--dim)" }}> · ed25519 ✓</span>
          </span>
        ))}
      </div>
    </div>
  );
}

export function Footer() {
  // Render the build date client-side only to avoid an SSR/hydration mismatch.
  const [buildDate, setBuildDate] = useState("");
  useEffect(() => {
    setBuildDate(new Date().toLocaleDateString("fr-FR"));
  }, []);

  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-grid">
          <div className="footer-brand">
            <div className="display">
              P2P Fraud
              <br />
              Detective
              <span style={{ color: "var(--risk)" }}>·</span>FR
            </div>
            <div className="desc">
              Vendor &amp; Payment Integrity, FR-native. Détection P2P, monitoring master data,
              piste d&apos;audit signée — pour ETI, cabinets d&apos;audit, secteur public.
            </div>
          </div>
          <div className="footer-col">
            <h4>Produit</h4>
            <a href="#hero">Console</a>
            <a href="#pipeline">Pipeline</a>
            <a href="#acte-i">Dossier</a>
            <a href="#refs">Référentiels</a>
          </div>
          <div className="footer-col">
            <h4>Preuve</h4>
            <a href="#trust">Trust center</a>
            <Link href="/methodology">Méthodologie</Link>
            <Link href="/cac-partner">CAC Partner</Link>
            <Link href="/fnc-rf-fraude-iban">FNC-RF & VoP</Link>
          </div>
          <div className="footer-col">
            <h4>Marchés</h4>
            <Link href="/secteur-public">Secteur public</Link>
            <Link href="/connecteurs">Connecteurs</Link>
            <Link href="/sandbox">Démo 60 s</Link>
            <Link href="/risk-docs">Changelog v2</Link>
          </div>
          <div className="footer-col">
            <h4>Code</h4>
            <a
              href="https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr"
              target="_blank"
              rel="noreferrer"
            >
              GitHub · MIT
            </a>
            <Link href="/risk-docs">Quickstart</Link>
            <Link href="/risk-docs">Docs · API</Link>
            <Link href="/exports">Power BI · .pbix</Link>
          </div>
        </div>
        <div className="footer-bottom">
          <div>© 2026 · P2P Fraud Detective FR · Licence MIT</div>
          <div>v2.1 · build 8412{buildDate ? ` · ${buildDate}` : ""}</div>
        </div>
      </div>
    </footer>
  );
}
