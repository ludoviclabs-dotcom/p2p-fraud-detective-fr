import type { Metadata } from "next";
import Link from "next/link";
import { ForensicPage } from "@/components/forensic-page";

export const metadata: Metadata = {
  title: "CAC Partner — preuve signée Ed25519 pour le dossier de révision",
  description:
    "Pour les commissaires aux comptes et cabinets d'audit : détecteurs ISA 240 / NEP 240 sur le cycle fournisseurs, export du dossier de révision, piste d'audit Ed25519 vérifiable par un tiers sans accès à la plateforme.",
  keywords: [
    "commissaire aux comptes",
    "NEP 240",
    "ISA 240",
    "dossier de révision",
    "audit cycle fournisseurs",
    "fraude au président",
    "piste d'audit signée",
  ],
};

const WORKFLOW = [
  ["1", "Importer", "Balance fournisseurs + journal des achats du dossier (CSV/Excel, mapping assisté). Aucune donnée ne quitte votre poste en mode on-premise."],
  ["2", "Détecter", "10 détecteurs en cascade — master data, doublons, fractionnement, sanctions, anneaux, ghost vendor, conflits d'intérêts, Benford."],
  ["3", "Documenter", "Chaque finding porte sa règle, sa norme (NEP/ISA 240) et son évidence — prêt à annexer au dossier de révision."],
  ["4", "Signer", "Export du dossier signé Ed25519 : le co-CAC, le régulateur ou le successeur vérifie l'intégrité avec la clé publique, sans accès à l'outil."],
] as const;

export default function CacPartnerPage() {
  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Canal · cabinets d&apos;audit & CAC</div>
          <h1 style={{ marginTop: 9 }}>
            La diligence fraude fournisseur,{" "}
            <span className="italic">avec preuve opposable</span>
          </h1>
          <p className="sub">
            NEP 240 / ISA 240 demandent des procédures d&apos;audit répondant au risque de fraude.
            P2P Fraud Detective les exécute sur le cycle fournisseurs et produit une preuve
            qu&apos;un tiers peut vérifier — sans compte, sans accès à la plateforme.
          </p>
        </div>
      </div>

      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <h2>L&apos;atout structurel : la preuve détachée de l&apos;outil</h2>
          <span className="glyph">✓</span>
        </div>
        <div className="fx-panel-body">
          <p style={{ fontSize: 14, lineHeight: 1.7, color: "var(--fg-2)", marginBottom: 12 }}>
            Les plateformes de vérification bancaire protègent le paiement — mais leur preuve vit
            dans leur SaaS. Ici, chaque finding rejoint une piste d&apos;audit{" "}
            <strong style={{ color: "var(--fg)" }}>append-only, hash-chaînée et signée Ed25519</strong>.
            L&apos;export contient les entrées, la chaîne de hachage et la clé publique :{" "}
            <strong style={{ color: "var(--fg)" }}>
              le co-commissaire, le H3C/PCAOB ou le CAC successeur vérifie l&apos;intégrité du
              dossier hors ligne
            </strong>
            , des années plus tard, même si la plateforme a disparu.
          </p>
          <p style={{ fontSize: 14, lineHeight: 1.7, color: "var(--fg-2)" }}>
            C&apos;est la différence entre « la plateforme affirme » et « le dossier prouve » — et
            c&apos;est ce qui rend l&apos;outil utilisable comme élément probant d&apos;audit, pas
            seulement comme filtre opérationnel.
          </p>
        </div>
      </div>

      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <h2>Parcours mission — de l&apos;import au dossier signé</h2>
          <span className="glyph">→</span>
        </div>
        <div className="fx-panel-body">
          <div className="space-y-3">
            {WORKFLOW.map(([n, t, d]) => (
              <div key={n} className="fx-step">
                <div className="n">{n}</div>
                <div>
                  <div className="t">{t}</div>
                  <div className="d">{d}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <h2>Cartographie NEP / ISA par détecteur</h2>
          <span className="glyph">§</span>
        </div>
        <div className="fx-table-wrap">
          <table className="fx-table">
            <thead>
              <tr>
                <th>Assertion / risque</th>
                <th>Détecteur</th>
                <th>Norme</th>
              </tr>
            </thead>
            <tbody>
              {[
                ["Contournement des contrôles par la direction", "master_data_changes (4-eyes)", "ISA 240 §31-33"],
                ["Fournisseurs fictifs / réalité des tiers", "ghost_vendor + cross-check Sirene", "ISA 240 · ISA 500"],
                ["Conflits d'intérêts non déclarés", "conflicts_of_interest (RH × vendors)", "ISA 240 · ISA 550 parties liées"],
                ["Exhaustivité / doubles paiements", "duplicates (fuzzy + IBAN)", "ISA 240"],
                ["Scoping des populations à tester", "benford (F1D/F2D, MAD Nigrini)", "ISA 240 · JET testing"],
                ["Contournement des seuils d'approbation", "under_thresholds", "ISA 240 · ISA 330"],
              ].map(([risk, det, norm]) => (
                <tr key={det}>
                  <td>{risk}</td>
                  <td className="key">{det}</td>
                  <td style={{ color: "var(--muted)" }}>{norm}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div
        style={{
          background: "var(--bg-2)",
          border: "1px solid var(--border)",
          borderLeft: "3px solid var(--risk)",
          padding: "16px 18px",
          marginBottom: 16,
        }}
      >
        <div className="fx-eyebrow" style={{ marginBottom: 8 }}>
          Format cabinet
        </div>
        <p style={{ fontSize: 15, lineHeight: 1.7, color: "var(--fg)", margin: 0 }}>
          Multi-dossiers par exercice, données cloisonnées par mission, exécution on-premise ou sur
          le poste de l&apos;auditeur — le référentiel client ne transite par aucun cloud tiers.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        <Link href="/audit" className="fx-btn-ghost sm">
          Voir la piste d&apos;audit signée →
        </Link>
        <Link href="/exports" className="fx-btn-ghost sm">
          Exports dossier de révision →
        </Link>
        <Link href="/methodology" className="fx-btn-ghost sm">
          Méthodologie & seuils →
        </Link>
        <Link href="/sandbox" className="fx-btn-ghost sm">
          Démo 60 secondes →
        </Link>
      </div>
    </ForensicPage>
  );
}
