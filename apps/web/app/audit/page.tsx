"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { explainAudit, listAudit, verifyAudit } from "@/lib/api-client";
import type { AuditExplainResult } from "@/lib/api-client";
import { ClaimList } from "@/components/grounded-claims";
import { useLocale } from "@/components/locale-provider";
import { formatDate } from "@/lib/utils";
import { ForensicPage } from "@/components/forensic-page";
import { case360Href, getPrimaryCase360Scenario } from "@/lib/risk/case-links";

export default function AuditPage() {
  const { t } = useLocale();
  const [cursor, setCursor] = useState(0);
  const [verifyRun, setVerifyRun] = useState(false);
  const [explainRun, setExplainRun] = useState(false);
  const primaryCase = getPrimaryCase360Scenario();

  const auditQuery = useQuery({
    queryKey: ["audit", cursor],
    queryFn: () => listAudit(cursor, 50),
  });

  const verifyQuery = useQuery({
    queryKey: ["audit-verify"],
    queryFn: verifyAudit,
    enabled: verifyRun,
    staleTime: 0,
  });

  const explainQuery = useQuery({
    queryKey: ["audit-explain"],
    queryFn: explainAudit,
    enabled: explainRun,
    staleTime: 0,
    retry: false,
  });

  const entries = auditQuery.data?.entries ?? [];
  const total = auditQuery.data?.total ?? 0;
  const nextCursor = auditQuery.data?.cursor_next;

  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Investigation</div>
          <h1 style={{ marginTop: 9 }}>
            Piste d&apos;<span className="italic">audit</span>
          </h1>
          <p className="sub">
            Journal immutable hash-chaîné SHA-256 + signatures Ed25519 (P5-5).
            Vérifiable indépendamment via{" "}
            <code
              className="fx-mono"
              style={{
                background: "var(--panel-2)",
                border: "1px solid var(--border)",
                padding: "1px 6px",
                fontSize: 11,
              }}
            >
              GET /security/public-key
            </code>
            .
          </p>
        </div>
        <div className="fx-head-actions">
          <Link href={case360Href(primaryCase.caseId)} className="fx-btn">
            Ouvrir Case 360 <span>↗</span>
          </Link>
        </div>
      </div>

      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <div>
            <h2>Vérification d&apos;intégrité</h2>
            <div className="sub">SHA-256 + Ed25519</div>
          </div>
          <span className="glyph">§</span>
        </div>
        <div
          className="fx-panel-body"
          data-testid="audit-verify-panel"
          style={{ display: "flex", flexWrap: "wrap", gap: 16, alignItems: "flex-start" }}
        >
          <button
            className="fx-btn"
            data-testid="audit-verify-button"
            onClick={() => setVerifyRun(true)}
            disabled={verifyQuery.isFetching}
            type="button"
          >
            {verifyQuery.isFetching ? "◷ Vérification…" : "↻ Recalculer la chaîne"}
          </button>
          {verifyQuery.data ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  color: verifyQuery.data.valid
                    ? "var(--verified)"
                    : "var(--risk)",
                  fontFamily: "var(--font-mono)",
                  fontSize: 13,
                }}
              >
                <span>{verifyQuery.data.valid ? "✓" : "⚠"}</span>
                <span>
                  {verifyQuery.data.valid
                    ? "Chaîne valide"
                    : `Séquences invalides : ${(verifyQuery.data.invalid_seqs ?? []).join(", ")}`}
                </span>
              </div>
              <div
                className="fx-mono"
                style={{ fontSize: 11, color: "var(--muted)" }}
              >
                {verifyQuery.data.n_total} entrées · {verifyQuery.data.n_signed}{" "}
                signées Ed25519
              </div>
              {verifyQuery.data.public_key_b64 ? (
                <div
                  className="fx-mono"
                  style={{ fontSize: 10, color: "var(--dim)" }}
                >
                  Clé publique :{" "}
                  {verifyQuery.data.public_key_b64.slice(0, 24)}…
                  {verifyQuery.data.public_key_b64.slice(-8)}
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>

      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <div>
            <h2>{t("audit_ai.title")}</h2>
            <div className="sub">{t("audit_ai.subtitle")}</div>
          </div>
          <span className="glyph">¶</span>
        </div>
        <div className="fx-panel-body" data-testid="audit-explain-panel">
          <button
            className="fx-btn"
            data-testid="audit-explain-button"
            onClick={() => setExplainRun(true)}
            disabled={explainQuery.isFetching}
            type="button"
          >
            {explainQuery.isFetching ? t("ai.generating") : t("audit_ai.explain")}
          </button>
          {explainQuery.error ? (
            <div className="fx-notice" style={{ marginTop: 14 }}>
              <span className="glyph">⚠</span>
              <div>
                <div className="nt">{t("ai.unavailable_title")}</div>
                <p className="nb">{t("audit_ai.unavailable_body")}</p>
              </div>
            </div>
          ) : null}
          {explainQuery.data ? (
            <ExplanationView result={explainQuery.data} />
          ) : null}
        </div>
      </div>

      <div className="fx-panel">
        <div className="fx-panel-head">
          <div>
            <h2>Entrées</h2>
            <div className="sub">
              {entries.length} / {total}
            </div>
          </div>
          <span className="glyph">▣</span>
        </div>
        {auditQuery.isLoading ? (
          <div className="fx-panel-body">
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((k) => (
                <div key={k} className="fx-skel" style={{ height: 44 }} />
              ))}
            </div>
          </div>
        ) : auditQuery.error ? (
          <div className="fx-panel-body">
            <div className="fx-notice">
              <span className="glyph">⚠</span>
              <div>
                <div className="nt">API indisponible</div>
                <p className="nb">
                  {(auditQuery.error as Error).message}
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="fx-table-wrap">
            <table data-testid="audit-table" className="fx-table">
              <thead>
                <tr>
                  <th>Seq</th>
                  <th>Quand</th>
                  <th>Acteur</th>
                  <th>Type</th>
                  <th>Hash (8)</th>
                  <th>Signature</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((e: import("@p2pfd/shared-types").AuditEntryOut) => (
                  <tr key={e.seq}>
                    <td className="key">{e.seq}</td>
                    <td style={{ color: "var(--muted)" }}>{formatDate(e.at)}</td>
                    <td>{e.actor}</td>
                    <td>{e.kind}</td>
                    <td>{e.hash.slice(0, 8)}…</td>
                    <td>
                      {e.signature ? (
                        <span style={{ color: "var(--verified)" }}>✓</span>
                      ) : (
                        <span style={{ color: "var(--dim)" }}>—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div
          className="fx-panel-body"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            borderTop: "1px solid var(--border)",
          }}
        >
          <div className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>
            Cursor : {cursor} · Suivant : {nextCursor ?? "—"}
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              className="fx-btn-ghost sm"
              onClick={() => setCursor(Math.max(0, cursor - 50))}
              disabled={cursor === 0}
              type="button"
            >
              ← Précédent
            </button>
            <button
              className="fx-btn-ghost sm"
              onClick={() => nextCursor && setCursor(nextCursor)}
              disabled={!nextCursor}
              type="button"
            >
              Suivant →
            </button>
          </div>
        </div>
      </div>
    </ForensicPage>
  );
}

function ExplanationView({ result }: { result: AuditExplainResult }) {
  const { t } = useLocale();
  const broken = result.chain_status === "broken";
  const statusColor = broken ? "var(--risk)" : "var(--verified)";
  return (
    <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 14 }}>
      <div
        style={{
          background: "var(--bg-2)",
          border: "1px solid var(--border)",
          borderLeft: `3px solid ${statusColor}`,
          padding: "12px 14px",
        }}
      >
        <div className="fx-eyebrow" style={{ color: statusColor }}>
          {broken
            ? t("audit_ai.broken")
            : result.chain_status === "empty"
              ? t("audit_ai.empty")
              : t("audit_ai.intact")}
        </div>
        <p style={{ margin: "6px 0 0", fontSize: 14, lineHeight: 1.6, color: "var(--fg)" }}>
          {result.explanation.headline}
        </p>
      </div>

      {result.explanation.human_review_required ? (
        <div className="fx-notice">
          <span className="glyph">★</span>
          <div>
            <div className="nt">{t("ai.human_review_title")}</div>
            <p className="nb">{t("audit_ai.review_body")}</p>
          </div>
        </div>
      ) : null}

      <div>
        <div className="fx-eyebrow" style={{ marginBottom: 8 }}>{t("audit_ai.explanation")}</div>
        <ClaimList claims={result.explanation.explanation} />
      </div>

      {result.explanation.audit_implications.length ? (
        <div>
          <div className="fx-eyebrow" style={{ marginBottom: 8 }}>{t("audit_ai.implications")}</div>
          <ClaimList claims={result.explanation.audit_implications} />
        </div>
      ) : null}

      {result.explanation.recommended_next_actions.length ? (
        <div>
          <div className="fx-eyebrow" style={{ marginBottom: 8 }}>{t("ai.recommended_actions")}</div>
          <ul style={{ margin: 0, paddingLeft: 18 }} className="space-y-1">
            {result.explanation.recommended_next_actions.map((action) => (
              <li key={action} style={{ fontSize: 13, lineHeight: 1.6, color: "var(--fg-2)" }}>
                {action}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {result.explanation.missing_evidence.length ? (
        <div>
          <div className="fx-eyebrow" style={{ marginBottom: 8, color: "var(--warn)" }}>
            {t("ai.missing_evidence")}
          </div>
          <ul style={{ margin: 0, paddingLeft: 18 }} className="space-y-1">
            {result.explanation.missing_evidence.map((item) => (
              <li key={item} style={{ fontSize: 13, lineHeight: 1.6, color: "var(--muted)" }}>
                {item}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="fx-mono" style={{ fontSize: 10, color: "var(--dim)" }}>
        {t("audit_ai.footer", {
          model: result.model,
          promptVersion: result.prompt_version,
          nTotal: result.n_total,
          nSigned: result.n_signed,
        })}
      </div>
    </div>
  );
}
