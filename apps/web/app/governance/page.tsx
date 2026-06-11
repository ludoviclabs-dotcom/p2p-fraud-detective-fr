import type { Metadata } from "next";
import Link from "next/link";
import { ForensicPage } from "@/components/forensic-page";
import { GovernanceLivePanels } from "@/components/governance-live-panels";

export const metadata: Metadata = {
  title: "Gouvernance — P2P Fraud Detective FR",
};

export default function GovernancePage() {
  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Gouvernance</div>
          <h1 style={{ marginTop: 9 }}>
            Gouver<span className="italic">nance</span>
          </h1>
          <p className="sub">
            AI Act · RGPD · RGAA 4.1 · RBAC · AMLD6 · CSRD · Sapin 2 · ANSSI
            RGS B1/B2
          </p>
        </div>
      </div>

      <GovernanceLivePanels />

      {/* Workbench — full width */}
      <div className="fx-card-accent" style={{ marginBottom: 16 }}>
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: 12,
            marginBottom: 12,
          }}
        >
          <span
            className="fx-mono"
            style={{ fontSize: 16, color: "var(--risk)", flexShrink: 0 }}
          >
            ⚠
          </span>
          <div>
            <div className="fx-eyebrow">Démonstrateur</div>
            <div
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 20,
                color: "var(--fg)",
                marginTop: 6,
                lineHeight: 1.1,
              }}
            >
              P2P Fraud Detection Workbench
            </div>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <p style={{ fontSize: 14, lineHeight: 1.65, color: "var(--fg-2)" }}>
            <strong style={{ color: "var(--fg)" }}>Statut</strong> :
            démonstrateur professionnel fondé sur des scénarios et datasets
            synthétiques, avec fallback local si Hugging Face est indisponible.
          </p>
          <p style={{ fontSize: 14, lineHeight: 1.65, color: "var(--fg-2)" }}>
            <strong style={{ color: "var(--fg)" }}>Limites</strong> : pas de
            décision bancaire réelle, pas de certification conformité, pas de
            fingerprinting réel, pas de dark web scraping. La décision finale
            reste humaine.
          </p>
        </div>
      </div>

      {/* Grid of governance cards */}
      <div className="grid gap-4 md:grid-cols-2" style={{ marginBottom: 16 }}>
        {/* AI Act */}
        <div className="fx-panel">
          <div className="fx-panel-head">
            <div>
              <h2>AI Act (UE 2024/1689)</h2>
            </div>
            <span className="glyph">§</span>
          </div>
          <div className="fx-panel-body space-y-3">
            <p style={{ fontSize: 14, lineHeight: 1.65, color: "var(--fg-2)" }}>
              <strong style={{ color: "var(--fg)" }}>Classification</strong> :
              système d&apos;IA à risque limité (art. 50) — transparence
              obligatoire, pas de risque élevé (annexe III).
            </p>
            <p style={{ fontSize: 14, lineHeight: 1.65, color: "var(--fg-2)" }}>
              <strong style={{ color: "var(--fg)" }}>Conformité</strong> : page
              Méthodologie publique avec sources, seuils, métriques F1, limites.
              Pas de scoring opaque. Audit log immutable de toutes les décisions.
            </p>
          </div>
        </div>

        {/* RGPD */}
        <div className="fx-panel">
          <div className="fx-panel-head">
            <div>
              <h2>RGPD (UE 2016/679)</h2>
            </div>
            <span className="glyph">□</span>
          </div>
          <div className="fx-panel-body space-y-3">
            <p style={{ fontSize: 14, lineHeight: 1.65, color: "var(--fg-2)" }}>
              <strong style={{ color: "var(--fg)" }}>Données traitées</strong> :
              100 % synthétiques en démo publique. En pilote ETI, données
              fournisseurs uniquement (vendor_name, SIREN, IBAN, montants) — pas
              de PII salariés.
            </p>
            <p style={{ fontSize: 14, lineHeight: 1.65, color: "var(--fg-2)" }}>
              <strong style={{ color: "var(--fg)" }}>
                Droit à l&apos;effacement (art. 17)
              </strong>{" "}
              : bouton &quot;Purger session&quot; + endpoint{" "}
              <code
                className="fx-mono"
                style={{
                  background: "var(--panel-2)",
                  border: "1px solid var(--border)",
                  padding: "1px 5px",
                  fontSize: 11,
                }}
              >
                purge_user_data()
              </code>
              .
            </p>
            <p style={{ fontSize: 14, lineHeight: 1.65, color: "var(--fg-2)" }}>
              <strong style={{ color: "var(--fg)" }}>IBAN au repos</strong> :
              chiffré Fernet (AES-128-CBC + HMAC-SHA256), clé{" "}
              <code
                className="fx-mono"
                style={{
                  background: "var(--panel-2)",
                  border: "1px solid var(--border)",
                  padding: "1px 5px",
                  fontSize: 11,
                }}
              >
                P2P_FRAUD_DATA_KEY
              </code>
              .
            </p>
          </div>
        </div>

        {/* RBAC */}
        <div className="fx-panel">
          <div className="fx-panel-head">
            <div>
              <h2>RBAC — 4 rôles</h2>
            </div>
            <span className="glyph">◇</span>
          </div>
          <div className="fx-table-wrap">
            <table className="fx-table">
              <thead>
                <tr>
                  <th>Rôle</th>
                  <th>Lecture</th>
                  <th>Triage</th>
                  <th>Clôture</th>
                  <th>Purge</th>
                </tr>
              </thead>
              <tbody>
                {[
                  ["viewer", "✓", "—", "—", "—"],
                  ["analyst", "✓", "✓", "—", "—"],
                  ["manager", "✓", "✓", "✓", "—"],
                  ["admin", "✓", "✓", "✓", "✓"],
                ].map(([r, ...rest]) => (
                  <tr key={r}>
                    <td className="key">{r}</td>
                    {rest.map((c, i) => (
                      <td
                        key={i}
                        style={{
                          color: c === "✓" ? "var(--verified)" : "var(--dim)",
                        }}
                      >
                        {c}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="fx-panel-body" style={{ borderTop: "1px solid var(--border)" }}>
            <p className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>
              PBKDF2-SHA256 200 000 itérations · sels uniques par user.
            </p>
          </div>
        </div>

        {/* AMLD6 */}
        <div className="fx-panel">
          <div className="fx-panel-head">
            <div>
              <h2>AMLD6 (UE 2018/1673)</h2>
            </div>
            <span className="glyph">▣</span>
          </div>
          <div className="fx-panel-body space-y-3">
            <p style={{ fontSize: 14, lineHeight: 1.65, color: "var(--fg-2)" }}>
              <strong style={{ color: "var(--fg)" }}>
                Bénéficiaires effectifs ≥ 25 %
              </strong>{" "}
              : page{" "}
              <Link className="fx-link" href="/decp-rbe">
                DECP &amp; RBE INPI
              </Link>{" "}
              via Pappers.
            </p>
            <p style={{ fontSize: 14, lineHeight: 1.65, color: "var(--fg-2)" }}>
              <strong style={{ color: "var(--fg)" }}>PEP screening</strong> :
              OpenSanctions Yente CC-BY 4.0, page{" "}
              <Link className="fx-link" href="/sanctions">
                Sanctions &amp; PEP
              </Link>
              .
            </p>
            <p style={{ fontSize: 14, lineHeight: 1.65, color: "var(--fg-2)" }}>
              <strong style={{ color: "var(--fg)" }}>
                Tracfin déclaration de soupçon
              </strong>{" "}
              : bouton &quot;Générer brouillon DS&quot; dans la fiche fournisseur
              (annoté &quot;démonstration pédagogique&quot;).
            </p>
          </div>
        </div>

        {/* Sapin 2 */}
        <div className="fx-panel">
          <div className="fx-panel-head">
            <div>
              <h2>Sapin 2 — art. 17</h2>
            </div>
            <span className="glyph">✓</span>
          </div>
          <div className="fx-panel-body space-y-3">
            <p style={{ fontSize: 14, lineHeight: 1.65, color: "var(--fg-2)" }}>
              <strong style={{ color: "var(--fg)" }}>Due diligence tiers</strong>{" "}
              : croisement automatique SIREN/SIRET avec DECP + RBE. Détection
              structures opaques, nationalités à haut risque.
            </p>
            <p style={{ fontSize: 14, lineHeight: 1.65, color: "var(--fg-2)" }}>
              <strong style={{ color: "var(--fg)" }}>Cartographie risques</strong>{" "}
              : scoring 0-100 par fournisseur, waterfall des contributions sur{" "}
              <Link className="fx-link" href="/score">
                /score
              </Link>
              .
            </p>
            <p style={{ fontSize: 14, lineHeight: 1.65, color: "var(--fg-2)" }}>
              <strong style={{ color: "var(--fg)" }}>Plan de prévention</strong>{" "}
              : audit trail Ed25519 recevable comme preuve de diligence (Cour des
              comptes 2024).
            </p>
          </div>
        </div>

        {/* ANSSI */}
        <div className="fx-panel">
          <div className="fx-panel-head">
            <div>
              <h2>ANSSI RGS B1/B2 — Ed25519</h2>
            </div>
            <span className="glyph">§</span>
          </div>
          <div className="fx-panel-body space-y-3">
            <p style={{ fontSize: 14, lineHeight: 1.65, color: "var(--fg-2)" }}>
              <strong style={{ color: "var(--fg)" }}>
                Signatures cryptographiques
              </strong>{" "}
              : audit log signé Ed25519 (RFC 8032) — non-répudiation, intégrité,
              vérifiabilité externe.
            </p>
            <p style={{ fontSize: 14, lineHeight: 1.65, color: "var(--fg-2)" }}>
              <strong style={{ color: "var(--fg)" }}>
                Clé publique exposée
              </strong>{" "}
              :{" "}
              <code
                className="fx-mono"
                style={{
                  background: "var(--panel-2)",
                  border: "1px solid var(--border)",
                  padding: "1px 5px",
                  fontSize: 11,
                }}
              >
                GET /security/public-key
              </code>{" "}
              — vérification indépendante par CAC, ACPR, magistrat.
            </p>
            <p style={{ fontSize: 14, lineHeight: 1.65, color: "var(--fg-2)" }}>
              <strong style={{ color: "var(--fg)" }}>
                Conformité eIDAS 2024/1183
              </strong>{" "}
              : signatures électroniques avancées.
            </p>
          </div>
        </div>
      </div>

      {/* Documents de conformité */}
      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <div>
            <h2>Documents de conformité</h2>
          </div>
          <span className="glyph">▦</span>
        </div>
        <div className="fx-table-wrap">
          <table className="fx-table">
            <thead>
              <tr>
                <th>Document</th>
                <th>Référence</th>
                <th>Lien</th>
              </tr>
            </thead>
            <tbody>
              {[
                [
                  "DPIA (Analyse d'impact RGPD)",
                  "Art. 35 RGPD",
                  "docs/compliance/dpia.md",
                ],
                [
                  "Registre AI Act",
                  "Art. 50 UE 2024/1689",
                  "docs/compliance/ai_act_register.md",
                ],
                [
                  "Registre RGPD art. 30",
                  "RGPD art. 30",
                  "docs/compliance/rgpd_register.md",
                ],
                [
                  "AMLD6 mapping",
                  "UE 2018/1673",
                  "docs/compliance/amld6_mapping.md",
                ],
                [
                  "Doctrine signatures Ed25519",
                  "P5-5",
                  "docs/conformite_signatures.md",
                ],
                [
                  "Sources de données",
                  "P5-1",
                  "docs/sources_de_donnees.md",
                ],
              ].map(([doc, ref, link]) => (
                <tr key={doc}>
                  <td className="key">{doc}</td>
                  <td style={{ color: "var(--muted)" }}>{ref}</td>
                  <td>
                    <a
                      className="fx-link"
                      href={`https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/blob/main/${link}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {link} ↗
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Accessibilité */}
      <div className="fx-panel">
        <div className="fx-panel-head">
          <div>
            <h2>Accessibilité RGAA 4.1 (partielle)</h2>
          </div>
          <span className="glyph">◫</span>
        </div>
        <div className="fx-panel-body space-y-3">
          <p style={{ fontSize: 14, lineHeight: 1.65, color: "var(--fg-2)" }}>
            <strong style={{ color: "var(--fg)" }}>Contrastes</strong> : navy{" "}
            <code
              className="fx-mono"
              style={{
                background: "var(--panel-2)",
                border: "1px solid var(--border)",
                padding: "1px 5px",
                fontSize: 11,
              }}
            >
              #1f3a6e
            </code>{" "}
            sur blanc = 8.59:1{" "}
            <span style={{ color: "var(--verified)" }}>✓</span>, gold{" "}
            <code
              className="fx-mono"
              style={{
                background: "var(--panel-2)",
                border: "1px solid var(--border)",
                padding: "1px 5px",
                fontSize: 11,
              }}
            >
              #e5a93a
            </code>{" "}
            sur navy = 7.21:1{" "}
            <span style={{ color: "var(--verified)" }}>✓</span> (cible WCAG AA
            ≥ 4.5:1).
          </p>
          <p style={{ fontSize: 14, lineHeight: 1.65, color: "var(--fg-2)" }}>
            <strong style={{ color: "var(--fg)" }}>
              Annotations graphiques
            </strong>{" "}
            : sigma.js / Recharts doublés d&apos;une vue tabulaire HTML pour
            lecteurs d&apos;écran.
          </p>
          <p style={{ fontSize: 14, lineHeight: 1.65, color: "var(--fg-2)" }}>
            <strong style={{ color: "var(--fg)" }}>Limites</strong> : composants
            TanStack Table partiellement ARIA, à compléter pour marchés publics
            requérant certification RGAA complète.
          </p>
        </div>
      </div>
    </ForensicPage>
  );
}
