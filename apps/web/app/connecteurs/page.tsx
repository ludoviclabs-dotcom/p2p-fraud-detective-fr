"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { ForensicPage } from "@/components/forensic-page";
import {
  listConnectors,
  vopPrecheck,
  type ConnectorOut,
  type VopPrecheckOut,
} from "@/lib/api-client";
import { CONNECTOR_CATEGORIES, mergeConnectors } from "@/data/connectors";
import { simulateVopPrecheck } from "@/lib/vop-sim";

const STATUS_LABEL: Record<ConnectorOut["status"], string> = {
  actif: "ACTIF",
  disponible: "DISPONIBLE",
  config_requise: "CONFIG REQUISE",
  en_attente_api: "EN ATTENTE API",
  roadmap: "ROADMAP",
};

const STATUS_COLOR: Record<ConnectorOut["status"], string> = {
  actif: "var(--ok)",
  disponible: "var(--info)",
  config_requise: "var(--warn)",
  en_attente_api: "var(--warn)",
  roadmap: "var(--dim)",
};

export default function ConnectorsPage() {
  // Registre backend quand il répond ; catalogue local sinon (offline-first).
  const query = useQuery({
    queryKey: ["connectors"],
    queryFn: listConnectors,
    retry: false,
  });
  const connectors = mergeConnectors(query.data);
  const isLive = Boolean(query.data?.length);

  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Écosystème · connecteurs</div>
          <h1 style={{ marginTop: 9 }}>
            Connecteurs & <span className="italic">emplacements</span>
          </h1>
          <p className="sub">
            Chaque source externe a un emplacement réservé : variables d&apos;environnement,
            signaux alimentés, statut effectif. Les connecteurs « EN ATTENTE API » (FNC-RF)
            ont leur interface prête — ils s&apos;activeront par simple configuration le jour
            de l&apos;ouverture de l&apos;API amont.
          </p>
        </div>
      </div>

      <div
        className="fx-mono"
        style={{
          fontSize: 11,
          color: "var(--muted)",
          marginBottom: 16,
          display: "flex",
          gap: 14,
          flexWrap: "wrap",
        }}
      >
        <span>
          Source :{" "}
          <span style={{ color: isLive ? "var(--ok)" : "var(--info)" }}>
            {isLive ? "registre backend (environnement réel)" : "catalogue local (démo publique)"}
          </span>
        </span>
        {(
          ["actif", "disponible", "config_requise", "en_attente_api", "roadmap"] as const
        ).map((s) => (
          <span key={s}>
            <span style={{ color: STATUS_COLOR[s] }}>●</span> {STATUS_LABEL[s]}
          </span>
        ))}
      </div>

      <VopWidget />

      {CONNECTOR_CATEGORIES.map((cat) => {
        const rows = connectors.filter((c) => c.category === cat.id);
        if (!rows.length) return null;
        return (
          <div key={cat.id} className="fx-panel" style={{ marginBottom: 16 }}>
            <div className="fx-panel-head">
              <h2>{cat.label}</h2>
              <span className="glyph">{cat.glyph}</span>
            </div>
            <div className="fx-panel-body space-y-3">
              {rows.map((c) => (
                <ConnectorRow key={c.id} connector={c} />
              ))}
            </div>
          </div>
        );
      })}
    </ForensicPage>
  );
}

function ConnectorRow({ connector: c }: { connector: ConnectorOut }) {
  return (
    <div
      style={{
        background: "var(--bg-2)",
        border: "1px solid var(--border)",
        borderLeft: `2px solid ${STATUS_COLOR[c.status]}`,
        padding: "12px 14px",
      }}
    >
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div style={{ minWidth: 240, flex: 1 }}>
          <div className="fx-mono" style={{ fontSize: 13, color: "var(--fg)", fontWeight: 500 }}>
            {c.name}
          </div>
          <p style={{ fontSize: 12, lineHeight: 1.6, color: "var(--fg-2)", marginTop: 4 }}>
            {c.description}
          </p>
        </div>
        <span
          className="fx-mono"
          style={{
            fontSize: 10,
            padding: "3px 8px",
            border: `1px solid ${STATUS_COLOR[c.status]}`,
            color: STATUS_COLOR[c.status],
            whiteSpace: "nowrap",
          }}
        >
          {STATUS_LABEL[c.status]} · {c.mode.toUpperCase()}
        </span>
      </div>

      <div className="flex flex-wrap gap-2" style={{ marginTop: 10 }}>
        {c.env_vars.map((v) => (
          <code
            key={v}
            className="fx-mono"
            style={{
              fontSize: 10,
              padding: "2px 6px",
              background: "var(--panel-2)",
              border: "1px solid var(--border)",
              color: "var(--info)",
            }}
          >
            {v}
          </code>
        ))}
      </div>

      <div
        className="fx-mono"
        style={{
          marginTop: 8,
          fontSize: 10,
          color: "var(--muted)",
          display: "flex",
          justifyContent: "space-between",
          gap: 12,
          flexWrap: "wrap",
        }}
      >
        <span>Alimente : {c.signals.join(" · ")}</span>
        {c.docs_url ? (
          <a
            href={c.docs_url}
            target="_blank"
            rel="noreferrer"
            className="fx-link"
            style={{ color: "var(--info)" }}
          >
            Documentation ↗
          </a>
        ) : null}
      </div>
    </div>
  );
}

