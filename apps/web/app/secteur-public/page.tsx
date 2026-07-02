import type { Metadata } from "next";
import Link from "next/link";
import { ForensicPage } from "@/components/forensic-page";

export const metadata: Metadata = {
  title: "Fraude fournisseur secteur public — hôpitaux, collectivités, EPA",
  description:
    "Détection de fraude fournisseur pour les entités publiques : fractionnement sous seuils de délégation, faux fournisseurs, favoritisme, conflits d'intérêts. Flux Chorus Pro, croisement DECP, piste d'audit signée opposable en CRC.",
  keywords: [
    "fraude fournisseur secteur public",
    "fractionnement marchés publics",
    "favoritisme",
    "Chorus Pro",
    "DECP",
    "contrôle interne comptable",
    "collectivités",
    "hôpitaux",
  ],
};

const USE_CASES = [
  {
    title: "Fractionnement sous seuils de délégation",
    detector: "under_thresholds",
    href: "/structuring",
    legal: "Art. L2122-1 CCP (seuils) · délit de favoritisme 432-14 CP",
    desc: "Douze factures calibrées juste sous le seuil qui déclencherait la double validation ou l'appel d'offres — densité anormale dans la fenêtre [seuil−ε, seuil[.",
  },
  {
    title: "Faux fournisseur / fournisseur fantôme",
    detector: "ghost_vendor",
    href: "/ghost-vendor",
    legal: "ISA 240 · contrôle hiérarchisé de la dépense",
    desc: "Fiche créée sans validation 4-eyes, première facture immédiate, sans engagement ni bon de commande, SIREN invérifiable au répertoire Sirene.",
  },
  {
    title: "Conflits d'intérêts agent ↔ prestataire",
    detector: "conflicts_of_interest",
    href: "/conflicts",
    legal: "Prise illégale d'intérêts 432-12 CP · déport HATVP",
    desc: "Croisement du référentiel RH avec les fournisseurs : IBAN de paie identique à un IBAN prestataire, adresse commune, agent qui valide ses propres factures.",
  },
  {
    title: "Concentration anormale de marchés",
    detector: "DECP",
    href: "/decp-rbe",
    legal: "Transparence de la commande publique (DECP)",
    desc: "Croisement open data DECP : prestataire concentrant les attributions d'un même acheteur, sans mise en concurrence traçable.",
  },
];

export default function SecteurPublicPage() {
  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Marché · secteur public</div>
          <h1 style={{ marginTop: 9 }}>
            La fraude fournisseur ne s&apos;arrête pas{" "}
            <span className="italic">au portail Chorus Pro</span>
          </h1>
          <p className="sub">
            Hôpitaux, collectivités, EPA : des flux AP massifs, des règles de délégation strictes —
            et aucun outil dédié à la détection de fraude fournisseur. Les mêmes détecteurs que le
            privé, plus les contrôles propres à la commande publique.
          </p>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-3" style={{ marginBottom: 16 }}>
        {[
          ["Flux structuré", "Chorus Pro / Factur-X", "La facturation électronique obligatoire produit exactement le format que le pipeline ingère."],
          ["Contrôles natifs", "Seuils & 4-eyes", "Les seuils de délégation du CCP sont des paramètres directs du détecteur de fractionnement."],
          ["Preuve opposable", "Ed25519 signé", "Piste d'audit vérifiable par la CRC ou le comptable public sans accès à la plateforme."],
        ].map(([k, v, d]) => (
          <div key={k} style={{ background: "var(--bg-2)", border: "1px solid var(--border)", padding: "14px 16px" }}>
            <div className="fx-eyebrow">{k}</div>
            <div className="fx-mono" style={{ fontSize: 14, color: "var(--fg)", marginTop: 6, fontWeight: 500 }}>
              {v}
            </div>
            <p style={{ fontSize: 12, lineHeight: 1.6, color: "var(--fg-2)", marginTop: 6 }}>{d}</p>
          </div>
        ))}
      </div>

      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <h2>Typologies couvertes · références pénales et CCP</h2>
          <span className="glyph">§</span>
        </div>
        <div className="fx-panel-body space-y-3">
          {USE_CASES.map((u) => (
            <div
              key={u.title}
              style={{
                background: "var(--bg-2)",
                border: "1px solid var(--border)",
                padding: "12px 14px",
              }}
            >
              <div className="flex items-start justify-between gap-3 flex-wrap">
                <div style={{ flex: 1, minWidth: 260 }}>
                  <div className="fx-mono" style={{ fontSize: 13, color: "var(--fg)", fontWeight: 500 }}>
                    {u.title}
                  </div>
                  <p style={{ fontSize: 12, lineHeight: 1.6, color: "var(--fg-2)", marginTop: 4 }}>
                    {u.desc}
                  </p>
                  <div className="fx-mono" style={{ fontSize: 10, color: "var(--muted)", marginTop: 6 }}>
                    {u.legal}
                  </div>
                </div>
                <Link href={u.href} className="fx-btn-ghost sm" style={{ whiteSpace: "nowrap" }}>
                  {u.detector} →
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <h2>Ingestion Chorus Pro — emplacement réservé</h2>
          <span className="glyph">↥</span>
        </div>
        <div className="fx-panel-body">
          <p style={{ fontSize: 14, lineHeight: 1.7, color: "var(--fg-2)", marginBottom: 12 }}>
            Le connecteur Chorus Pro (portail AIFE) a son emplacement réservé dans le registre :
            variables <code className="fx-mono">CHORUS_PRO_API_URL</code> /{" "}
            <code className="fx-mono">CHORUS_PRO_API_KEY</code>. En attendant, l&apos;export
            CSV/Excel de votre GFC (Hélios, CPage, MGDIS…) s&apos;importe directement — le mapping
            de colonnes assisté reconnaît les formats usuels.
          </p>
          <div className="flex flex-wrap gap-2">
            <Link href="/connecteurs" className="fx-btn-ghost sm">
              Registre des connecteurs →
            </Link>
            <Link href="/upload" className="fx-btn-ghost sm">
              Importer un export GFC →
            </Link>
            <Link href="/sandbox" className="fx-btn-ghost sm">
              Scénario fractionnement COSI →
            </Link>
          </div>
        </div>
      </div>

      <div
        style={{
          background: "var(--bg-2)",
          border: "1px solid var(--border)",
          borderLeft: "3px solid var(--risk)",
          padding: "16px 18px",
        }}
      >
        <div className="fx-eyebrow" style={{ marginBottom: 8 }}>
          Pour l&apos;ordonnateur et le comptable
        </div>
        <p style={{ fontSize: 15, lineHeight: 1.7, color: "var(--fg)", margin: 0 }}>
          Chaque finding est daté, signé et rattaché à sa règle de contrôle : le dossier remis à la
          chambre régionale des comptes prouve que le contrôle interne a fonctionné — ou documente
          précisément où il a été contourné.
        </p>
      </div>
    </ForensicPage>
  );
}
