"use client";

import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { AlertTriangle, Sparkles, StopCircle } from "lucide-react";

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
      <div
        role="note"
        className="flex items-start gap-2 rounded-md border border-[#f0dca0] bg-[#fff8e1] px-3 py-2 text-xs text-[#7a5d12]"
      >
        <AlertTriangle size={14} className="mt-0.5 shrink-0" />
        <div>
          <strong>Assistance rédactionnelle générée par IA</strong> — outil
          d&apos;aide à la rédaction d&apos;une narration d&apos;investigation
          (cadre ISA 240). Le contenu produit ne décide pas et n&apos;engage
          pas l&apos;organisation : <strong>une supervision humaine est
          requise</strong> avant toute utilisation opérationnelle, transmission
          à un tiers ou archivage. Conforme à l&apos;obligation de
          transparence (AI Act art. 50).
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {streaming ? (
          <Button onClick={stop} variant="danger" type="button">
            <StopCircle size={14} /> Arrêter
          </Button>
        ) : (
          <Button onClick={start} type="button">
            <Sparkles size={14} /> Générer narration (Claude streaming)
          </Button>
        )}
        <span className="text-xs text-[#5a6478]">
          Streaming SSE via{" "}
          <code className="rounded bg-[#f4f6fa] px-1 py-0.5">
            POST /api/v1/llm/narrative
          </code>{" "}
          · Requiert <code>ANTHROPIC_API_KEY</code> côté FastAPI.
        </span>
      </div>

      {error ? (
        <div className="rounded border border-[#a23e48] bg-[#fdecee] p-3 text-sm text-[#a23e48]">
          ❌ {error}
        </div>
      ) : null}

      {text || streaming ? (
        <div className="rounded-md border border-[#e1e5ee] bg-white p-4">
          <div className="mb-2 flex items-center gap-2 text-xs uppercase tracking-wider text-[#5a6478]">
            <Sparkles size={12} className={streaming ? "animate-pulse" : ""} />
            Narration ISA 240 {streaming ? "(streaming…)" : ""}
          </div>
          <div className="whitespace-pre-wrap text-sm text-[#1a1f2c]">
            {text}
            {streaming ? (
              <span className="ml-1 inline-block h-3 w-2 animate-pulse bg-[#1f3a6e]" />
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}
