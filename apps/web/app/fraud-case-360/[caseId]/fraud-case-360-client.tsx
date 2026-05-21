"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import type { EvidencePack, RiskScenario, RiskScoreResult } from "@/types/risk";
import { Button } from "@/components/ui/button";
import { Badge, SeverityBadge } from "@/components/ui/badge";
import { formatEur } from "@/lib/utils";
import { ForensicPage } from "@/components/forensic-page";
import { maskSensitiveValue } from "@/lib/risk/evidence-redaction";

type AnalystAction =
  | "assign"
  | "review"
  | "escalate"
  | "false_positive"
  | "block_recommended"
  | "export_evidence";

const ACTION_LABELS: Record<AnalystAction, string> = {
  assign: "Assigner",
  review: "Mettre en revue",
  escalate: "Escalader",
  false_positive: "Marquer faux positif",
  block_recommended: "Recommander blocage",
  export_evidence: "Exporter evidence pack",
};

export function FraudCase360Client({
  scenario,
  score,
}: {
  scenario: RiskScenario;
  score: RiskScoreResult;
}) {
  const storageKey = `p2pfd.case360.${scenario.caseId}`;
  const [assignee, setAssignee] = useState("analyst-demo@p2pfd.local");
  const [notes, setNotes] = useState("");
  const [auditTrail, setAuditTrail] = useState<
    { at: string; actor: string; action: string; detail: string }[]
  >([]);
  const [evidence, setEvidence] = useState<EvidencePack | null>(null);
  const [exportStatus, setExportStatus] = useState<string | null>(null);

  useEffect(() => {
    const raw = window.localStorage.getItem(storageKey);
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw) as {
        assignee?: string;
        notes?: string;
        auditTrail?: { at: string; actor: string; action: string; detail: string }[];
      };
      if (parsed.assignee) setAssignee(parsed.assignee);
      if (parsed.notes) setNotes(parsed.notes);
      if (Array.isArray(parsed.auditTrail)) setAuditTrail(parsed.auditTrail);
    } catch {
      window.localStorage.removeItem(storageKey);
    }
  }, [storageKey]);

  useEffect(() => {
    window.localStorage.setItem(
      storageKey,
      JSON.stringify({ assignee, notes, auditTrail }),
    );
  }, [assignee, auditTrail, notes, storageKey]);

  const timeline = useMemo(
    () => [
      {
        at: scenario.transaction.createdAt,
        actor: "payment-workbench",
        event: "Transaction chargée",
        detail: scenario.description,
      },
      {
        at: score.generatedAt,
        actor: score.modelVersion,
        event: "Score calculé",
        detail: `${score.score}/100 · ${score.level} · ${score.decision}`,
      },
      ...auditTrail.map((item) => ({
        at: item.at,
        actor: item.actor,
        event: item.action,
        detail: item.detail,
      })),
    ],
    [auditTrail, scenario.description, scenario.transaction.createdAt, score],
  );

  function record(action: AnalystAction) {
    const entry = {
      at: new Date().toISOString(),
      actor: assignee || "demo-analyst",
      action,
      detail: ACTION_LABELS[action],
    };
    setAuditTrail((previous) => [entry, ...previous]);
    return entry;
  }

  async function exportEvidence() {
    const exportEntry = record("export_evidence");
    setExportStatus("Génération de l'evidence pack en cours...");
    const response = await fetch("/api/evidence/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        caseId: scenario.caseId,
        transaction: scenario.transaction,
        analystNotes: notes,
        auditTrail: [exportEntry, ...auditTrail],
        timeline,
      }),
    });
    if (!response.ok) {
      setExportStatus("Export impossible pour le moment.");
      return;
    }
    const payload = (await response.json()) as {
      evidencePack: EvidencePack;
      printableHtml: string;
    };
    setEvidence(payload.evidencePack);

    const blob = new Blob([JSON.stringify(payload.evidencePack, null, 2)], {
      type: "application/json",
    });
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${scenario.caseId}-evidence-pack.json`;
    anchor.click();
    window.URL.revokeObjectURL(url);
    setExportStatus(`Evidence pack JSON généré pour ${scenario.caseId}.`);
  }

  return (
    <ForensicPage>
      <Link href="/p2p-scenarios" className="fx-link" style={{ marginBottom: 18, display: "inline-flex" }}>
        ← Retour aux scénarios
      </Link>

      <div className="mt-4 grid gap-5 lg:grid-cols-[1fr_360px]">
        <div
          className="fx-panel"
          style={{ overflow: "hidden" }}
        >
          <div
            className="fx-panel-head"
            style={{ background: "var(--bg)", borderBottom: "1px solid var(--border-strong)", padding: "22px 24px" }}
          >
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between w-full">
              <div>
                <div className="fx-eyebrow">Fraud Case 360</div>
                <h1
                  style={{
                    fontFamily: "var(--font-display)",
                    fontSize: "clamp(24px, 2.5vw, 36px)",
                    fontWeight: 400,
                    letterSpacing: "-0.015em",
                    lineHeight: 1.04,
                    color: "var(--fg)",
                    margin: "10px 0 8px",
                  }}
                >
                  {scenario.title}
                </h1>
                <p
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: 12,
                    lineHeight: 1.65,
                    color: "var(--muted)",
                    maxWidth: 600,
                  }}
                >
                  {scenario.businessContext}
                </p>
              </div>
              <SeverityBadge value={score.level} />
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <Link href="/rings" className="fx-btn-ghost sm">
                Graphe rings <span>↗</span>
              </Link>
              <Link href="/audit" className="fx-btn-ghost sm">
                Piste audit <span>↗</span>
              </Link>
              <Link href="/exports" className="fx-btn-ghost sm">
                Exports <span>↗</span>
              </Link>
            </div>
          </div>
          <div className="fx-panel-body">
            <div className="grid gap-3 sm:grid-cols-4">
              <Kpi label="Score" value={`${score.score}/100`} />
              <Kpi label="Décision" value={score.decision} />
              <Kpi label="Typologie" value={score.typology} />
              <Kpi label="Montant" value={formatEur(scenario.transaction.amount)} />
            </div>
          </div>
        </div>

        <div className="fx-panel">
          <div className="fx-panel-head">
            <h2>Analyst Action Bar</h2>
            <span className="glyph">▣</span>
          </div>
          <div className="fx-panel-body space-y-3">
            <label
              htmlFor="case-360-assignee"
              className="fx-eyebrow"
              style={{ display: "block", marginBottom: 6 }}
            >
              Assigné à
            </label>
            <input
              id="case-360-assignee"
              value={assignee}
              onChange={(event) => setAssignee(event.target.value)}
              style={{
                height: 38,
                width: "100%",
                background: "var(--bg)",
                border: "1px solid var(--border)",
                padding: "0 12px",
                fontFamily: "var(--font-mono)",
                fontSize: 12,
                color: "var(--fg)",
                outline: "none",
              }}
            />
            <div className="grid grid-cols-2 gap-2">
              <Button type="button" size="sm" variant="outline" onClick={() => record("assign")}>
                Assigner
              </Button>
              <Button type="button" size="sm" variant="outline" onClick={() => record("review")}>
                Revue
              </Button>
              <Button type="button" size="sm" variant="outline" onClick={() => record("escalate")}>
                Escalader
              </Button>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => record("false_positive")}
              >
                Faux positif
              </Button>
            </div>
            <Button type="button" className="w-full" onClick={() => record("block_recommended")}>
              Recommander blocage
            </Button>
            <Button type="button" variant="secondary" className="w-full" onClick={exportEvidence}>
              ↓ Exporter evidence pack
            </Button>
            {exportStatus ? (
              <div
                role="status"
                style={{
                  background: "var(--panel-2)",
                  border: "1px solid var(--border-strong)",
                  padding: "12px 14px",
                  fontFamily: "var(--font-mono)",
                  fontSize: 12,
                  color: "var(--fg)",
                }}
              >
                {exportStatus}
              </div>
            ) : null}
          </div>
        </div>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="fx-panel">
          <div className="fx-panel-head">
            <h2>Transaction details</h2>
            <span className="glyph">§</span>
          </div>
          <div className="fx-panel-body">
            <dl className="grid gap-3 sm:grid-cols-2">
              <Detail label="Transaction" value={scenario.transaction.transactionId} />
              <Detail label="Rail" value={scenario.transaction.rail} />
              <Detail label="Payeur" value={scenario.transaction.payer.displayName} />
              <Detail label="Bénéficiaire" value={scenario.transaction.beneficiary.name} />
              <Detail label="IBAN" value={maskSensitiveValue(scenario.transaction.beneficiary.iban)} />
              <Detail label="Canal" value={scenario.transaction.channel ?? "n/a"} />
            </dl>
          </div>
        </div>

        <div className="fx-panel">
          <div className="fx-panel-head">
            <h2>Timeline</h2>
            <span className="glyph">◷</span>
          </div>
          <div className="fx-panel-body space-y-3">
            {timeline.map((item) => (
              <div
                key={`${item.at}-${item.event}-${item.detail}`}
                style={{
                  background: "var(--bg-2)",
                  border: "1px solid var(--border)",
                  padding: "12px 14px",
                }}
              >
                <div
                  className="fx-mono"
                  style={{ fontSize: 10, color: "var(--muted)", marginBottom: 4 }}
                >
                  ◷ {new Date(item.at).toLocaleString("fr-FR")} · {item.actor}
                </div>
                <div style={{ fontSize: 13, fontWeight: 600, color: "var(--fg)" }}>
                  {item.event}
                </div>
                <p
                  className="fx-mono"
                  style={{ marginTop: 4, fontSize: 11, lineHeight: 1.6, color: "var(--muted)" }}
                >
                  {item.detail}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <ReasonCodesPanel score={score} />
        <BeneficiaryTrustPanel score={score} />
        <DetectorPanel
          glyph="⚠"
          title="Scam Narrative Panel"
          detector="scamNarrative"
          score={score}
        />
        <DetectorPanel glyph="∿" title="Velocity Signals Panel" detector="velocity" score={score} />
        <DetectorPanel glyph="□" title="Device Risk Panel" detector="deviceSession" score={score} />
        {scenario.transaction.qr ? (
          <DetectorPanel glyph="▦" title="QR Analyzer Panel" detector="qrRisk" score={score} />
        ) : null}
        <FraudGraphPanel scenario={scenario} />
        <AuditChainPanel evidence={evidence} auditTrail={auditTrail} />
        <EvidencePanel evidence={evidence} notes={notes} setNotes={setNotes} />
      </div>
    </ForensicPage>
  );
}

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        background: "var(--bg-2)",
        border: "1px solid var(--border)",
        padding: "12px 14px",
      }}
    >
      <div className="fx-eyebrow">{label}</div>
      <div
        className="fx-mono"
        style={{ marginTop: 6, fontSize: 13, fontWeight: 600, color: "var(--fg)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
      >
        {value}
      </div>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="fx-eyebrow">{label}</dt>
      <dd
        className="fx-mono"
        style={{ marginTop: 6, fontSize: 13, color: "var(--fg)", wordBreak: "break-word" }}
      >
        {value}
      </dd>
    </div>
  );
}

function ReasonCodesPanel({ score }: { score: RiskScoreResult }) {
  return (
    <div className="fx-panel">
      <div className="fx-panel-head">
        <h2>Reason codes cliquables</h2>
        <span className="glyph">§</span>
      </div>
      <div className="fx-panel-body space-y-2">
        {score.reasonCodes.map((reasonCode) => (
          <details
            key={`${reasonCode.detector}-${reasonCode.code}`}
            style={{
              background: "var(--bg-2)",
              border: "1px solid var(--border)",
              padding: "12px 14px",
            }}
          >
            <summary
              style={{ cursor: "pointer", listStyle: "none" }}
            >
              <span className="fx-link" style={{ marginRight: 8 }}>
                {reasonCode.code}
              </span>
              <span style={{ fontSize: 13, fontWeight: 600, color: "var(--fg)" }}>
                {reasonCode.label}
              </span>
            </summary>
            <p
              className="fx-mono"
              style={{ marginTop: 8, fontSize: 11, lineHeight: 1.65, color: "var(--muted)" }}
            >
              {reasonCode.description}
            </p>
          </details>
        ))}
      </div>
    </div>
  );
}

function BeneficiaryTrustPanel({ score }: { score: RiskScoreResult }) {
  return (
    <DetectorPanel
      glyph="★"
      title="Beneficiary Trust Card"
      detector="beneficiaryTrust"
      score={score}
    />
  );
}

function DetectorPanel({
  glyph,
  title,
  detector,
  score,
}: {
  glyph: string;
  title: string;
  detector: RiskScoreResult["detectorScores"][number]["detector"];
  score: RiskScoreResult;
}) {
  const detectorScore = score.detectorScores.find((item) => item.detector === detector);
  return (
    <div className="fx-panel">
      <div className="fx-panel-head">
        <div className="flex items-center gap-2">
          <span className="glyph">{glyph}</span>
          <h2>{title}</h2>
        </div>
        {detectorScore ? <Badge>{detectorScore.status}</Badge> : null}
      </div>
      <div className="fx-panel-body">
        {detectorScore ? (
          <>
            <div
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 32,
                fontWeight: 400,
                color: "var(--fg)",
                marginBottom: 8,
              }}
            >
              {detectorScore.score}/{detectorScore.maxScore}
            </div>
            <p
              className="fx-mono"
              style={{ fontSize: 12, lineHeight: 1.65, color: "var(--muted)" }}
            >
              {detectorScore.explanation}
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {detectorScore.reasonCodes.map((item) => (
                <Badge
                  key={item.code}
                  severity={item.severity.toLowerCase() as "critical" | "high" | "medium" | "low"}
                >
                  {item.code}
                </Badge>
              ))}
              {!detectorScore.reasonCodes.length ? <Badge severity="low">Aucun signal</Badge> : null}
            </div>
          </>
        ) : (
          <span className="fx-mono" style={{ fontSize: 12, color: "var(--muted)" }}>
            Module non exécuté.
          </span>
        )}
      </div>
    </div>
  );
}

function FraudGraphPanel({ scenario }: { scenario: RiskScenario }) {
  return (
    <div className="fx-panel">
      <div className="fx-panel-head">
        <div className="flex items-center gap-2">
          <span className="glyph">◫</span>
          <h2>Fraud Graph Panel</h2>
        </div>
      </div>
      <div className="fx-panel-body">
        <p
          className="fx-mono"
          style={{ fontSize: 12, lineHeight: 1.6, color: "var(--muted)", marginBottom: 12 }}
        >
          {scenario.graphSummary.suspiciousPath}
        </p>
        <div className="grid gap-2">
          {scenario.graphSummary.nodes.map((node) => (
            <div
              key={node.id}
              className="flex items-center justify-between"
              style={{
                background: "var(--bg-2)",
                border: "1px solid var(--border)",
                padding: "12px 14px",
              }}
            >
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: "var(--fg)" }}>
                  {node.label}
                </div>
                <div className="fx-mono" style={{ fontSize: 11, color: "var(--muted)", marginTop: 2 }}>
                  {node.kind}
                </div>
              </div>
              {node.risk ? <SeverityBadge value={node.risk} /> : null}
            </div>
          ))}
        </div>
        <div
          className="fx-mono"
          style={{
            marginTop: 12,
            background: "var(--bg)",
            border: "1px solid var(--border-strong)",
            padding: "12px 14px",
            fontSize: 12,
            color: "var(--fg-2)",
          }}
        >
          Score graphe: {scenario.graphSummary.graphScore}/100 · Clusters:{" "}
          {scenario.graphSummary.clusters.join(", ")}
        </div>
      </div>
    </div>
  );
}

function AuditChainPanel({
  evidence,
  auditTrail,
}: {
  evidence: EvidencePack | null;
  auditTrail: { at: string; actor: string; action: string; detail: string }[];
}) {
  const visibleEntries = evidence?.auditTrail ?? auditTrail;
  return (
    <div className="fx-panel">
      <div className="fx-panel-head">
        <div className="flex items-center gap-2">
          <span className="glyph">§</span>
          <h2>Audit Chain Panel</h2>
        </div>
      </div>
      <div className="fx-panel-body space-y-3">
        <div className="grid gap-3 sm:grid-cols-3">
          <Kpi label="État" value={evidence?.integrity.chainValid ? "Vérifié" : "En attente"} />
          <Kpi label="Entrées" value={`${visibleEntries.length}`} />
          <Kpi label="Signées" value={`${evidence?.integrity.signedEntries ?? 0}`} />
        </div>
        {evidence ? (
          <div
            className="fx-mono"
            style={{
              background: "var(--bg)",
              border: "1px solid var(--border-strong)",
              color: "var(--fg-2)",
              fontSize: 11,
              padding: "12px 14px",
              wordBreak: "break-all",
            }}
          >
            Root hash · {evidence.integrity.rootHash}
          </div>
        ) : (
          <p className="fx-mono" style={{ fontSize: 12, lineHeight: 1.65, color: "var(--muted)" }}>
            Les actions analyste sont horodatées localement. L’export Evidence Pack les transforme en
            chaîne SHA-256 vérifiable.
          </p>
        )}
        <div className="space-y-2">
          {visibleEntries.slice(0, 4).map((entry) => (
            <div
              key={`${entry.at}-${entry.action}-${entry.detail}`}
              style={{
                background: "var(--bg-2)",
                border: "1px solid var(--border)",
                padding: "10px 12px",
              }}
            >
              <div className="fx-mono" style={{ fontSize: 11, color: "var(--fg)" }}>
                {entry.action}
              </div>
              <div className="fx-mono" style={{ marginTop: 4, fontSize: 10, color: "var(--muted)" }}>
                {entry.actor} · {new Date(entry.at).toLocaleString("fr-FR")}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function EvidencePanel({
  evidence,
  notes,
  setNotes,
}: {
  evidence: EvidencePack | null;
  notes: string;
  setNotes: (value: string) => void;
}) {
  return (
    <div className="fx-panel">
      <div className="fx-panel-head">
        <div className="flex items-center gap-2">
          <span className="glyph">□</span>
          <h2>Evidence Pack Panel</h2>
        </div>
      </div>
      <div className="fx-panel-body space-y-3">
        <label
          htmlFor="case-360-analyst-notes"
          className="fx-eyebrow"
          style={{ display: "block", marginBottom: 6 }}
        >
          Notes analyste
        </label>
        <textarea
          id="case-360-analyst-notes"
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          rows={5}
          placeholder="Notes analyste synthétiques..."
          style={{
            width: "100%",
            background: "var(--bg)",
            border: "1px solid var(--border)",
            padding: "10px 12px",
            fontFamily: "var(--font-mono)",
            fontSize: 12,
            color: "var(--fg)",
            outline: "none",
            resize: "vertical",
          }}
        />
        {evidence ? (
          <>
            <div className="grid gap-3 sm:grid-cols-2">
              <Kpi label="Sources" value={`${evidence.sourceRefs.length}`} />
              <Kpi label="Root hash" value={evidence.integrity.rootHash.slice(0, 12)} />
            </div>
            <div className="space-y-2">
              {evidence.sourceRefs.map((source) => (
                <div
                  key={source.id}
                  style={{
                    background: "var(--bg-2)",
                    border: "1px solid var(--border)",
                    padding: "10px 12px",
                  }}
                >
                  <div className="fx-mono" style={{ fontSize: 11, color: "var(--fg)" }}>
                    {source.label}
                  </div>
                  <p className="fx-mono" style={{ marginTop: 4, fontSize: 10, lineHeight: 1.5, color: "var(--muted)" }}>
                    {source.claim}
                  </p>
                </div>
              ))}
            </div>
            <pre
              style={{
                maxHeight: 288,
                overflowY: "auto",
                background: "var(--bg)",
                border: "1px solid var(--border-strong)",
                padding: "14px 16px",
                fontSize: 11,
                lineHeight: 1.6,
                color: "var(--fg-2)",
                fontFamily: "var(--font-mono)",
                whiteSpace: "pre-wrap",
                wordBreak: "break-all",
              }}
            >
              {JSON.stringify(evidence, null, 2)}
            </pre>
          </>
        ) : (
          <p
            className="fx-mono"
            style={{ fontSize: 12, lineHeight: 1.65, color: "var(--muted)" }}
          >
            Exportez le dossier pour générer un JSON incluant transaction, score, reason codes,
            graphe, timeline, notes et audit trail.
          </p>
        )}
      </div>
    </div>
  );
}
