import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { ForensicPage } from "@/components/forensic-page";

const glossary = [
  ["APP fraud", "Authorized Push Payment fraud: la victime autorise elle-même le paiement sous manipulation."],
  ["Reason code", "Code explicable qui documente pourquoi un score augmente."],
  ["Risk decision", "Recommandation de traitement: ALLOW, MONITOR, MANUAL_REVIEW ou BLOCK_RECOMMENDED."],
  ["Risk level", "Niveau lisible: LOW, MEDIUM, HIGH ou CRITICAL."],
  ["VoP simulée", "Vérification nom/IBAN de démonstration: match, close_match, no_match ou unavailable."],
  ["Mule account", "Compte relais utilisé pour recevoir ou disperser des fonds frauduleux."],
  ["Evidence pack", "Dossier exportable contenant transaction, score, raisons, graphe, timeline et notes."],
  ["Source locale de démo", "Scénarios synthétiques intégrés utilisés si la source Hugging Face n'est pas configurée ou indisponible."],
];

const reasonFamilies = [
  ["Beneficiary / IBAN", "NEW_BENEFICIARY, IBAN_NAME_MISMATCH, SUPPLIER_RIB_RECENT_CHANGE"],
  ["Narrative APP", "NARRATIVE_URGENCY, NARRATIVE_SAFE_ACCOUNT, NARRATIVE_INVESTMENT"],
  ["Velocity", "UNUSUAL_AMOUNT, NEW_BENEFICIARY_INSTANT_PAYMENT, SPLIT_PAYMENTS"],
  ["Device", "NEW_DEVICE, UNUSUAL_IP_COUNTRY, REMOTE_ACCESS_FLAG"],
  ["QR", "QR_IBAN_MISMATCH, QR_TYPOSQUATTED_DOMAIN, QR_SUSPICIOUS_URL"],
  ["Graph", "GRAPH_HIGH_RISK_CLUSTER, GRAPH_MULE_LINKED_PAYERS, GRAPH_SHARED_IBAN"],
  ["AML", "SANCTIONS_POSSIBLE_HIT, PEP_POSSIBLE_HIT, HIGH_RISK_COUNTRY"],
];

