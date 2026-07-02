import type { Metadata } from "next";
import Link from "next/link";
import { ForensicPage } from "@/components/forensic-page";

export const metadata: Metadata = {
  title: "FNC-RF : le fichier des IBAN frauduleux (Banque de France) — et ce qu'il ne couvre pas",
  description:
    "Depuis le 7 mai 2026, le FNC-RF partage les IBAN frauduleux entre banques. Il agit côté PSP, au moment du virement. La fraude au RIB fournisseur s'installe en amont — au changement du master data. Les trois couches expliquées : FNC-RF, VoP, contrôle interne pre-payment.",
  keywords: [
    "FNC-RF",
    "fraude IBAN",
    "Banque de France",
    "IBAN frauduleux",
    "Verification of Payee",
    "VoP",
    "fraude au virement",
    "changement RIB fournisseur",
    "BEC",
  ],
};

const LAYERS = [
  {
    name: "FNC-RF · Banque de France",
    when: "Après signalement — IBAN déjà identifié frauduleux",
    where: "Côté PSP (interbancaire)",
    covers: "Réutilisation d'un IBAN déjà signalé par une autre banque",
    misses: "Le premier paiement vers un IBAN pas encore signalé",
    since: "7 mai 2026",
  },
  {
    name: "VoP · Verification of Payee",
    when: "Au moment du virement",
    where: "Côté PSP (zone euro)",
    covers: "Divergence nom ↔ IBAN à l'exécution du paiement",
    misses: "Un RIB frauduleux enregistré sous le nom exact du fournisseur",
    since: "9 octobre 2025 (IPR 2024/886)",
  },
  {
    name: "P2P Fraud Detective",
    when: "Au changement du master data — 48 h avant le règlement",
    where: "Dans votre SI (contrôle interne)",
    covers: "Modification de RIB sans 4-eyes, fiche fantôme, faisceau BEC",
    misses: "—",
    since: "Couche pre-payment, complémentaire des deux autres",
  },
];

export default function FncRfPage() {
  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Veille réglementaire · mai 2026</div>
          <h1 style={{ marginTop: 9 }}>
            FNC-RF : le fichier des IBAN frauduleux —{" "}
            <span className="italic">et ce qu&apos;il ne couvre pas</span>
          </h1>
          <p className="sub">
            Depuis le 7 mai 2026, la Banque de France opère le Fichier National Commun de la
            Relation Frauduleuse : les IBAN frauduleux connus sont partagés entre tous les PSP.
            C&apos;est une excellente nouvelle — et elle ne remplace aucun de vos contrôles internes.
          </p>
        </div>
      </div>

      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <h2>Ce que le FNC-RF change</h2>
          <span className="glyph">◉</span>
        </div>
        <div className="fx-panel-body">
          <p style={{ fontSize: 14, lineHeight: 1.7, color: "var(--fg-2)", marginBottom: 12 }}>
            Le FNC-RF lève le cloisonnement du secret bancaire sur la donnée de fraude : un IBAN
            signalé frauduleux par une banque devient visible de toutes les autres. Combiné à la{" "}
            <strong style={{ color: "var(--fg)" }}>Verification of Payee</strong> (obligatoire
            depuis octobre 2025 pour tous les PSP de la zone euro), le système bancaire filtre
            désormais deux choses : les IBAN déjà connus comme frauduleux, et les divergences
            nom ↔ IBAN au moment du virement.
          </p>
          <p style={{ fontSize: 14, lineHeight: 1.7, color: "var(--fg-2)" }}>
            Ce que ces deux couches ne voient pas :{" "}
            <strong style={{ color: "var(--fg)" }}>
              le moment où la fraude s&apos;installe dans votre référentiel fournisseur
            </strong>
            . Un RIB modifié par email usurpé, sans contre-signature, 48 heures avant un règlement,
            passe le VoP si le nom déclaré est exact — et le FNC-RF si l&apos;IBAN n&apos;a jamais été
            signalé. Les CRCC l&apos;ont dit explicitement : les procédures internes de vérification
            restent un sujet à part entière.
          </p>
        </div>
      </div>

      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <h2>Les trois couches de défense</h2>
          <span className="glyph">▤</span>
        </div>
        <div className="fx-table-wrap">
          <table className="fx-table">
            <thead>
              <tr>
                <th>Couche</th>
                <th>Quand elle agit</th>
                <th>Où</th>
                <th>Couvre</th>
                <th>Ne couvre pas</th>
              </tr>
            </thead>
            <tbody>
              {LAYERS.map((l) => (
                <tr key={l.name}>
                  <td className="key">
                    {l.name}
                    <div style={{ color: "var(--muted)", fontSize: 10, marginTop: 3 }}>{l.since}</div>
                  </td>
                  <td>{l.when}</td>
                  <td>{l.where}</td>
                  <td>{l.covers}</td>
                  <td style={{ color: l.misses === "—" ? "var(--muted)" : "var(--warn)" }}>
                    {l.misses}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <h2>Le connecteur FNC-RF est prêt</h2>
          <span className="glyph">✓</span>
        </div>
        <div className="fx-panel-body">
          <p style={{ fontSize: 14, lineHeight: 1.7, color: "var(--fg-2)", marginBottom: 12 }}>
            L&apos;API du FNC-RF est aujourd&apos;hui réservée aux PSP. L&apos;emplacement du
            connecteur est déjà réservé dans le produit : interface figée, variables
            d&apos;environnement documentées (<code className="fx-mono">FNC_RF_API_URL</code>,{" "}
            <code className="fx-mono">FNC_RF_API_KEY</code>). Le jour où la Banque de France ouvre
            l&apos;accès aux entreprises, le cross-check « IBAN présent au FNC-RF » s&apos;active
            par simple configuration — sans refactor, et chaque vérification rejoindra la piste
            d&apos;audit signée Ed25519.
          </p>
          <div className="flex flex-wrap gap-2">
            <Link href="/connecteurs" className="fx-btn-ghost sm">
              Voir l&apos;emplacement du connecteur →
            </Link>
            <Link href="/sandbox" className="fx-btn-ghost sm">
              Rejouer un BEC en 60 secondes →
            </Link>
            <Link href="/master-history" className="fx-btn-ghost sm">
              Surveiller les changements de RIB →
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
          En une phrase
        </div>
        <p style={{ fontSize: 15, lineHeight: 1.7, color: "var(--fg)", margin: 0 }}>
          Le FNC-RF protège le système bancaire <em>après</em> qu&apos;un IBAN a été signalé ; la
          VoP protège le virement <em>au moment</em> où il part ; P2P Fraud Detective protège votre
          référentiel fournisseur <em>avant</em> — là où 80 % des fraudes P2P commencent.
        </p>
      </div>
    </ForensicPage>
  );
}
