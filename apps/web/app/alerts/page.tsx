"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import {
  listAlertChannels,
  listAudit,
  sendTestAlert,
  type AlertTestResponse,
  type AuditEntryOut,
} from "@/lib/api-client";
import {
  ALERTS_FEED_LIMIT,
  ALERTS_REFETCH_MS,
  buildAlertStreamUrl,
  computeAlertFeedStats,
  getAlertStreamStatusLabel,
  mergeAuditEvent,
  parseAuditStreamEvent,
  parseHeartbeatCursor,
  readStoredAlertCursor,
  writeStoredAlertCursor,
  type StreamState,
} from "@/lib/alerts-feed";
import { SeverityBadge } from "@/components/ui/badge";
import { formatDate } from "@/lib/utils";
import { useLocale } from "@/components/locale-provider";
import { ForensicPage } from "@/components/forensic-page";

type StreamMessage = {
  key: string;
  custom?: string;
};

export default function AlertsPage() {
  const { t } = useLocale();
  const [streamState, setStreamState] = useState<StreamState>("connecting");
  const [streamEvents, setStreamEvents] = useState<AuditEntryOut[]>([]);
  const [lastCursor, setLastCursor] = useState(0);
  const [streamMessage, setStreamMessage] = useState<StreamMessage>({
    key: "alerts.stream_connecting",
  });

  const query = useQuery({
    queryKey: ["alerts-feed"],
    queryFn: () => listAudit(0, ALERTS_FEED_LIMIT),
    enabled: streamState !== "open",
    refetchInterval: ALERTS_REFETCH_MS,
    refetchIntervalInBackground: false,
  });

  useEffect(() => {
    const storage = typeof window !== "undefined" ? window.localStorage : undefined;
    const storedCursor = readStoredAlertCursor(storage);
    setLastCursor(storedCursor);

    const updateCursor = (cursor: number) => {
      setLastCursor((previous) => {
        const nextCursor = Math.max(previous, cursor);
        writeStoredAlertCursor(storage, nextCursor);
        return nextCursor;
      });
    };

    const source = new EventSource(
      buildAlertStreamUrl(storedCursor, ALERTS_FEED_LIMIT),
    );

    source.onopen = () => {
      setStreamState("open");
      setStreamMessage({ key: "alerts.stream_connected" });
    };

    source.addEventListener("audit", (event) => {
      const message = event as MessageEvent<string>;
      const next = parseAuditStreamEvent(message.data);
      if (!next) {
        setStreamMessage({ key: "alerts.stream_malformed" });
        return;
      }

      setStreamEvents((prev) => mergeAuditEvent(prev, next, ALERTS_FEED_LIMIT));

      const eventId = Number.parseInt(message.lastEventId, 10);
      updateCursor(Number.isFinite(eventId) ? Math.max(eventId, next.seq) : next.seq);
    });

    source.addEventListener("heartbeat", (event) => {
      const cursor = parseHeartbeatCursor((event as MessageEvent<string>).data);
      if (cursor !== null) updateCursor(cursor);
      setStreamMessage({ key: "alerts.stream_active" });
    });

    source.addEventListener("auth_error", (event) => {
      setStreamState("fallback");
      setStreamMessage({
        key: "alerts.stream_interrupted",
        custom: parseBackendHint((event as MessageEvent<string>).data),
      });
      source.close();
    });

    source.addEventListener("backend_error", (event) => {
      setStreamState("fallback");
      setStreamMessage({
        key: "alerts.stream_backend_missing",
        custom: parseBackendHint((event as MessageEvent<string>).data),
      });
      source.close();
    });

    source.onerror = () => {
      setStreamState("fallback");
      setStreamMessage({ key: "alerts.stream_interrupted" });
      source.close();
    };

    return () => source.close();
  }, []);

  const events = useMemo(
    () => (streamState === "open" ? streamEvents : query.data?.entries ?? []),
    [query.data?.entries, streamEvents, streamState],
  );

  const stats = useMemo(() => computeAlertFeedStats(events), [events]);
  const streamStatusLabel = getAlertStreamStatusLabel({
    streamState,
    isFetching: query.isFetching,
    translate: t,
  });
  const streamMessageText = streamMessage.custom ?? t(streamMessage.key);

  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">{t("alerts.kicker")}</div>
          <h1 style={{ marginTop: 9 }}>{t("alerts.title")}</h1>
          <p className="sub">{t("alerts.description")}</p>
        </div>
        <div className="fx-head-actions">
          <div
            className="flex items-center gap-2"
            style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--muted)" }}
          >
            <span
              style={{
                width: 7,
                height: 7,
                borderRadius: "50%",
                background:
                  streamState === "open" || query.isFetching
                    ? "var(--verified)"
                    : "var(--dim)",
                display: "inline-block",
              }}
            />
            {streamStatusLabel}
          </div>
        </div>
      </div>

      <div className="mb-5 grid gap-4 md:grid-cols-4">
        <div className="fx-stat info">
          <div className="fx-stat-top">
            <span className="glyph">∿</span>
          </div>
          <div className="lbl">{t("alerts.metric_total")}</div>
          <div className="val">{stats.total}</div>
        </div>
        <div className="fx-stat risk">
          <div className="fx-stat-top">
            <span className="glyph">▲</span>
          </div>
          <div className="lbl">{t("alerts.metric_critical")}</div>
          <div className="val">{stats.critical}</div>
        </div>
        <div className="fx-stat ok">
          <div className="fx-stat-top">
            <span className="glyph">✓</span>
          </div>
          <div className="lbl">{t("alerts.metric_signed")}</div>
          <div className="val">
            {stats.signed} / {stats.total}
          </div>
        </div>
        <div className="fx-stat">
          <div className="fx-stat-top">
            <span className="glyph">◇</span>
          </div>
          <div className="lbl">{t("alerts.metric_kinds")}</div>
          <div className="val">{stats.kinds.size}</div>
        </div>
      </div>

      <ChannelsPanel t={t} />

      <div className="fx-panel">
        <div className="fx-panel-head">
          <h2>{t("alerts.feed_title")}</h2>
          <span className="glyph">∿</span>
        </div>
        <div className="fx-panel-body">
          <div
            data-testid="alerts-stream-message"
            className="mb-4 flex flex-wrap items-center justify-between gap-3"
            style={{
              background: "var(--panel-2)",
              border: "1px solid var(--border)",
              padding: "10px 14px",
            }}
          >
            <span
              className="fx-mono"
              style={{ fontSize: 11, color: "var(--fg-2)" }}
            >
              {streamMessageText}
            </span>
            <span
              data-testid="alerts-cursor"
              className="fx-mono"
              style={{ fontSize: 11, color: "var(--muted)" }}
            >
              {t("alerts.cursor")}: {lastCursor}
            </span>
          </div>
          {streamState !== "open" && query.isLoading ? (
            <span className="fx-mono" style={{ fontSize: 12, color: "var(--muted)" }}>
              {t("alerts.connecting")}
            </span>
          ) : !events.length ? (
            <span className="fx-mono" style={{ fontSize: 12, color: "var(--muted)" }}>
              {t("alerts.empty")}
            </span>
          ) : (
            <EventFeed events={events} t={t} />
          )}
        </div>
      </div>
    </ForensicPage>
  );
}