export default function RiskDocsPage() {
  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Documentation produit</div>
          <h1 style={{ marginTop: 9 }}>
            Docs &amp; <span className="italic">glossaire</span>
          </h1>
          <p className="sub">
            Guide de test, API, modèle de scoring, glossaire et limites de la démonstration.
            Cette page aide un recruteur ou un évaluateur à tester l&apos;outil sans contexte préalable.
          </p>
        </div>
        <div className="fx-head-actions">
          <Link href="/risk-test-lab" className="fx-btn">
            Ouvrir le Test Lab ↗
          </Link>
          <Link href="/p2p-scenarios" className="fx-btn-ghost">
            Scénarios guidés
          </Link>
        </div>
      </div>

      <section className="grid gap-4 md:grid-cols-3" style={{ marginBottom: 20 }}>
        <QuickCard
          title="Tester en 3 minutes"
          glyph="□"
          body="Choisir un scénario, cliquer Scorer via API, ouvrir Fraud Case 360, exporter l'evidence pack."
          href="/risk-test-lab"
        />
        <QuickCard
          title="Lire le modèle"
          glyph="§"
          body="Comprendre score 0-100, niveaux de risque, décisions, typologies et reason codes."
          href="#model"
        />
        <QuickCard
          title="Voir les limites"
          glyph="▣"
          body="Données synthétiques, décision humaine, pas de détection bancaire réelle."
          href="#limits"
        />
      </section>

      <section className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]" style={{ marginBottom: 20 }}>
        <div className="fx-panel" id="model">
          <div className="fx-panel-head">
            <h2>Modèle de scoring</h2>
            <span className="glyph">◇</span>
          </div>
          <div className="fx-panel-body space-y-4">
            <p style={{ fontSize: 13, lineHeight: 1.7, color: "var(--fg-2)" }}>
              Le moteur <code className="fx-mono" style={{ fontSize: 12, color: "var(--info)" }}>risk-engine-demo-v1</code> agrège huit détecteurs déterministes.
              Chaque détecteur produit un score partiel, des signaux et des reason
              codes. Le score final est borné entre 0 et 100.
            </p>
            <div className="grid gap-3 sm:grid-cols-4">
              <ScaleBox label="LOW" value="0-24" />
              <ScaleBox label="MEDIUM" value="25-49" />
              <ScaleBox label="HIGH" value="50-74" />
              <ScaleBox label="CRITICAL" value="75-100" />
            </div>
            <div style={{ background: "var(--bg-2)", border: "1px solid var(--border)", padding: "14px 16px" }}>
              <div className="fx-eyebrow" style={{ marginBottom: 10 }}>Décisions</div>
              <div className="grid gap-2 sm:grid-cols-2">
                {["ALLOW", "MONITOR", "MANUAL_REVIEW", "BLOCK_RECOMMENDED"].map((d) => (
                  <span key={d} className="fx-mono" style={{ fontSize: 12, color: "var(--fg-2)" }}>{d}</span>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="fx-panel">
          <div className="fx-panel-head">
            <h2>API de test</h2>
            <span className="glyph">§</span>
          </div>
          <div className="fx-panel-body">
            <div className="grid gap-3">
              <EndpointRow method="POST" path="/api/risk/score" body="Score une transaction synthétique." />
              <EndpointRow method="GET" path="/api/risk/scenarios" body="Retourne les scénarios locaux ou Hugging Face." />
              <EndpointRow method="POST" path="/api/risk/cases" body="Crée un case simulé et retourne son lien." />
              <EndpointRow method="POST" path="/api/evidence/export" body="Génère JSON + HTML imprimable." />
            </div>
            <pre
              className="fx-mono"
              style={{
                marginTop: 16,
                overflow: "auto",
                background: "var(--bg)",
                border: "1px solid var(--border)",
                padding: "14px",
                fontSize: 11,
                lineHeight: 1.6,
                color: "var(--fg-2)",
              }}
            >
{`{
  "score": 91,
  "level": "CRITICAL",
  "decision": "BLOCK_RECOMMENDED",
  "typology": "APP_FRAUD_BANK_IMPERSONATION",
  "modelVersion": "risk-engine-demo-v1"
}`}
            </pre>
          </div>
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-2" style={{ marginBottom: 20 }}>
        <div className="fx-panel">
          <div className="fx-panel-head">
            <h2>Glossaire</h2>
            <span className="glyph">§</span>
          </div>
          <div className="fx-panel-body space-y-3">
            {glossary.map(([term, definition]) => (
              <div
                key={term}
                style={{ background: "var(--bg-2)", border: "1px solid var(--border)", padding: "10px 12px" }}
              >
                <div className="fx-mono" style={{ fontSize: 12, color: "var(--fg)", fontWeight: 500 }}>{term}</div>
                <p style={{ marginTop: 4, fontSize: 13, lineHeight: 1.6, color: "var(--fg-2)" }}>{definition}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="fx-panel">
          <div className="fx-panel-head">
            <h2>Familles de reason codes</h2>
            <span className="glyph">◫</span>
          </div>
          <div className="fx-panel-body space-y-3">
            {reasonFamilies.map(([family, codes]) => (
              <div
                key={family}
                style={{ background: "var(--bg-2)", border: "1px solid var(--border)", padding: "10px 12px" }}
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="fx-mono" style={{ fontSize: 12, color: "var(--fg)", fontWeight: 500 }}>{family}</div>
                  <Badge severity="neutral">demo</Badge>
                </div>
                <p className="fx-mono" style={{ marginTop: 6, fontSize: 11, lineHeight: 1.6, color: "var(--muted)" }}>{codes}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-2" style={{ marginBottom: 20 }}>
        <div className="fx-panel">
          <div className="fx-panel-head">
            <h2>Tests &amp; validation</h2>
            <span className="glyph">□</span>
          </div>
          <div className="fx-panel-body space-y-3">
            <p style={{ fontSize: 13, lineHeight: 1.7, color: "var(--fg-2)" }}>
              Parcours conseillé : choisir un scénario, lancer l&apos;analyse, ouvrir
              Fraud Case 360, ajouter une note analyste puis exporter l&apos;evidence pack.
            </p>
            <div className="grid gap-2">
              {[
                "GET /api/risk/scenarios doit retourner 6 scénarios synthétiques.",
                "POST /api/risk/score doit retourner score, décision, typologie, reason codes et détecteurs.",
                "POST /api/evidence/export doit retourner evidencePack et printableHtml.",
                "Les routes visibles ne doivent pas mener à une 404.",
              ].map((item) => (
                <div
                  key={item}
                  className="fx-mono"
                  style={{ fontSize: 11, background: "var(--bg-2)", border: "1px solid var(--border)", padding: "8px 10px", color: "var(--fg-2)", lineHeight: 1.5 }}
                >
                  {item}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="fx-panel">
          <div className="fx-panel-head">
            <h2>Configuration Hugging Face / Vercel</h2>
            <span className="glyph">✓</span>
          </div>
          <div className="fx-panel-body space-y-3">
            <p style={{ fontSize: 13, lineHeight: 1.7, color: "var(--fg-2)" }}>
              La source Hugging Face reste optionnelle. Sans variable serveur valide,
              l&apos;application affiche un fallback local explicite et ne bloque pas la démo.
            </p>
            <pre
              className="fx-mono"
              style={{
                overflow: "auto",
                background: "var(--bg)",
                border: "1px solid var(--border)",
                padding: "14px",
                fontSize: 11,
                lineHeight: 1.6,
                color: "var(--fg-2)",
              }}
            >
{`HF_SYNTHETIC_SCENARIOS_URL=https://...
HF_TOKEN=hf_... # uniquement si dataset privé`}
            </pre>
            <p style={{ fontSize: 13, lineHeight: 1.7, color: "var(--fg-2)" }}>
              Le token ne doit jamais être exposé au navigateur. Les datasets doivent
              rester synthétiques.
            </p>
          </div>
        </div>
      </section>

      <div
        id="limits"
        className="fx-card-accent"
        style={{ marginBottom: 20 }}
      >
        <div className="fx-eyebrow" style={{ marginBottom: 8 }}>⚠ Limites et gouvernance</div>
        <div className="grid gap-3 md:grid-cols-2">
          <p style={{ fontSize: 13, lineHeight: 1.7, color: "var(--fg-2)" }}>
            Données synthétiques uniquement. Aucune donnée personnelle réelle ne
            doit être saisie dans la démo publique.
          </p>
          <p style={{ fontSize: 13, lineHeight: 1.7, color: "var(--fg-2)" }}>
            Pas de décision bancaire réelle, pas de certification conformité, pas
            de fingerprinting réel, pas de dark web scraping. La décision finale
            reste humaine.
          </p>
        </div>
      </div>
    </ForensicPage>
  );
}

function QuickCard({
  title,
  body,
  glyph,
  href,
}: {
  title: string;
  body: string;
  glyph: string;
  href: string;
}) {
  const inner = (
    <>
      <span className="fx-mono" style={{ fontSize: 16, color: "var(--risk)" }}>{glyph}</span>
      <div className="fx-mono" style={{ fontSize: 13, color: "var(--fg)", marginTop: 10, fontWeight: 500 }}>{title}</div>
      <p style={{ fontSize: 13, lineHeight: 1.6, color: "var(--muted)", marginTop: 6 }}>{body}</p>
    </>
  );
  if (href.startsWith("#")) {
    return (
      <a href={href} className="fx-card" style={{ display: "block", textDecoration: "none" }}>
        {inner}
      </a>
    );
  }
  return (
    <Link href={href} className="fx-card" style={{ display: "block", textDecoration: "none" }}>
      {inner}
    </Link>
  );
}

function ScaleBox({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ background: "var(--bg-2)", border: "1px solid var(--border)", padding: "10px 12px" }}>
      <div className="fx-eyebrow">{label}</div>
      <div className="fx-mono" style={{ fontSize: 13, color: "var(--fg)", marginTop: 4, fontWeight: 500 }}>
        {value}
      </div>
    </div>
  );
}

function EndpointRow({ method, path, body }: { method: string; path: string; body: string }) {
  return (
    <div style={{ background: "var(--bg-2)", border: "1px solid var(--border)", padding: "10px 12px" }}>
      <div className="flex flex-wrap items-center gap-2">
        <Badge severity={method === "GET" ? "low" : "medium"}>{method}</Badge>
        <code className="fx-mono" style={{ fontSize: 11, color: "var(--info)" }}>{path}</code>
      </div>
      <p style={{ marginTop: 6, fontSize: 13, lineHeight: 1.6, color: "var(--fg-2)" }}>{body}</p>
    </div>
  );
}
