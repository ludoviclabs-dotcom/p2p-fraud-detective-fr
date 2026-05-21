"use client";

import { useRef, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";
const SECRET = process.env.FRAUD_API_SECRET ?? "";

type Props = {
  vendorId: string;
  vendorName?: string | null;
  siren?: string | null;
  totalPaidEur?: number | null;
  nInvoices: number;
  isSanctioned: boolean;
  isPep: boolean;
};

export function LlmNarrativeStream(props: Props) {
  const [text, setText] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const start = async () => {
    setText("");
    setError(null);
    setStreaming(true);
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    try {
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };
      if (SECRET) headers.Authorization = `Bearer ${SECRET}`;
      const resp = await fetch(`${API_BASE}/api/v1/llm/narrative`, {
        method: "POST",
        headers,
        signal: ctrl.signal,
        body: JSON.stringify({
          vendor_id: props.vendorId,
          vendor_name: props.vendorName ?? null,
          siren: props.siren ?? null,
          total_paid_eur: props.totalPaidEur ?? null,
          n_invoices: props.nInvoices,
          is_sanctioned: props.isSanctioned,
          is_pep: props.isPep,
          findings: [],
        }),
      });
      if (!resp.ok || !resp.body) {
        const t = await resp.text();
        throw new Error(`HTTP ${resp.status} : ${t.slice(0, 200)}`);
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        // Parse Server-Sent Events : lignes "data: <json>\n\n"
        const events = buffer.split("\n\n");
        buffer = events.pop() ?? ""; // garder le dernier (potentiellement incomplet)
        for (const event of events) {
          for (const line of event.split("\n")) {
            if (!line.startsWith("data:")) continue;
            const payload = line.slice(5).trim();
            if (payload === "[DONE]") {
              setStreaming(false);
              return;
            }
            try {
              const parsed = JSON.parse(payload) as {
                text?: string;
                error?: string;
              };
              if (parsed.error) {
                throw new Error(parsed.error);
              }
              if (parsed.text) {
                setText((prev) => prev + parsed.text);
              }
            } catch (e) {
              // payload malformé — on tente d'afficher raw
              if (payload && !payload.startsWith("{")) {
                setText((prev) => prev + payload);
              } else {
                throw e;
              }
            }
          }
        }
      }
    } catch (e) {
      if ((e as Error).name === "AbortError") {
        // arrêt volontaire
      } else {
        setError((e as Error).message);
      }
    } finally {
      setStreaming(false);
      abortRef.current = null;
    }
  };

  const stop = () => {
    abortRef.current?.abort();
  };

  return (
    <div className="space-y-3">
      {/* Controls row */}
      <div className="flex flex-wrap items-center gap-3">
        {streaming ? (
          <button onClick={stop} type="button" className="fx-btn sm">
            ◼ Arrêter
          </button>
        ) : (
          <button onClick={start} type="button" className="fx-btn sm">
            ★ Générer narration (Claude streaming)
          </button>
        )}
        <span className="fx-mono" style={{ fontSize: 10, color: "var(--muted)" }}>
          Streaming SSE via{" "}
          <code
            style={{
              fontFamily: "var(--font-mono)",
              background: "var(--panel-2)",
              border: "1px solid var(--border)",
              padding: "1px 5px",
              fontSize: 10,
            }}
          >
            POST /api/v1/llm/narrative
          </code>{" "}
          · Requiert <code
            style={{
              fontFamily: "var(--font-mono)",
              background: "var(--panel-2)",
              border: "1px solid var(--border)",
              padding: "1px 5px",
              fontSize: 10,
            }}
          >
            ANTHROPIC_API_KEY
          </code>{" "}
          côté FastAPI.
        </span>
      </div>

      {/* Error state */}
      {error ? (
        <div className="fx-notice" style={{ borderLeftColor: "var(--risk)" }}>
          <span className="glyph" style={{ color: "var(--risk)" }}>⚠</span>
          <div>
            <div className="nt" style={{ color: "var(--risk)" }}>Erreur de streaming</div>
            <p className="nb">{error}</p>
          </div>
        </div>
      ) : null}

      {/* Narrative output */}
      {text || streaming ? (
        <div className="fx-panel">
          <div className="fx-panel-head">
            <div>
              <div className="fx-eyebrow">
                ∿ Narration ISA 240{streaming ? " (streaming…)" : ""}
              </div>
            </div>
            {streaming ? (
              <span
                className="fx-mono"
                style={{ fontSize: 10, color: "var(--risk)", animation: "forensicPulse 1.4s infinite" }}
              >
                LIVE
              </span>
            ) : null}
          </div>
          <div className="fx-panel-body">
            <div
              className="fx-mono"
              style={{
                fontSize: 13,
                lineHeight: 1.7,
                color: "var(--fg-2)",
                whiteSpace: "pre-wrap",
              }}
            >
              {text}
              {streaming ? (
                <span
                  style={{
                    display: "inline-block",
                    width: 8,
                    height: 14,
                    background: "var(--risk)",
                    marginLeft: 4,
                    verticalAlign: "text-bottom",
                    animation: "forensicPulse 0.9s infinite",
                  }}
                />
              ) : null}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