function EventFeed({
  events,
  t,
}: {
  events: AuditEntryOut[];
  t: (key: string, params?: Record<string, string | number>) => string;
}) {
  return (
    <ul className="space-y-2">
      {events.map((event) => {
        const sev = (event.payload?.severity as string) ?? "";
        const borderColor =
          sev === "critical"
            ? "var(--risk)"
            : sev === "high"
              ? "var(--warn)"
              : sev === "medium"
                ? "var(--warn)"
                : sev === "low"
                  ? "var(--verified)"
                  : "var(--border-strong)";
        return (
          <li
            key={event.seq}
            style={{
              display: "flex",
              alignItems: "flex-start",
              justifyContent: "space-between",
              gap: 12,
              background: "var(--panel-2)",
              borderLeft: `3px solid ${borderColor}`,
              padding: "10px 14px",
            }}
          >
            <div style={{ flex: 1, minWidth: 0 }}>
              <div className="flex items-baseline gap-2">
                <span
                  className="fx-mono"
                  style={{ fontSize: 12, color: "var(--fg)" }}
                >
                  {event.kind}
                </span>
                {sev ? <SeverityBadge value={sev} /> : null}
              </div>
              <div
                className="fx-mono"
                style={{ fontSize: 11, color: "var(--muted)", marginTop: 3 }}
              >
                {t("alerts.by_actor")}{" "}
                <strong style={{ color: "var(--fg)" }}>{event.actor}</strong>
                {event.payload?.case_id ? (
                  <>
                    {" "}
                    - {t("alerts.case")}{" "}
                    <span style={{ color: "var(--info)" }}>
                      {String(event.payload.case_id).slice(0, 16)}
                    </span>
                  </>
                ) : null}
              </div>
            </div>
            <div
              className="flex flex-col items-end"
              style={{ flexShrink: 0 }}
            >
              <span
                className="fx-mono"
                style={{ fontSize: 11, color: "var(--muted)" }}
              >
                {formatDate(event.at)}
              </span>
              {event.signature ? (
                <span
                  className="fx-mono"
                  style={{ fontSize: 10, color: "var(--verified)" }}
                >
                  {t("alerts.ed25519")}
                </span>
              ) : null}
            </div>
          </li>
        );
      })}
    </ul>
  );
}

function parseBackendHint(raw: string): string | undefined {
  try {
    const payload = JSON.parse(raw) as { hint?: unknown; error?: unknown };
    return typeof payload.hint === "string"
      ? payload.hint
      : typeof payload.error === "string"
        ? payload.error
        : undefined;
  } catch {
    return undefined;
  }
}

