"use client";

import { useMutation } from "@tanstack/react-query";
import { generateCase360 } from "@/lib/api-client";
import type { Case360Result } from "@/lib/api-client";
import { ClaimList, SourceChips } from "@/components/grounded-claims";
import { SeverityBadge } from "@/components/ui/badge";

/**
 * Panneau « Dossier IA » (Fraud Case 360 AI, Phase 3 ADR-0007).
 *
 * Génère un dossier d'enquête structuré et sourcé pour un cas backend réel.
 * La provenance des faits est validée côté serveur ; la revue humaine est
 * toujours requise (forcée en code) — aucun bouton de décision ici.
 */
export function Case360DossierPanel({ caseId }: { caseId: string | null }) {
  const mutation = useMutation({
    mutationFn: (id: string) => generateCase360(id),
  });

  return (
    <div className="fx-panel" style={{ marginTop: 16 }} data-testid="case360-dossier-panel">
      <div className="fx-panel-head">
        <div>
          <h2>Dossier IA — Fraud Case 360</h2>
          <div className="sub">
            Faits sourcés depuis le cas et son workflow · provenance validée en
            code · revue humaine toujours requise
          </div>
        </div>
        <span className="glyph">◎</span>
      </div>
      <div className="fx-panel-body">
        <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <button
            className="fx-btn"
            data-testid="case360-generate-button"
            type="button"
            disabled={!caseId || mutation.isPending}
            onClick={() => caseId && mutation.mutate(caseId)}
          >
            {mutation.isPending ? "◷ Génération…" : "◎ Générer le dossier d'enquête"}
          </button>
          <span className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>
            {caseId
              ? `Cas sélectionné : ${caseId}`
              : "Sélectionnez exactement un cas dans la table."}
          </span>
        </div>

        {mutation.error ? (
          <div className="fx-notice" style={{ marginTop: 14 }}>
            <span className="glyph">⚠</span>
            <div>
              <div className="nt">Génération indisponible</div>
              <p className="nb">
                Le backend FastAPI (et sa clé ANTHROPIC_API_KEY) doit être
                configuré. Le case management reste pleinement fonctionnel sans IA.
              </p>
            </div>
          </div>
        ) : null}

        {mutation.data ? <DossierView result={mutation.data} /> : null}
      </div>
    </div>
  );
}

function DossierView({ result }: { result: Case360Result }) {
  const dossier = result.dossier;
  return (
    <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 14 }}>
      <div
        style={{
          background: "var(--bg-2)",
          border: "1px solid var(--border)",
          borderLeft: "3px solid var(--risk)",
          padding: "12px 14px",
        }}
      >
        <div className="flex items-center justify-between gap-3">
          <div className="fx-eyebrow">Synthèse exécutive</div>
          <SeverityBadge value={dossier.severity_assessment} />
        </div>
        <p style={{ margin: "8px 0 0", fontSize: 14, lineHeight: 1.65, color: "var(--fg)" }}>
          {dossier.executive_summary}
        </p>
      </div>

      <div className="fx-notice">
        <span className="glyph">★</span>
        <div>
          <div className="nt">Revue humaine requise</div>
          <p className="nb">
            Ce dossier est une aide à l&apos;instruction. Aucune décision
            (blocage, clôture) n&apos;est prise automatiquement.
          </p>
        </div>
      </div>

      <div>
        <div className="fx-eyebrow" style={{ marginBottom: 8 }}>Faits vérifiés</div>
        <ClaimList claims={dossier.verified_facts} />
      </div>

      {dossier.risk_signals.length ? (
        <div>
          <div className="fx-eyebrow" style={{ marginBottom: 8 }}>Signaux de risque</div>
          <div className="space-y-2">
            {dossier.risk_signals.map((signal) => (
              <div
                key={`${signal.rule_id}-${signal.text}`}
                style={{
                  background: "var(--bg-2)",
                  border: "1px solid var(--border)",
                  padding: "10px 12px",
                }}
              >
                <div className="flex items-center justify-between gap-2">
                  <code className="fx-mono" style={{ fontSize: 11, color: "var(--info)" }}>
                    {signal.rule_id}
                  </code>
                  <SeverityBadge value={signal.severity} />
                </div>
                <p style={{ margin: "6px 0 0", fontSize: 13, lineHeight: 1.6, color: "var(--fg-2)" }}>
                  {signal.text}
                  <SourceChips sourceIds={signal.source_ids} />
                </p>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {dossier.contradictions.length ? (
        <BulletSection
          title="Contradictions"
          items={dossier.contradictions}
          color="var(--risk)"
        />
      ) : null}

      {dossier.missing_evidence.length ? (
        <BulletSection
          title="Données manquantes"
          items={dossier.missing_evidence}
          color="var(--warn)"
        />
      ) : null}

      {dossier.open_questions.length ? (
        <BulletSection title="Questions ouvertes" items={dossier.open_questions} />
      ) : null}

      {dossier.recommended_next_actions.length ? (
        <BulletSection
          title="Diligences recommandées"
          items={dossier.recommended_next_actions}
        />
      ) : null}

      <div className="fx-mono" style={{ fontSize: 10, color: "var(--dim)" }}>
        Généré par {result.model} · prompt {result.prompt_version} · journalisé au
        ledger ai.generation
      </div>
    </div>
  );
}

function BulletSection({
  title,
  items,
  color,
}: {
  title: string;
  items: string[];
  color?: string;
}) {
  return (
    <div>
      <div className="fx-eyebrow" style={{ marginBottom: 8, color: color ?? undefined }}>
        {title}
      </div>
      <ul style={{ margin: 0, paddingLeft: 18 }} className="space-y-1">
        {items.map((item) => (
          <li key={item} style={{ fontSize: 13, lineHeight: 1.6, color: "var(--fg-2)" }}>
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
