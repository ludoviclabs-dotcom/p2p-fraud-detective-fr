import type { Metadata } from "next";
import Link from "next/link";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  AlertTriangle,
  BookOpen,
  Database,
  FileText,
  Github,
  ShieldCheck,
  UserCheck,
} from "lucide-react";

export const metadata: Metadata = {
  title: "À propos & limites — P2P Fraud Detective FR",
  description:
    "Périmètre, limites d'usage, sources de données, licences et validation requise avant production.",
};

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-10 lg:px-8">
      <div className="mb-1 text-xs uppercase tracking-wider text-[#5a6478]">
        Transparence
      </div>
      <h1 className="mb-2 text-3xl font-bold text-[#0f1b33] dark:text-white">
        À propos &amp; limites
      </h1>
      <p className="mb-8 text-sm leading-6 text-[#5a6478]">
        Cette page synthétise le périmètre, les limites, les sources et les
        validations requises pour utiliser P2P Fraud Detective FR autrement
        qu&apos;en démonstration publique.
      </p>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen size={18} /> Périmètre du produit
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>
            <strong>P2P Fraud Detective FR</strong> est un démonstrateur public
            d&apos;outil d&apos;aide à la détection, l&apos;investigation et la
            documentation d&apos;anomalies du cycle{" "}
            <em>Procure-to-Pay</em> (achats → comptabilité → paiement).
          </p>
          <p>
            L&apos;objectif explicite est de devenir, à terme, une couche
            spécialisée de contrôle continu de l&apos;intégrité fournisseur et
            paiement, interopérable avec ERP, plateformes de facturation
            électronique et services de vérification de bénéficiaire (VoP).
            Aujourd&apos;hui, le produit est en phase démonstrateur — voir la
            roadmap dans{" "}
            <a
              href="https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/blob/main/docs/migration-v2-recap.md"
              className="text-[#1f3a6e] hover:underline"
              target="_blank"
              rel="noreferrer"
            >
              docs/migration-v2-recap.md
            </a>
            .
          </p>
        </CardContent>
      </Card>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UserCheck size={18} /> Pour qui ?
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <ul className="list-disc space-y-1 pl-5">
            <li>Directions financières d&apos;ETI (200 M€ – 2 Md€ CA)</li>
            <li>Cabinets d&apos;audit mid-tier et fonctions d&apos;audit interne</li>
            <li>Fonctions conformité et RCCI</li>
            <li>
              Acteurs publics : collectivités, hôpitaux, universités, CRC,
              inspections, juridictions financières
            </li>
            <li>
              Secteurs à forte exigence de probité (santé, associations, sport,
              BTP — cf. guides AFA)
            </li>
          </ul>
        </CardContent>
      </Card>

      <Card className="mb-4 border-[#f0dca0] bg-[#fff8e1]/40">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-[#7a5d12]">
            <AlertTriangle size={18} /> Ce que le produit n&apos;est pas
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <ul className="list-disc space-y-1 pl-5">
            <li>
              <strong>Pas un système LCB-FT opérationnel</strong> au sens de
              l&apos;art. L. 561-2 du Code monétaire et financier. L&apos;outil
              ne transmet pas de déclarations de soupçon au portail ERMES de
              Tracfin et n&apos;a pas vocation à le faire sans qualification
              d&apos;assujetti.
            </li>
            <li>
              <strong>Pas une solution clé en main DORA, NIS2 ou AI Act haut
              risque (annexe III)</strong>. Le produit se positionne comme un
              système d&apos;IA à risque limité (AI Act art. 50) ; il facilite
              la mise en œuvre de contrôles attendus par ces référentiels mais
              ne s&apos;y substitue pas.
            </li>
            <li>
              <strong>Pas une signature qualifiée eIDAS</strong> niveau
              « qualifié ». L&apos;audit trail signé Ed25519 (RFC 8032) est
              conforme au socle technique eIDAS et RGS B1/B2 ; sa valeur
              probatoire dans un contentieux dépend du contexte et doit être
              validée au cas par cas.
            </li>
            <li>
              <strong>Pas un substitut</strong> d&apos;audit légal, de
              commissaire aux comptes, de contrôleur interne ou d&apos;une
              autorité de contrôle. C&apos;est un complément d&apos;aide à la
              décision sous supervision humaine.
            </li>
            <li>
              <strong>Pas un système de scoring sur personnes physiques</strong>.
              Le scoring porte sur des transactions et des entités morales.
            </li>
          </ul>
        </CardContent>
      </Card>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database size={18} /> Données et licences
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>
            <strong>Démonstration publique</strong> : données 100&nbsp;%
            synthétiques générées par{" "}
            <code className="rounded bg-[#f4f6fa] px-1 py-0.5 text-xs">
              p2p_fraud.synthetic.generator
            </code>{" "}
            (échantillon{" "}
            <code className="rounded bg-[#f4f6fa] px-1 py-0.5 text-xs">
              data/samples/sample_5k.csv
            </code>
            ).
          </p>
          <p>
            <strong>Sources publiques utilisées</strong> (en pilote / live) :
          </p>
          <ul className="list-disc space-y-1 pl-5">
            <li>INSEE Sirene v3 — Licence Ouverte 2.0 (Etalab)</li>
            <li>DECP (Données Essentielles de la Commande Publique) — Etalab</li>
            <li>OpenSanctions Yente — CC-BY 4.0</li>
            <li>Trésor FR (gels d&apos;avoirs) — Légifrance</li>
            <li>Pappers (RBE en mode démo) — commercial</li>
          </ul>
          <p className="text-xs text-[#5a6478]">
            L&apos;accès aux données de bénéficiaires effectifs (RBE / INPI)
            est encadré et soumis à autorisation pour certains usages ;
            l&apos;accès doit être qualifié au cas par cas en production.
          </p>
        </CardContent>
      </Card>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShieldCheck size={18} /> Validation requise avant production
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>
            Toute utilisation de l&apos;outil hors démonstration publique
            implique au minimum :
          </p>
          <ul className="list-disc space-y-1 pl-5">
            <li>
              une <strong>DPIA</strong> (analyse d&apos;impact relative à la
              protection des données — art. 35 RGPD) adaptée au contexte
              client ;
            </li>
            <li>
              la <strong>validation par le DPO</strong>, le RSSI et le conseil
              juridique du déployeur ;
            </li>
            <li>
              un <strong>audit de sécurité</strong> indépendant pour un usage
              en environnement régulé (DORA, secteur public sensible) ;
            </li>
            <li>
              un <strong>pilote instrumenté</strong> sur données client pour
              calibrer les seuils et valider rétrospectivement la précision
              avant tout claim de performance en production ;
            </li>
            <li>
              le <strong>respect des règles de rétention</strong> et de purge
              prévues par le déployeur et les régimes applicables (RGPD,
              AMLD6, CMF, CGI).
            </li>
          </ul>
        </CardContent>
      </Card>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText size={18} /> Maturité du produit
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>
            Le projet est aujourd&apos;hui en phase{" "}
            <strong>démonstrateur public</strong>. La trajectoire prévue
            comporte quatre étapes :
          </p>
          <ol className="list-decimal space-y-1 pl-5">
            <li>
              <strong>Démonstrateur</strong> (état actuel) — données
              synthétiques, fonctionnalités présentées comme aide à
              l&apos;investigation, supervision humaine systématique.
            </li>
            <li>
              <strong>POC entreprise</strong> — preuve de concept sur données
              réelles ou semi-réelles avec un client identifié.
            </li>
            <li>
              <strong>Pilote ETI / secteur public</strong> — usage contrôlé
              sur un échantillon avec workflows, gouvernance et exports
              probatoires complets.
            </li>
            <li>
              <strong>Produit SaaS / on-premise</strong> — industrialisation,
              connecteurs ERP, e-invoicing, VoP, support, SLA.
            </li>
          </ol>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Github size={18} /> Licence &amp; contact
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>
            <strong>Licence</strong> : MIT — voir{" "}
            <a
              href="https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/blob/main/LICENSE"
              className="text-[#1f3a6e] hover:underline"
              target="_blank"
              rel="noreferrer"
            >
              LICENSE
            </a>
            .
          </p>
          <p>
            <strong>Code source</strong> :{" "}
            <a
              href="https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr"
              className="text-[#1f3a6e] hover:underline"
              target="_blank"
              rel="noreferrer"
            >
              github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr
            </a>
          </p>
          <p>
            <strong>Signaler un problème</strong> :{" "}
            <a
              href="https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/issues"
              className="text-[#1f3a6e] hover:underline"
              target="_blank"
              rel="noreferrer"
            >
              issues GitHub
            </a>
          </p>
          <p className="pt-2 text-xs text-[#5a6478]">
            Voir aussi :{" "}
            <Link href="/governance" className="text-[#1f3a6e] hover:underline">
              Gouvernance
            </Link>{" "}
            ·{" "}
            <Link href="/methodology" className="text-[#1f3a6e] hover:underline">
              Méthodologie
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
