import type { Metadata } from "next";
import Link from "next/link";
import {
  AlertOctagon,
  ArrowRight,
  Building2,
  CircleDollarSign,
  Copy,
  FileSignature,
  Ghost,
  Mail,
  Network,
  Repeat,
  Scale,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export const metadata: Metadata = {
  title: "Cas d'usage — P2P Fraud Detective FR",
  description:
    "Catalogue des typologies de fraude Procure-to-Pay couvertes par le démonstrateur : signaux observés, détecteurs activés et statut produit.",
};

type Status = "available" | "partial" | "roadmap";

const STATUS_META: Record<
  Status,
  { label: string; className: string }
> = {
  available: {
    label: "Disponible",
    className: "bg-[#e8f8f1] text-[#12714d] border-[#bfe7d5]",
  },
  partial: {
    label: "Couverture partielle",
    className: "bg-[#fff8e1] text-[#7a5d12] border-[#f0dca0]",
  },
  roadmap: {
    label: "Roadmap pilote",
    className: "bg-[#eaf1ff] text-[#1f3a6e] border-[#c9d6ee]",
  },
};

type Detector = { label: string; href: string };

type UseCase = {
  id: string;
  title: string;
  intro: string;
  signals: string[];
  detectors: Detector[];
  references: string[];
  status: Status;
  Icon: React.ComponentType<{ size?: number; className?: string }>;
};

const USE_CASES: UseCase[] = [
  {
    id: "faux-iban",
    title: "1 · Faux changement d'IBAN",
    intro:
      "Un attaquant ou un fournisseur compromis modifie les coordonnées bancaires d'un fournisseur référencé pour rediriger le prochain paiement vers un compte qu'il contrôle. C'est la typologie la plus fréquente de fraude P2P.",
    signals: [
      "Modification IBAN sans bon de commande associé ni demande tracée",
      "Changement IBAN suivi d'un paiement dans une fenêtre courte (proximité temporelle)",
      "Absence d'approbation 4-eyes sur le changement de référentiel",
      "Nouveau BIC dans un pays différent du précédent",
    ],
    detectors: [
      { label: "Historique référentiel", href: "/master-history" },
      { label: "Anneaux IBAN", href: "/rings" },
      { label: "Cases d'investigation", href: "/cases" },
    ],
    references: [
      "ISA 240 — risques de fraude management override",
      "ACPR — lignes directrices LCB-FT (2020)",
      "Rapport Tracfin Tome III 2024-2025 (typologies BEC)",
    ],
    status: "available",
    Icon: Repeat,
  },
  {
    id: "doublon-facture",
    title: "2 · Doublon de facture",
    intro:
      "Une même facture est saisie deux fois (montant identique, écart de 1 ou 2 jours) ou avec une variation mineure (numéro modifié, fournisseur quasi-identique) pour obtenir un double paiement.",
    signals: [
      "Bucket montant ± 0,01 € · fenêtre 30 jours",
      "Similarité fournisseur RapidFuzz WRatio ≥ 92",
      "Même IBAN destinataire, même invoice_id à un caractère près",
      "Pic d'activité sur un même fournisseur sur une période courte",
    ],
    detectors: [
      { label: "Doublons fuzzy", href: "/duplicates" },
      { label: "Cockpit risque", href: "/dashboard" },
    ],
    references: [
      "AICPA Audit Data Standards",
      "ISA 240 — tests journal entry",
    ],
    status: "available",
    Icon: Copy,
  },
  {
    id: "fournisseur-fictif",
    title: "3 · Fournisseur fictif",
    intro:
      "Création d'un fournisseur qui n'a pas d'existence réelle (SIREN absent ou récemment créé, adresse domiciliée, pas de site, statut Sirene inactif) pour facturer des prestations inexistantes.",
    signals: [
      "SIREN absent du référentiel INSEE Sirene ou très récent",
      "Statut Sirene actif/inactif incohérent avec l'activité facturée",
      "Adresse de domiciliation ou pays à haut risque",
      "Pas de présence DECP ni de marché public référencé",
    ],
    detectors: [
      { label: "Contrôle Sirene", href: "/sirene" },
      { label: "DECP & RBE INPI", href: "/decp-rbe" },
      { label: "Fiche fournisseur 360", href: "/vendors" },
    ],
    references: [
      "Sapin 2 art. 17 — due diligence tiers",
      "AFA — guide due diligence des tiers (2024)",
    ],
    status: "available",
    Icon: Ghost,
  },
  {
    id: "dormant-reactive",
    title: "4 · Fournisseur dormant réactivé",
    intro:
      "Un fournisseur inactif depuis plusieurs mois ou années est soudainement réactivé pour une facturation atypique, souvent juste après une modification de ses coordonnées.",
    signals: [
      "Absence de mouvement pendant 6 à 24 mois",
      "Réactivation immédiatement suivie d'une grosse facture ou d'un changement d'IBAN",
      "Reprise d'activité hors cycle saisonnier connu",
    ],
    detectors: [
      { label: "Historique référentiel", href: "/master-history" },
      { label: "Anomalies ML", href: "/anomalies" },
    ],
    references: [
      "ISA 240 — appendice A signaux comportementaux",
      "Continuous auditing — réveil de comptes dormants",
    ],
    status: "partial",
    Icon: AlertOctagon,
  },
  {
    id: "fractionnement",
    title: "5 · Fractionnement sous seuil (structuring)",
    intro:
      "Découpage volontaire d'une opération en plusieurs versements maintenus juste sous un seuil de contrôle (délégation, seuil COSI) pour éviter une revue ou un signalement.",
    signals: [
      "Cluster d'opérations 900-999 €",
      "Cumul mensuel par client / compte > 2 000 € ou > 10 000 €",
      "Coefficient de variation faible sur fenêtre 30 jours",
      "Multiples factures sous le seuil de délégation hiérarchique",
    ],
    detectors: [
      { label: "Fractionnement (structuring)", href: "/structuring" },
      { label: "Loi de Benford (scoping)", href: "/benford" },
    ],
    references: [
      "Art. D. 561-31-1 et R. 561-31-2 CMF",
      "Doctrine COSI sur seuils de transmission",
    ],
    status: "available",
    Icon: CircleDollarSign,
  },
  {
    id: "conflit-interets",
    title: "6 · Conflit d'intérêts",
    intro:
      "Un salarié, un dirigeant ou une personne politiquement exposée a un lien capitalistique, familial ou professionnel avec un fournisseur référencé. Le risque est l'orientation indue de la commande.",
    signals: [
      "Croisement employé ↔ bénéficiaire effectif d'un fournisseur",
      "PEP (Personne Exposée Politiquement) parmi les bénéficiaires effectifs",
      "Adresses partagées entre fournisseurs et personnel interne",
      "Plusieurs fournisseurs liés à une même personne physique",
    ],
    detectors: [
      { label: "Sanctions & PEP", href: "/sanctions" },
      { label: "Anneaux de fraude", href: "/rings" },
      { label: "DECP & RBE INPI", href: "/decp-rbe" },
    ],
    references: [
      "Sapin 2 art. 17 — code de conduite et cartographie",
      "AFA — guide secteur public (marchés publics)",
    ],
    status: "partial",
    Icon: Scale,
  },
  {
    id: "bec",
    title: "7 · Fraude au président / BEC",
    intro:
      "Business Email Compromise — usurpation d'identité d'un dirigeant, d'un fournisseur de confiance ou d'un service interne pour obtenir un virement urgent vers un compte frauduleux. Persistant et en hausse avec l'IA générative.",
    signals: [
      "Demande inhabituelle de virement urgent ou confidentiel",
      "Changement de coordonnées bancaires demandé par email",
      "Domaine d'email proche du domaine légitime (typosquatting)",
      "Pic d'activité hors cycle, hors PO",
    ],
    detectors: [
      { label: "Historique référentiel (IBAN)", href: "/master-history" },
      { label: "Anneaux IBAN", href: "/rings" },
      { label: "Anomalies ML", href: "/anomalies" },
    ],
    references: [
      "Europol IOCTA — BEC parmi les schémas les plus prolifiques",
      "ENISA — montée des deepfakes et de l'IA générative dans la fraude",
      "Cybermalveillance.gouv.fr — faux ordres de virement",
    ],
    status: "available",
    Icon: Mail,
  },
  {
    id: "e-invoicing",
    title: "8 · Anomalie e-invoicing",
    intro:
      "Anomalie autour des plateformes agréées de facturation électronique (PDP). La réforme française rend l'e-invoicing structurant à partir du 1er septembre 2026 pour la réception et l'émission ETI/GE.",
    signals: [
      "Facture émise via une plateforme non agréée alors que le fournisseur est censé être basculé",
      "Discordance entre données PDP et données ERP",
      "Numéro de TVA, SIREN ou statut PDP incohérent",
      "Plateforme de réception bascule sans notification",
    ],
    detectors: [
      { label: "Import de données", href: "/upload" },
      { label: "Contrôle Sirene", href: "/sirene" },
    ],
    references: [
      "Réforme facturation électronique — calendrier 1er sept. 2026 / 2027",
      "DGFiP — liste des plateformes agréées (PDP)",
    ],
    status: "roadmap",
    Icon: FileSignature,
  },
  {
    id: "marche-public",
    title: "9 · Marché public sensible",
    intro:
      "Analyse de signaux d'atteinte à la probité sur les marchés publics : concentration de fournisseurs, attributions répétées, sociétés taxis dans le BTP, structures opaques.",
    signals: [
      "Forte concentration d'un fournisseur sur une collectivité",
      "Attribution récurrente sans mise en concurrence visible",
      "Bénéficiaires effectifs opaques ou pays à risque",
      "Présence DECP atypique (montants, fréquences, codes CPV)",
    ],
    detectors: [
      { label: "DECP & RBE INPI", href: "/decp-rbe" },
      { label: "Anneaux de fraude", href: "/rings" },
      { label: "Sanctions & PEP", href: "/sanctions" },
    ],
    references: [
      "AFA — guide marchés publics et lutte contre la corruption",
      "Rapport Tracfin Tome III 2024-2025 (sociétés taxis BTP)",
      "Cour des comptes — rapports publics sur la commande publique",
    ],
    status: "partial",
    Icon: Building2,
  },
];

function StatusBadge({ status }: { status: Status }) {
  const meta = STATUS_META[status];
  return (
    <span
      className={`inline-flex items-center rounded border px-2 py-0.5 text-[11px] font-semibold ${meta.className}`}
    >
      {meta.label}
    </span>
  );
}

export default function UseCasesPage() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-10 lg:px-8">
      <div className="mb-1 text-xs uppercase tracking-wider text-[#5a6478]">
        Catalogue
      </div>
      <h1 className="mb-2 text-3xl font-bold text-[#0f1b33] dark:text-white">
        Cas d&apos;usage Procure-to-Pay
      </h1>
      <p className="mb-6 max-w-3xl text-sm leading-6 text-[#5a6478]">
        Typologies de fraude et d&apos;anomalies couvertes par le démonstrateur,
        avec les signaux observés, les détecteurs activés et le statut
        d&apos;implémentation. Cette page est un référentiel pédagogique :
        elle n&apos;exécute aucun contrôle. Pour tester un scénario live,
        utilisez la{" "}
        <Link href="/sandbox" className="text-[#1f3a6e] hover:underline">
          sandbox interactive
        </Link>
        .
      </p>

      <div className="mb-6 flex flex-wrap items-center gap-2 rounded-md border border-[#d7deea] bg-[#f7f9fc] px-4 py-3 text-xs dark:bg-white/[0.03]">
        <span className="font-semibold text-[#0f1b33] dark:text-white">
          Statuts utilisés sur cette page :
        </span>
        <StatusBadge status="available" />
        <span className="text-[#5a6478]">détecté par un module live</span>
        <span className="text-[#9aa3b3]">·</span>
        <StatusBadge status="partial" />
        <span className="text-[#5a6478]">signaux exposés, calibration pilote requise</span>
        <span className="text-[#9aa3b3]">·</span>
        <StatusBadge status="roadmap" />
        <span className="text-[#5a6478]">à intégrer avec partenaire / source officielle</span>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {USE_CASES.map((uc) => (
          <Card key={uc.id} id={uc.id} className="flex flex-col">
            <CardHeader>
              <CardTitle className="flex items-start justify-between gap-3">
                <span className="flex items-center gap-2">
                  <span className="grid h-9 w-9 shrink-0 place-items-center rounded-md bg-[#eaf1ff] text-[#1f3a6e]">
                    <uc.Icon size={18} />
                  </span>
                  <span className="text-base">{uc.title}</span>
                </span>
                <StatusBadge status={uc.status} />
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-1 flex-col gap-3 text-sm">
              <p className="text-[#1a1f2c] dark:text-white/80">{uc.intro}</p>

              <div>
                <div className="mb-1 text-xs font-semibold uppercase tracking-wider text-[#5a6478]">
                  Signaux observés
                </div>
                <ul className="list-disc space-y-0.5 pl-5 text-sm text-[#1a1f2c] dark:text-white/80">
                  {uc.signals.map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              </div>

              <div>
                <div className="mb-1 text-xs font-semibold uppercase tracking-wider text-[#5a6478]">
                  Détecteurs / pages associés
                </div>
                <div className="flex flex-wrap gap-2">
                  {uc.detectors.map((d) => (
                    <Link
                      key={d.href}
                      href={d.href}
                      className="inline-flex items-center gap-1 rounded border border-[#c9d6ee] bg-white px-2 py-1 text-xs font-medium text-[#1f3a6e] transition-colors hover:bg-[#eaf1ff] dark:bg-white/[0.04]"
                    >
                      {d.label}
                      <ArrowRight size={12} />
                    </Link>
                  ))}
                </div>
              </div>

              <div className="mt-auto pt-1">
                <div className="mb-1 text-xs font-semibold uppercase tracking-wider text-[#5a6478]">
                  Références
                </div>
                <ul className="space-y-0.5 text-xs text-[#5a6478]">
                  {uc.references.map((r) => (
                    <li key={r}>· {r}</li>
                  ))}
                </ul>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-8 rounded-md border border-[#d7deea] bg-[#f7f9fc] p-5 text-sm text-[#5a6478] dark:bg-white/[0.03]">
        <p>
          Les détecteurs cités ci-dessus tournent sur des{" "}
          <strong>données 100&nbsp;% synthétiques</strong> en démonstration
          publique. La calibration des seuils, la cartographie des règles
          internes et le rattachement à des sources officielles (RNE/INPI,
          PDP agréées, listes consolidées) sont des sujets à traiter au cas
          par cas avant un usage opérationnel. Voir{" "}
          <Link href="/methodology" className="text-[#1f3a6e] hover:underline">
            la page Méthodologie
          </Link>{" "}
          et{" "}
          <Link href="/about" className="text-[#1f3a6e] hover:underline">
            À propos &amp; limites
          </Link>
          .
        </p>
      </div>
    </div>
  );
}
