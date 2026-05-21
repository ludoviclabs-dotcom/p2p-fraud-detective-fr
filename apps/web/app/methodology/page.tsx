import type { Metadata } from "next";
import { ForensicPage } from "@/components/forensic-page";

export const metadata: Metadata = {
  title: "Méthodologie — P2P Fraud Detective FR",
};

export default function MethodologyPage() {
  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Gouvernance</div>
          <h1 style={{ marginTop: 9 }}>
            Métho<span className="italic">dologie</span>
          </h1>
          <p className="sub">
            Documentation transparente de l&apos;approche analytique, des seuils
            de détection, des métriques de validation et des limites connues.
            Conforme aux exigences de transparence{" "}
            <strong style={{ color: "var(--fg)" }}>AI Act art. 50</strong>.
          </p>
        </div>
      </div>

      {/* Objectifs et périmètre */}
      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <div>
            <h2>Objectifs et périmètre</h2>
          </div>
          <span className="glyph">◇</span>
        </div>
        <div className="fx-panel-body">
          <p style={{ fontSize: 14, lineHeight: 1.65, color: "var(--fg-2)", marginBottom: 12 }}>
            <strong style={{ color: "var(--fg)" }}>P2P Fraud Detective FR</strong>{" "}
            est un démonstrateur d&apos;audit du cycle Procure-to-Pay orienté
            détection de fraude : sous-seuils, doublons, BEC (Business Email
            Compromise), sanctions, anneaux IBAN. Aligné sur les méthodologies
            AML/CFT et les contrôles attendus en audit P2P public :{" "}
            <strong style={{ color: "var(--fg)" }}>ISA 240</strong>,{" "}
            <strong style={{ color: "var(--fg)" }}>AS 2401</strong>,{" "}
            <strong style={{ color: "var(--fg)" }}>Sapin 2</strong>,{" "}
            <strong style={{ color: "var(--fg)" }}>LCB-FT</strong>,{" "}
            <strong style={{ color: "var(--fg)" }}>DORA art. 28</strong>,{" "}
            <strong style={{ color: "var(--fg)" }}>AMLD6</strong>.
          </p>
          <p style={{ fontSize: 14, lineHeight: 1.65, color: "var(--fg-2)" }}>
            Pertinent pour les ETI 500 M€-2 Md€, cabinets d&apos;audit
            mid-tier, fonctions publiques et organismes de contrôle (DGFiP,
            Tracfin, IGF, Cour des comptes, CRC régionales).
          </p>
        </div>
      </div>

      {/* Sources de données publiques */}
      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <div>
            <h2>Sources de données publiques</h2>
          </div>
          <span className="glyph">▦</span>
        </div>
        <div className="fx-table-wrap">
          <table className="fx-table">
            <thead>
              <tr>
                <th>Source</th>
                <th>Endpoint</th>
                <th>Licence</th>
                <th>Fréquence</th>
              </tr>
            </thead>
            <tbody>
              {[
                ["INSEE Sirene v3", "api.insee.fr/entreprises/sirene/V3", "ODbL 1.0", "Quotidienne"],
                ["DECP v3", "data.economie.gouv.fr/decp_augmente", "ODbL 1.0", "Quotidienne"],
                ["Pappers (RBE)", "api.pappers.fr/v2/entreprise", "Commercial", "Temps réel"],
                ["OpenSanctions Yente", "api.opensanctions.org/match/sanctions", "CC-BY 4.0", "Hebdomadaire"],
                ["UE consolidée", "via Yente", "EU Open Data", "Quotidienne"],
                ["OFAC SDN", "via Yente", "US Public Domain", "Hebdomadaire"],
                ["Trésor FR (gels)", "tresor.economie.gouv.fr", "Légifrance", "Quotidienne"],
              ].map(([src, ep, lic, freq]) => (
                <tr key={src}>
                  <td className="key">{src}</td>
                  <td>{ep}</td>
                  <td>{lic}</td>
                  <td>{freq}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Seuils statistiques */}
      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <div>
            <h2>Seuils statistiques</h2>
          </div>
          <span className="glyph">Σ</span>
        </div>
        <div className="fx-table-wrap">
          <table className="fx-table">
            <thead>
              <tr>
                <th>Détecteur</th>
                <th>Seuil</th>
                <th>Référence</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="key">Benford</td>
                <td>KS p &lt; 0.05 · min 1 000 factures</td>
                <td style={{ color: "var(--muted)" }}>ISA 240</td>
              </tr>
              <tr>
                <td className="key">Doublons fuzzy</td>
                <td>RapidFuzz WRatio ≥ 92 · fenêtre 30 j</td>
                <td style={{ color: "var(--muted)" }}>ACPR LCB-FT</td>
              </tr>
              <tr>
                <td className="key">Sous-seuils COSI</td>
                <td>900-999 €, cumul mensuel &gt; 2 000 € / 10 000 €</td>
                <td style={{ color: "var(--muted)" }}>D. 561-31-1 / R. 561-31-2 CMF</td>
              </tr>
              <tr>
                <td className="key">Isolation Forest</td>
                <td>contamination 0.05 · n_estimators 200</td>
                <td style={{ color: "var(--muted)" }}>scikit-learn 1.5</td>
              </tr>
              <tr>
                <td className="key">Anneaux IBAN</td>
                <td>Cluster ≥ 3 vendors partageant un IBAN</td>
                <td style={{ color: "var(--muted)" }}>NetworkX 3.3</td>
              </tr>
              <tr>
                <td className="key">Sanctions matching</td>
                <td>RapidFuzz WRatio ≥ 90</td>
                <td style={{ color: "var(--muted)" }}>OpenSanctions Yente</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Métriques F1 */}
      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <div>
            <h2>Métriques F1 (validation sur ground truth)</h2>
          </div>
          <span className="glyph">★</span>
        </div>
        <div className="fx-table-wrap">
          <table className="fx-table">
            <thead>
              <tr>
                <th>Détecteur</th>
                <th className="num">F1</th>
                <th className="num">Précision</th>
                <th className="num">Rappel</th>
                <th>Dataset</th>
              </tr>
            </thead>
            <tbody>
              {[
                ["BEC (master_data)", "0.91", "0.94", "0.88", "Synthetic + 6 cas confirmés"],
                ["Doublons fuzzy", "0.87", "0.92", "0.83", "AMLSim 50k"],
                ["Sous-seuils", "0.84", "0.89", "0.80", "Synthetic structuring"],
                ["Anneaux IBAN", "1.0", "1.0", "1.0", "Synthetic anneau_fraude"],
                ["Sanctions", "0.95", "0.97", "0.93", "Snapshot UE 2024-2026"],
              ].map(([d, f1, p, r, ds]) => (
                <tr key={d}>
                  <td className="key">{d}</td>
                  <td className="num" style={{ color: "var(--verified)" }}>{f1}</td>
                  <td className="num">{p}</td>
                  <td className="num">{r}</td>
                  <td style={{ color: "var(--muted)" }}>{ds}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="fx-panel-body" style={{ borderTop: "1px solid var(--border)" }}>
          <p className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>
            Voir{" "}
            <code
              style={{
                background: "var(--panel-2)",
                border: "1px solid var(--border)",
                padding: "1px 5px",
              }}
            >
              docs/benchmark_results.json
            </code>{" "}
            pour les métriques détaillées par configuration de seuil.
          </p>
        </div>
      </div>

      {/* Limites connues */}
      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <div>
            <h2>Limites connues</h2>
          </div>
          <span className="glyph">⚠</span>
        </div>
        <div className="fx-panel-body">
          <div className="space-y-3">
            {[
              "Loi de Benford : non fiable sous 1 000 factures (puissance statistique insuffisante)",
              "Liste PEP open-source : couverture élus locaux français estimée 60-70 %",
              "DECP : seuils minimaux légaux (25 k€ TTC marchés, 90 k€ DSP) — petits marchés non couverts",
              "Pappers free tier : ~ 100 requêtes/jour — pilote ETI avec 10 000 fournisseurs nécessite plan payant ou self-host RNE",
              "Streamlit Cloud (legacy v0.5) : limité à une session — pour multi-user persistant, utiliser FastAPI + PostgreSQL Aiven",
              "Pas de connecteur ERP natif (SAP/Sage/Cegid) — extraction CSV manuelle requise",
            ].map((item, i) => (
              <div key={i} className="fx-step">
                <div className="n" style={{ color: "var(--warn)", borderColor: "var(--warn)" }}>
                  △
                </div>
                <div>
                  <div className="d" style={{ marginTop: 0 }}>{item}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Architecture */}
      <div className="fx-panel">
        <div className="fx-panel-head">
          <div>
            <h2>Architecture (v2 Next.js + FastAPI)</h2>
          </div>
          <span className="glyph">□</span>
        </div>
        <div className="fx-panel-body">
          <pre
            style={{
              overflowX: "auto",
              background: "var(--bg-2)",
              border: "1px solid var(--border)",
              padding: "16px 20px",
              fontFamily: "var(--font-mono)",
              fontSize: 11,
              color: "var(--fg-2)",
              lineHeight: 1.65,
            }}
          >
            {`                  ┌────────────────────────────────────┐
                  │  VISITEUR (recruteur / pilote ETI) │
                  └──────────────────┬─────────────────┘
                                     │ HTTPS
                                     ▼
              ┌──────────────────────────────────────┐
              │  Vercel free (Next.js 15)            │
              │  ├─ App Router : 21 routes           │
              │  ├─ shadcn-style UI + Tailwind v4    │
              │  ├─ Recharts + sigma.js + visx       │
              │  ├─ TanStack Query/Table             │
              │  ├─ /api/auth/* (OIDC proxy)         │
              │  └─ /api/uploads (multipart proxy)   │
              └──────────────┬───────────────────────┘
                             │ REST + SSE
                             ▼
            ┌──────────────────────────────────────┐
            │ HF Spaces (FastAPI Docker free 16GB) │
            │ ├─ src/p2p_fraud/** (Python pur)     │
            │ ├─ 26 endpoints /api/v1/*            │
            │ ├─ NetworkX + Pandas + scikit-learn  │
            │ ├─ Audit log SHA-256 + Ed25519       │
            │ ├─ OIDC discovery + JWKS             │
            │ └─ weasyprint PDF                    │
            └──────────┬───────────────────────────┘
                       │ SQLAlchemy
                       ▼
              ┌────────────────────────┐
              │ Neon free (PG 16,      │
              │  0.5 GB, scale-to-zero)│
              └────────────────────────┘`}
          </pre>
        </div>
      </div>
    </ForensicPage>
  );
}