function VopWidget() {
  const [beneficiaryName, setBeneficiaryName] = useState("Aciers Nord Est");
  const [expectedName, setExpectedName] = useState("Aciers Nord-Est SAS");
  const [iban, setIban] = useState("FR76 3000 6000 0112 3456 7890 189");
  const [result, setResult] = useState<(VopPrecheckOut & { offline?: boolean }) | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      vopPrecheck({
        beneficiary_name: beneficiaryName,
        iban,
        expected_name: expectedName || undefined,
      }),
    onSuccess: (data) => setResult(data),
    onError: () => {
      // Backend injoignable → simulation locale (même sémantique EPC).
      const sim = simulateVopPrecheck(beneficiaryName, expectedName || undefined);
      setResult({ ...sim, provider: sim.provider, offline: true });
    },
  });

  const verdictColor: Record<string, string> = {
    match: "var(--ok)",
    close_match: "var(--warn)",
    no_match: "var(--risk)",
    not_available: "var(--muted)",
  };
  const verdictLabel: Record<string, string> = {
    match: "MATCH",
    close_match: "CLOSE MATCH",
    no_match: "NO MATCH",
    not_available: "NON DISPONIBLE",
  };

  return (
    <div className="fx-panel" style={{ marginBottom: 16 }}>
      <div className="fx-panel-head">
        <div>
          <div className="fx-eyebrow">§ Emplacement VoP · IPR 2024/886</div>
          <h2 style={{ marginTop: 4 }}>Pré-check nom ↔ IBAN à la saisie du RIB</h2>
        </div>
        <span className="glyph">◫</span>
      </div>
      <div className="fx-panel-body">
        <p style={{ fontSize: 13, lineHeight: 1.65, color: "var(--fg-2)", marginBottom: 14 }}>
          La couche VoP de votre PSP vérifie le bénéficiaire <em>au moment du virement</em>.
          Ce pré-check reproduit la même sémantique (MATCH / CLOSE MATCH / NO MATCH){" "}
          <strong style={{ color: "var(--fg)" }}>au moment de la saisie du RIB</strong> dans le
          master data — là où la fraude BEC s&apos;installe, 48 h avant le règlement.
        </p>

        <div className="grid gap-3 sm:grid-cols-3">
          <VopField
            label="Nom saisi (demande de RIB)"
            value={beneficiaryName}
            onChange={setBeneficiaryName}
          />
          <VopField
            label="Nom attendu (registre / Sirene)"
            value={expectedName}
            onChange={setExpectedName}
          />
          <VopField label="IBAN saisi" value={iban} onChange={setIban} mono />
        </div>

        <div style={{ marginTop: 12, display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <button
            type="button"
            className="fx-btn-ghost sm"
            disabled={mutation.isPending}
            onClick={() => mutation.mutate()}
          >
            {mutation.isPending ? "◷ Vérification…" : "▶ Vérifier la concordance"}
          </button>
          {result ? (
            <span
              className="fx-mono"
              style={{
                fontSize: 11,
                padding: "4px 10px",
                border: `1px solid ${verdictColor[result.verdict]}`,
                color: verdictColor[result.verdict],
              }}
            >
              {verdictLabel[result.verdict]}
              {result.similarity != null ? ` · ${result.similarity}%` : ""}
            </span>
          ) : null}
        </div>

        {result ? (
          <div
            style={{
              marginTop: 12,
              background: "var(--bg-2)",
              border: "1px solid var(--border)",
              borderLeft: `3px solid ${verdictColor[result.verdict]}`,
              padding: "10px 14px",
            }}
          >
            <p style={{ fontSize: 12, lineHeight: 1.6, color: "var(--fg-2)", margin: 0 }}>
              {result.detail}
            </p>
            <div className="fx-mono" style={{ fontSize: 10, color: "var(--dim)", marginTop: 6 }}>
              Fournisseur de vérification : {result.provider}
              {result.offline ? " · backend injoignable, simulation exécutée localement" : ""}
              {" · "}
              <Link href="/master-history" className="fx-link">
                voir les modifications de RIB surveillées →
              </Link>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function VopField({
  label,
  value,
  onChange,
  mono,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  mono?: boolean;
}) {
  return (
    <label style={{ display: "block" }}>
      <span className="fx-eyebrow" style={{ display: "block", marginBottom: 6 }}>
        {label}
      </span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={mono ? "fx-mono" : undefined}
        style={{
          width: "100%",
          fontSize: 12,
          padding: "8px 10px",
          background: "var(--panel)",
          border: "1px solid var(--border-strong)",
          color: "var(--fg)",
          outline: "none",
        }}
      />
    </label>
  );
}
