"use client";

import { useMutation } from "@tanstack/react-query";
import { generateCase360 } from "@/lib/api-client";
import type { Case360Result } from "@/lib/api-client";
import { ClaimList, SourceChips } from "@/components/grounded-claims";
import { SeverityBadge } from "@/components/ui/badge";
import { useLocale } from "@/components/locale-provider";

/**
 * Panneau « Dossier IA » (Fraud Case 360 AI, Phase 3 ADR-0007).
 *
 * Génère un dossier d'enquête structuré et sourcé pour un cas backend réel.
 * La provenance des faits est validée côté serveur ; la revue humaine est
 * toujours requise (forcée en code) — aucun bouton de décision ici.
 */
export function Case360DossierPanel({ caseId }: { caseId: string | null }) {
  const { t } = useLocale();
  const mutation = useMutation({
    mutationFn: (id: string) => generateCase360(id),
  });

  return (
    <div className="fx-panel" style={{ marginTop: 16 }} data-testid="case360-dossier-panel">
      <div className="fx-panel-head">
        <div>
          <h2>{t("case360.title")}</h2>
          <div className="sub">{t("case360.subtitle")}</div>
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
            {mutation.isPending ? t("ai.generating") : t("case360.generate")}
          </button>
          <span className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>
            {caseId ? t("ai.case_selected", { caseId }) : t("ai.select_one_case")}
          </span>
        </div>

        {mutation.error ? (
          <div className="fx-notice" style={{ marginTop: 14 }}>
            <span className="glyph">⚠</span>
            <div>
              <div className="nt">{t("ai.unavailable_title")}</div>
              <p className="nb">{t("ai.unavailable_body")}</p>
            </div>
          </div>
        ) : null}

        {mutation.data ? <DossierView result={mutation.data} /> : null}
      </div>
    </div>
  );
}

function DossierView({ result }: { result: Case360Result }) {
  const { t } = useLocale();
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
          <div className="fx-eyebrow">{t("case360.exec_summary")}</div>
          <SeverityBadge value={dossier.severity_assessment} />
        </div>
        <p style={{ margin: "8px 0 0", fontSize: 14, lineHeight: 1.65, color: "var(--fg)" }}>
          {dossier.executive_summary}
        </p>
      </div>

      <div className="fx-notice">
        <span className="glyph">★</span>
        <div>
          <div className="nt">{t("ai.human_review_title")}</div>
          <p className="nb">{t("case360.review_body")}</p>
        </div>
      </div>

      <div>
        <div className="fx-eyebrow" style={{ marginBottom: 8 }}>{t("case360.verified_facts")}</div>
        <ClaimList claims={dossier.verified_facts} />
      </div>

      {dossier.risk_signals.length ? (
        <div>
          <div className="fx-eyebrow" style={{ marginBottom: 8 }}>{t("case360.risk_signals")}</div>
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
          title={t("case360.contradictions")}
          items={dossier.contradictions}
          color="var(--risk)"
        />
      ) : null}

      {dossier.missing_evidence.length ? (
        <BulletSection
          title={t("ai.missing_evidence")}
          items={dossier.missing_evidence}
          color="var(--warn)"
        />
      ) : null}

      {dossier.open_questions.length ? (
        <BulletSection title={t("case360.open_questions")} items={dossier.open_questions} />
      ) : null}

      {dossier.recommended_next_actions.length ? (
        <BulletSection
          title={t("ai.recommended_actions")}
          items={dossier.recommended_next_actions}
        />
      ) : null}

      <div className="fx-mono" style={{ fontSize: 10, color: "var(--dim)" }}>
        {t("ai.generated_by", { model: result.model, promptVersion: result.prompt_version })}
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
