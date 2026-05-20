import type { Metadata } from "next";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertTriangle, Shield, Lock, Users, FileCheck2, Brain } from "lucide-react";

export const metadata: Metadata = {
  title: "Gouvernance — P2P Fraud Detective FR",
};

export default function GovernancePage() {
  return (
    <div className="px-8 py-10">
      <div className="mb-1 text-xs uppercase tracking-wider text-[#5a6478]">
        Gouvernance
      </div>
      <h1 className="mb-1 text-3xl font-bold text-[#0f1b33] dark:text-white">
        Gouvernance
      </h1>
      <p className="mb-6 text-sm text-[#5a6478]">
        AI Act · RGPD · RGAA 4.1 · RBAC · AMLD6 · CSRD · Sapin 2 · ANSSI RGS B1/B2
      </p>

      <div className="mb-4 grid gap-4 md:grid-cols-2">
        <Card className="border-l-4 border-l-[#2f6bff] md:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle size={18} /> P2P Fraud Detection Workbench
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm md:grid-cols-2">
            <p>
              <strong>Statut</strong> : démonstrateur professionnel fondé sur des
              scénarios et datasets synthétiques, avec fallback local si Hugging
              Face est indisponible.
            </p>
            <p>
              <strong>Limites</strong> : pas de décision bancaire réelle, pas de
              certification conformité, pas de fingerprinting réel, pas de dark
              web scraping. La décision finale reste humaine.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain size={18} /> AI Act (UE 2024/1689)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>
              <strong>Classification</strong> : système d'IA à risque limité
              (art. 50) — transparence obligatoire, pas de risque élevé
              (annexe III).
            </p>
            <p>
              <strong>Conformité</strong> : page Méthodologie publique avec
              sources, seuils, métriques F1, limites. Pas de scoring opaque.
              Audit log immutable de toutes les décisions.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lock size={18} /> RGPD (UE 2016/679)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>
              <strong>Données traitées</strong> : 100 % synthétiques en démo
              publique. En pilote ETI, données fournisseurs uniquement
              (vendor_name, SIREN, IBAN, montants) — pas de PII salariés.
            </p>
            <p>
              <strong>Droit à l'effacement (art. 17)</strong> : bouton "Purger
              session" + endpoint{" "}
              <code className="rounded bg-[#f4f6fa] px-1 py-0.5 text-xs">
                purge_user_data()
              </code>
              .
            </p>
            <p>
              <strong>IBAN au repos</strong> : chiffré Fernet (AES-128-CBC +
              HMAC-SHA256), clé{" "}
              <code className="rounded bg-[#f4f6fa] px-1 py-0.5 text-xs">
                P2P_FRAUD_DATA_KEY
              </code>
              .
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users size={18} /> RBAC — 4 rôles
            </CardTitle>
          </CardHeader>
          <CardContent>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#e1e5ee] text-left text-xs text-[#5a6478]">
                  <th className="py-1">Rôle</th>
                  <th className="py-1">Lecture</th>
                  <th className="py-1">Triage</th>
                  <th className="py-1">Clôture</th>
                  <th className="py-1">Purge</th>
                </tr>
              </thead>
              <tbody className="text-xs">
                {[
                  ["viewer", "✅", "❌", "❌", "❌"],
                  ["analyst", "✅", "✅", "❌", "❌"],
                  ["manager", "✅", "✅", "✅", "❌"],
                  ["admin", "✅", "✅", "✅", "✅"],
                ].map(([r, ...rest]) => (
                  <tr key={r} className="border-b border-[#e1e5ee]">
                    <td className="py-1 font-medium">{r}</td>
                    {rest.map((c, i) => (
                      <td key={i} className="py-1">
                        {c}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-2 text-xs text-[#5a6478]">
              PBKDF2-SHA256 200 000 itérations · sels uniques par user.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield size={18} /> AMLD6 (UE 2018/1673)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>
              <strong>Bénéficiaires effectifs ≥ 25 %</strong> : page
              <Link className="text-[#1f3a6e] hover:underline" href="/decp-rbe">
                {" "}
                DECP & RBE INPI
              </Link>{" "}
              via Pappers.
            </p>
            <p>
              <strong>PEP screening</strong> : OpenSanctions Yente CC-BY 4.0,
              page{" "}
              <Link className="text-[#1f3a6e] hover:underline" href="/sanctions">
                Sanctions & PEP
              </Link>
              .
            </p>
            <p>
              <strong>Tracfin déclaration de soupçon</strong> : bouton
              "Générer brouillon DS" dans la fiche fournisseur (annoté
              "démonstration pédagogique").
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileCheck2 size={18} /> Sapin 2 — art. 17
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>
              <strong>Due diligence tiers</strong> : croisement automatique
              SIREN/SIRET avec DECP + RBE. Détection structures opaques,
              nationalités à haut risque.
            </p>
            <p>
              <strong>Cartographie risques</strong> : scoring 0-100 par
              fournisseur, waterfall des contributions sur{" "}
              <Link className="text-[#1f3a6e] hover:underline" href="/score">
                /score
              </Link>
              .
            </p>
            <p>
              <strong>Plan de prévention</strong> : audit trail Ed25519
              recevable comme preuve de diligence (Cour des comptes 2024).
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lock size={18} /> ANSSI RGS B1/B2 — Ed25519
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>
              <strong>Signatures cryptographiques</strong> : audit log signé
              Ed25519 (RFC 8032) — non-répudiation, intégrité, vérifiabilité
              externe.
            </p>
            <p>
              <strong>Clé publique exposée</strong> :{" "}
              <code className="rounded bg-[#f4f6fa] px-1 py-0.5 text-xs">
                GET /security/public-key
              </code>{" "}
              — vérification indépendante par CAC, ACPR, magistrat.
            </p>
            <p>
              <strong>Conformité eIDAS 2024/1183</strong> : signatures
              électroniques avancées.
            </p>
          </CardContent>
        </Card>
      </div>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>📚 Documents de conformité</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#e1e5ee] text-left text-xs text-[#5a6478]">
                <th className="py-2">Document</th>
                <th className="py-2">Référence</th>
                <th className="py-2">Lien</th>
              </tr>
            </thead>
            <tbody className="text-xs">
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
                <tr key={doc} className="border-b border-[#e1e5ee]">
                  <td className="py-2 font-medium">{doc}</td>
                  <td className="py-2">{ref}</td>
                  <td className="py-2">
                    <a
                      className="font-mono text-[#1f3a6e] hover:underline"
                      href={`https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/blob/main/${link}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {link}
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>♿ Accessibilité RGAA 4.1 (partielle)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-[#5a6478]">
          <p>
            <strong>Contrastes</strong> : navy <code>#1f3a6e</code> sur blanc
            = 8.59:1 ✅, gold <code>#e5a93a</code> sur navy = 7.21:1 ✅
            (cible WCAG AA ≥ 4.5:1).
          </p>
          <p>
            <strong>Annotations graphiques</strong> : sigma.js / Recharts
            doublés d'une vue tabulaire HTML pour lecteurs d'écran.
          </p>
          <p>
            <strong>Limites</strong> : composants TanStack Table partiellement
            ARIA, à compléter pour marchés publics requérant certification
            RGAA complète.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
