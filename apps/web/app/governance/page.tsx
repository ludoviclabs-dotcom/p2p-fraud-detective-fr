import type { Metadata } from "next";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Shield, Lock, Users, FileCheck2, Brain, Info } from "lucide-react";

export const metadata: Metadata = {
  title: "Gouvernance — P2P Fraud Detective FR",
};

type Status = "applicable" | "aide" | "client";

const STATUS_LABEL: Record<Status, { dot: string; label: string; className: string }> = {
  applicable: {
    dot: "🟢",
    label: "Applicable et documenté",
    className: "bg-[#e8f8f1] text-[#12714d] border-[#bfe7d5]",
  },
  aide: {
    dot: "🟡",
    label: "Aide à la mise en œuvre",
    className: "bg-[#fff8e1] text-[#7a5d12] border-[#f0dca0]",
  },
  client: {
    dot: "🔵",
    label: "À configurer selon le contexte client",
    className: "bg-[#eaf1ff] text-[#1f3a6e] border-[#c9d6ee]",
  },
};

function StatusBadge({ status }: { status: Status }) {
  const meta = STATUS_LABEL[status];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded border px-2 py-0.5 text-[11px] font-semibold ${meta.className}`}
    >
      <span aria-hidden>{meta.dot}</span>
      {meta.label}
    </span>
  );
}

export default function GovernancePage() {
  return (
    <div className="px-8 py-10">
      <div className="mb-1 text-xs uppercase tracking-wider text-[#5a6478]">
        Gouvernance
      </div>
      <h1 className="mb-1 text-3xl font-bold text-[#0f1b33] dark:text-white">
        Gouvernance
      </h1>
      <p className="mb-4 text-sm text-[#5a6478]">
        Référentiels couverts par la documentation produit — statut indiqué
        pour chaque cadre. Aucune des cartes ci-dessous ne vaut auto-certification :
        le produit est un démonstrateur public et une mise en production
        nécessite la validation par votre DPO, RSSI, juriste et auditeur.
      </p>

      <Card className="mb-4 border-[#d7deea] bg-[#f7f9fc] dark:bg-white/[0.03]">
        <CardContent className="flex flex-col gap-2 py-4 text-sm">
          <div className="flex items-center gap-2 text-[#5a6478]">
            <Info size={16} />
            <span className="font-semibold text-[#0f1b33] dark:text-white">
              Légende des statuts
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            <StatusBadge status="applicable" />
            <StatusBadge status="aide" />
            <StatusBadge status="client" />
          </div>
          <p className="text-xs text-[#5a6478]">
            🟢 le projet implémente directement le contrôle (ex. RGPD art. 30,
            AI Act art. 50, RGS B1/B2 Ed25519). 🟡 le projet fournit des
            artefacts pour aider le déployeur (ex. AMLD6 mapping, Sapin 2 due
            diligence). 🔵 à paramétrer selon le déploiement (ex. NIS2, DPIA
            spécifique, RGAA complet).
          </p>
        </CardContent>
      </Card>

      <div className="mb-4 grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between gap-2">
              <span className="flex items-center gap-2">
                <Brain size={18} /> AI Act (UE 2024/1689)
              </span>
              <StatusBadge status="applicable" />
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>
              <strong>Classification</strong> : système d'IA à risque limité
              (art. 50) — transparence obligatoire, pas de risque élevé
              (annexe III).
            </p>
            <p>
              <strong>Transparence</strong> : page Méthodologie publique avec
              sources, seuils, métriques F1 sur dataset synthétique, limites
              connues. Pas de scoring opaque. Audit log immutable de toutes
              les décisions.
            </p>
            <p className="text-xs text-[#5a6478]">
              Obligations haut risque (annexe III) applicables à partir du
              2 août 2026 — non concernées par ce produit.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between gap-2">
              <span className="flex items-center gap-2">
                <Lock size={18} /> RGPD (UE 2016/679)
              </span>
              <StatusBadge status="applicable" />
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>
              <strong>Données traitées</strong> : 100 % synthétiques en démo
              publique. En pilote ETI, données fournisseurs uniquement
              (vendor_name, SIREN, IBAN, montants) — pas de PII salariés. Si
              le référentiel contient des entrepreneurs individuels ou des
              personnes nommément désignées, un DPIA spécifique est requis.
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
            <CardTitle className="flex items-center justify-between gap-2">
              <span className="flex items-center gap-2">
                <Users size={18} /> RBAC — 4 rôles
              </span>
              <StatusBadge status="applicable" />
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
            <CardTitle className="flex items-center justify-between gap-2">
              <span className="flex items-center gap-2">
                <Shield size={18} /> AMLD6 (UE 2018/1673)
              </span>
              <StatusBadge status="aide" />
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p className="rounded bg-[#fff8e1] px-2 py-1 text-xs text-[#7a5d12]">
              Couverture partielle — démonstrateur non opérationnel. Le
              produit n'est pas un système LCB-FT au sens de l'art. L. 561-2
              du Code monétaire et financier (assujettis).
            </p>
            <p>
              <strong>Bénéficiaires effectifs ≥ 25 %</strong> : page
              <a className="text-[#1f3a6e] hover:underline" href="/decp-rbe">
                {" "}
                DECP & RBE INPI
              </a>{" "}
              via Pappers (mode démo). Stratégie RNE/INPI directe à mettre en
              œuvre en pilote.
            </p>
            <p>
              <strong>PEP screening</strong> : OpenSanctions Yente CC-BY 4.0,
              page{" "}
              <a className="text-[#1f3a6e] hover:underline" href="/sanctions">
                Sanctions & PEP
              </a>
              .
            </p>
            <p>
              <strong>Export documentaire d'investigation</strong> : PDF +
              JSONL signé téléchargeables depuis la fiche fournisseur, annotés
              « démonstration pédagogique ». Non transmissibles au portail
              ERMES de Tracfin sans qualification d'assujetti (art. L. 561-2
              CMF).
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between gap-2">
              <span className="flex items-center gap-2">
                <FileCheck2 size={18} /> Sapin 2 — art. 17
              </span>
              <StatusBadge status="aide" />
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>
              <strong>Due diligence tiers</strong> : croisement automatique
              SIREN/SIRET avec DECP + RBE. Détection structures opaques,
              nationalités à haut risque.
            </p>
            <p>
              <strong>Cartographie des risques</strong> : scoring 0-100 par
              fournisseur, waterfall des contributions sur{" "}
              <a className="text-[#1f3a6e] hover:underline" href="/score">
                /score
              </a>
              .
            </p>
            <p>
              <strong>Plan de prévention</strong> : audit trail signé Ed25519
              conforme aux standards techniques RGS B1/B2. La qualification
              probatoire dans un contentieux dépend du contexte d'usage et
              doit être validée au cas par cas par le conseil juridique et
              l'auditeur du déployeur.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between gap-2">
              <span className="flex items-center gap-2">
                <Lock size={18} /> ANSSI RGS B1/B2 — Ed25519
              </span>
              <StatusBadge status="applicable" />
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>
              <strong>Signatures cryptographiques</strong> : audit log signé
              Ed25519 (RFC 8032) — intégrité prouvable, non-répudiation,
              vérifiabilité externe via clé publique.
            </p>
            <p>
              <strong>Clé publique exposée</strong> :{" "}
              <code className="rounded bg-[#f4f6fa] px-1 py-0.5 text-xs">
                GET /security/public-key
              </code>{" "}
              — permet la vérification indépendante par un tiers (CAC,
              superviseur, magistrat).
            </p>
            <p>
              <strong>Cadre eIDAS</strong> : règlement (UE) 910/2014 mis à
              jour par le règlement (UE) 2024/1183 — signature électronique
              avancée.
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
                  "docs/compliance/dpia_template.md",
                ],
                [
                  "Registre AI Act",
                  "Art. 50 UE 2024/1689",
                  "docs/compliance/ai_act_register.md",
                ],
                [
                  "Registre RGPD art. 30",
                  "RGPD art. 30",
                  "docs/compliance/data_processing_record.md",
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
          <CardTitle className="flex items-center justify-between gap-2">
            <span>♿ Accessibilité RGAA 4.1 (partielle)</span>
            <StatusBadge status="client" />
          </CardTitle>
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