const CHANNEL_ENV: Record<string, string> = {
  slack: "SLACK_WEBHOOK_URL",
  teams: "TEAMS_WEBHOOK_URL",
  smtp: "SMTP_HOST · SMTP_FROM · SMTP_TO",
};

const CHANNEL_LABEL: Record<string, string> = {
  slack: "Slack Webhook",
  teams: "Microsoft Teams",
  smtp: "Email (SMTP)",
};

/**
 * Canaux de notification — statut live quand le backend répond, documentation
 * des variables d'environnement sinon (offline-first). Le bouton d'alerte test
 * valide la chaîne finding → règle → canal sans attendre un déclenchement réel.
 */
function ChannelsPanel({ t }: { t: (key: string) => string }) {
  const channels = useQuery({
    queryKey: ["alert-channels"],
    queryFn: listAlertChannels,
    retry: false,
  });
  const [testResult, setTestResult] = useState<AlertTestResponse | null>(null);
  const testMutation = useMutation({
    mutationFn: sendTestAlert,
    onSuccess: setTestResult,
  });

  const live = channels.data ?? null;

  return (
    <div className="fx-panel" style={{ marginBottom: 16 }}>
      <div className="fx-panel-head">
        <div>
          <h2>{t("alerts.channels_title")}</h2>
        </div>
        <span
          className="fx-mono"
          style={{
            fontSize: 10,
            padding: "3px 8px",
            border: `1px solid ${live ? "var(--ok)" : "var(--border-strong)"}`,
            color: live ? "var(--ok)" : "var(--muted)",
          }}
        >
          {live ? "STATUT LIVE" : "DOC OFFLINE"}
        </span>
      </div>
      <div className="fx-table-wrap">
        <table data-testid="alerts-channel-table" className="fx-table">
          <thead>
            <tr>
              <th>{t("alerts.channel")}</th>
              <th>{t("alerts.status")}</th>
              <th>{t("alerts.target")}</th>
            </tr>
          </thead>
          <tbody>
            {(live ?? [
              { name: "slack", configured: false, target: "" },
              { name: "teams", configured: false, target: "" },
              { name: "smtp", configured: false, target: "" },
            ]).map((c) => (
              <tr key={c.name}>
                <td className="key">{CHANNEL_LABEL[c.name] ?? c.name}</td>
                <td>
                  {live ? (
                    <span
                      className="fx-mono"
                      style={{
                        fontSize: 11,
                        color: c.configured ? "var(--ok)" : "var(--warn)",
                      }}
                    >
                      {c.configured ? "● ACTIF" : "○ CONFIG REQUISE"}
                    </span>
                  ) : (
                    <span className="fx-mono" style={{ fontSize: 11 }}>
                      {t("alerts.configurable_via")}
                    </span>
                  )}{" "}
                  <code
                    style={{
                      background: "var(--panel-2)",
                      border: "1px solid var(--border)",
                      padding: "1px 5px",
                      fontFamily: "var(--font-mono)",
                      fontSize: 10,
                    }}
                  >
                    {CHANNEL_ENV[c.name] ?? c.name}
                  </code>
                </td>
                <td>
                  <span className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>
                    {c.configured && c.target
                      ? c.target
                      : c.name === "slack"
                        ? t("alerts.slack_target")
                        : c.name === "teams"
                          ? t("alerts.teams_target")
                          : "Destinataires SMTP"}
                  </span>
                </td>
              </tr>
            ))}
            <tr>
              <td className="key">Webhook B2B CloudEvents</td>
              <td>
                <span className="fx-mono" style={{ fontSize: 11 }}>
                  {t("alerts.hmac_signed_via")}{" "}
                  <code
                    style={{
                      background: "var(--panel-2)",
                      border: "1px solid var(--border)",
                      padding: "1px 5px",
                      fontFamily: "var(--font-mono)",
                      fontSize: 10,
                    }}
                  >
                    WEBHOOK_URL
                  </code>
                </span>
              </td>
              <td>
                <span className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>
                  {t("alerts.webhook_target")}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div
        className="fx-panel-body"
        style={{ borderTop: "1px solid var(--border)", display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}
      >
        <button
          type="button"
          className="fx-btn-ghost sm"
          disabled={testMutation.isPending}
          onClick={() => testMutation.mutate()}
        >
          {testMutation.isPending ? "◷ Envoi…" : "▶ Envoyer une alerte test"}
        </button>
        {testMutation.isError ? (
          <span className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>
            Backend FastAPI requis pour l&apos;alerte test — la configuration des canaux
            reste documentée ci-dessus.
          </span>
        ) : null}
        {testResult ? (
          <span className="fx-mono" style={{ fontSize: 11, color: "var(--fg-2)" }}>
            {testResult.message}
            {testResult.sent.map((d) => (
              <span
                key={d.channel}
                style={{
                  marginLeft: 8,
                  color: d.delivered ? "var(--ok)" : "var(--risk)",
                }}
              >
                {d.channel}: {d.delivered ? "✓" : "✕"}
              </span>
            ))}
          </span>
        ) : null}
      </div>
    </div>
  );
}
