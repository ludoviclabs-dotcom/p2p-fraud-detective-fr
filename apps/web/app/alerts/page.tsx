"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { listAudit, type AuditEntryOut } from "@/lib/api-client";
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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SeverityBadge } from "@/components/ui/badge";
import { Bell, Activity } from "lucide-react";
import { formatDate } from "@/lib/utils";
import { useLocale } from "@/components/locale-provider";

const SEVERITY_BG: Record<string, string> = {
  critical: "border-l-4 border-l-[#a23e48]",
  high: "border-l-4 border-l-[#c97b1f]",
  medium: "border-l-4 border-l-[#e5a93a]",
  low: "border-l-4 border-l-[#3e7c5a]",
};

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
    <div className="px-8 py-10">
      <div className="mb-1 flex items-center justify-between">
        <div className="text-xs uppercase tracking-wider text-[#5a6478]">
          {t("alerts.kicker")}
        </div>
        <div className="flex items-center gap-1 text-xs text-[#5a6478]">
          <span
            className={`h-2 w-2 rounded-full ${
              streamState === "open" || query.isFetching
                ? "animate-pulse bg-[#3e7c5a]"
                : "bg-[#9aa3b2]"
            }`}
          />
          {streamStatusLabel}
        </div>
      </div>
      <h1 className="mb-1 text-3xl font-bold text-[#0f1b33] dark:text-white">
        {t("alerts.title")}
      </h1>
      <p className="mb-6 text-sm text-[#5a6478]">{t("alerts.description")}</p>

      <div className="mb-4 grid gap-3 md:grid-cols-4">
        <Card>
          <CardContent>
            <div className="text-xs uppercase tracking-wider text-[#5a6478]">
              {t("alerts.metric_total")}
            </div>
            <div className="flex items-center gap-2 text-2xl font-semibold text-[#0f1b33]">
              <Activity size={18} /> {stats.total}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div className="text-xs uppercase tracking-wider text-[#5a6478]">
              {t("alerts.metric_critical")}
            </div>
            <div className="flex items-center gap-2 text-2xl font-semibold text-[#a23e48]">
              <Bell size={18} /> {stats.critical}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div className="text-xs uppercase tracking-wider text-[#5a6478]">
              {t("alerts.metric_signed")}
            </div>
            <div className="text-2xl font-semibold text-[#3e7c5a]">
              {stats.signed} / {stats.total}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div className="text-xs uppercase tracking-wider text-[#5a6478]">
              {t("alerts.metric_kinds")}
            </div>
            <div className="text-2xl font-semibold text-[#0f1b33]">
              {stats.kinds.size}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>{t("alerts.channels_title")}</CardTitle>
        </CardHeader>
        <CardContent>
          <table data-testid="alerts-channel-table" className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#e1e5ee] text-left text-xs text-[#5a6478]">
                <th className="py-2">{t("alerts.channel")}</th>
                <th className="py-2">{t("alerts.status")}</th>
                <th className="py-2">{t("alerts.target")}</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-[#e1e5ee]">
                <td className="py-2 font-medium">Slack Webhook</td>
                <td className="py-2 text-xs">
                  {t("alerts.configurable_via")}{" "}
                  <code className="rounded bg-[#f4f6fa] px-1 py-0.5">
                    SLACK_WEBHOOK_URL
                  </code>
                </td>
                <td className="py-2 text-xs text-[#5a6478]">
                  {t("alerts.slack_target")}
                </td>
              </tr>
              <tr className="border-b border-[#e1e5ee]">
                <td className="py-2 font-medium">Microsoft Teams</td>
                <td className="py-2 text-xs">
                  {t("alerts.configurable_via")}{" "}
                  <code className="rounded bg-[#f4f6fa] px-1 py-0.5">
                    TEAMS_WEBHOOK_URL
                  </code>
                </td>
                <td className="py-2 text-xs text-[#5a6478]">
                  {t("alerts.teams_target")}
                </td>
              </tr>
              <tr className="border-b border-[#e1e5ee]">
                <td className="py-2 font-medium">Webhook B2B CloudEvents</td>
                <td className="py-2 text-xs">
                  {t("alerts.hmac_signed_via")}{" "}
                  <code className="rounded bg-[#f4f6fa] px-1 py-0.5">
                    WEBHOOK_URL
                  </code>
                </td>
                <td className="py-2 text-xs text-[#5a6478]">
                  {t("alerts.webhook_target")}
                </td>
              </tr>
            </tbody>
          </table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("alerts.feed_title")}</CardTitle>
        </CardHeader>
        <div className="p-4">
          <div
            data-testid="alerts-stream-message"
            className="mb-3 flex flex-wrap items-center justify-between gap-2 rounded-md bg-[#f4f6fa] px-3 py-2 text-xs text-[#5a6478]"
          >
            <span>{streamMessageText}</span>
            <span data-testid="alerts-cursor" className="font-mono">
              {t("alerts.cursor")}: {lastCursor}
            </span>
          </div>
          {streamState !== "open" && query.isLoading ? (
            <div className="text-sm text-[#5a6478]">{t("alerts.connecting")}</div>
          ) : !events.length ? (
            <div className="text-sm text-[#5a6478]">{t("alerts.empty")}</div>
          ) : (
            <EventFeed events={events} t={t} />
          )}
        </div>
      </Card>
    </div>
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
        const sevClass = SEVERITY_BG[sev] ?? "border-l-4 border-l-[#9aa3b2]";
        return (
          <li
            key={event.seq}
            className={`flex items-start justify-between gap-3 rounded bg-[#f9fafc] px-3 py-2 ${sevClass}`}
          >
            <div className="flex-1">
              <div className="flex items-baseline gap-2">
                <span className="font-mono text-xs text-[#1f3a6e]">
                  {event.kind}
                </span>
                {sev ? <SeverityBadge value={sev} /> : null}
              </div>
              <div className="mt-0.5 text-xs text-[#5a6478]">
                {t("alerts.by_actor")}{" "}
                <strong className="text-[#0f1b33]">{event.actor}</strong>
                {event.payload?.case_id ? (
                  <>
                    {" "}
                    - {t("alerts.case")}{" "}
                    <span className="font-mono text-[#1f3a6e]">
                      {String(event.payload.case_id).slice(0, 16)}
                    </span>
                  </>
                ) : null}
              </div>
            </div>
            <div className="flex flex-col items-end text-xs text-[#5a6478]">
              <span>{formatDate(event.at)}</span>
              {event.signature ? (
                <span className="text-[#3e7c5a]">{t("alerts.ed25519")}</span>
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
