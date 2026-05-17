"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowRight,
  BarChart3,
  BriefcaseBusiness,
  Clock3,
  FileSearch,
  RefreshCw,
  ShieldAlert,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";
import {
  getCockpitKpis,
  getTopVendors,
  type CockpitKPIs,
  type TopVendor,
} from "@/lib/api-client";
import { formatEur } from "@/lib/utils";
import { Button } from "@/components/ui/button";

type KpiTone = "blue" | "risk" | "amber" | "green";

const toneClasses: Record<KpiTone, { icon: string; ring: string; text: string }> = {
  blue: {
    icon: "bg-[#eaf1ff] text-[#2f6bff]",
    ring: "border-l-[#2f6bff]",
    text: "text-[#2f6bff]",
  },
  risk: {
    icon: "bg-[#fff0f1] text-[#e5484d]",
    ring: "border-l-[#e5484d]",
    text: "text-[#e5484d]",
  },
  amber: {
    icon: "bg-[#fff7e8] text-[#b56b00]",
    ring: "border-l-[#f5a524]",
    text: "text-[#b56b00]",
  },
  green: {
    icon: "bg-[#e8f8f1] text-[#12a876]",
    ring: "border-l-[#12a876]",
    text: "text-[#12a876]",
  },
};

function KPICard({
  label,
  value,
  delta,
  tone,
  Icon,
}: {
  label: string;
  value: string;
  delta?: string;
  tone: KpiTone;
  Icon: LucideIcon;
}) {
  const classes = toneClasses[tone];
  return (
    <div
      className={`rounded-md border border-l-4 border-[#e6ebf2] ${classes.ring} bg-white p-5 shadow-sm dark:border-white/10 dark:bg-white/[0.04]`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className={`grid h-10 w-10 place-items-center rounded-md ${classes.icon}`}>
          <Icon size={20} />
        </div>
        {delta ? (
          <span className={`rounded px-2 py-1 text-xs font-semibold ${classes.icon}`}>
            {delta}
          </span>
        ) : null}
      </div>
      <div className="mt-5 text-xs font-semibold uppercase tracking-wider text-[#667085]">
        {label}
      </div>
      <div className="metric-number mt-2 font-bold text-[#111827] dark:text-white">
        {value}
      </div>
    </div>
  );
}

function Sparkline({
  points,
  color = "#2f6bff",
}: {
  points: { date: string; value: number }[];
  color?: string;
}) {
  if (!points.length) {
    return (
      <div className="mt-3 h-12 rounded bg-[#f7f9fc] dark:bg-white/[0.04]" />
    );
  }
  const max = Math.max(...points.map((p) => p.value), 1);
  const width = 200;
  const height = 44;
  const stepX = width / (points.length - 1 || 1);
  const path = points
    .map((p, i) => {
      const x = i * stepX;
      const y = height - (p.value / max) * height;
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  const area = `${path} L${width},${height} L0,${height} Z`;
  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      className="mt-3 h-14 w-full"
      aria-hidden
    >
      <path d={area} fill={color} fillOpacity={0.14} />
      <path d={path} fill="none" stroke={color} strokeWidth={2.4} />
    </svg>
  );
}

export default function DashboardPage() {
  const kpisQuery = useQuery({
    queryKey: ["cockpit", "kpis"],
    queryFn: getCockpitKpis,
    retry: false,
  });
  const vendorsQuery = useQuery({
    queryKey: ["cockpit", "top-vendors"],
    queryFn: () => getTopVendors(10),
    retry: false,
  });

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[#08111f] dark:text-white">
            Cockpit risque P2P
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-[#667085]">
            Vue consolidée des risques fournisseurs, triée par exposition
            financière et prête pour la décision audit.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            href="/sandbox"
            className="inline-flex h-10 items-center gap-2 rounded-md bg-[#2f6bff] px-4 text-sm font-semibold text-white shadow-sm shadow-[#2f6bff]/20 transition-colors hover:bg-[#2457d6]"
          >
            Analyser un scénario
            <ArrowRight size={15} />
          </Link>
          <Link
            href="/exports"
            className="inline-flex h-10 items-center gap-2 rounded-md border border-[#e6ebf2] bg-white px-4 text-sm font-semibold text-[#667085] transition-colors hover:border-[#2f6bff] hover:text-[#2f6bff] dark:border-white/10 dark:bg-white/[0.04]"
          >
            Préparer l'export
          </Link>
        </div>
      </div>

      <section className="mt-6 grid gap-4 lg:grid-cols-[1fr_0.42fr]">
        <div>
          {kpisQuery.isLoading ? (
            <KpiSkeleton />
          ) : kpisQuery.error ? (
            <ActionState
              title="Backend indisponible"
              body="Les KPI API ne sont pas accessibles. Vous pouvez tout de même lancer une démo synthétique pour explorer le parcours."
              actionHref="/sandbox"
              actionLabel="Lancer la sandbox"
            />
          ) : (
            <KpiGrid data={kpisQuery.data!} />
          )}
        </div>

        <div className="rounded-md border border-[#e6ebf2] bg-[#08111f] p-5 text-white shadow-xl shadow-[#08111f]/10">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-xs font-semibold uppercase tracking-wider text-white/42">
                Priorité du jour
              </div>
              <div className="mt-2 text-xl font-semibold">
                Réduire l'exposition critique
              </div>
            </div>
            <div className="grid h-11 w-11 place-items-center rounded-md bg-[#fff0f1] text-[#e5484d]">
              <ShieldAlert size={22} />
            </div>
          </div>
          <p className="mt-4 text-sm leading-6 text-white/62">
            Traitez d'abord les fournisseurs à criticité maximale avec retard
            SLA ou absence d'assignation. Chaque case doit produire une preuve
            d'audit exploitable.
          </p>
          <div className="mt-5 grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-md bg-white/[0.07] p-3">
              <div className="text-white/45">Next action</div>
              <div className="mt-1 font-semibold">Assigner reviewer</div>
            </div>
            <div className="rounded-md bg-white/[0.07] p-3">
              <div className="text-white/45">Preuve</div>
              <div className="mt-1 font-semibold">Audit trail</div>
            </div>
          </div>
        </div>
      </section>

      <section className="mt-8 grid gap-4 xl:grid-cols-[1fr_0.42fr]">
        <div className="rounded-md border border-[#e6ebf2] bg-white shadow-sm dark:border-white/10 dark:bg-white/[0.04]">
          <div className="flex items-center justify-between gap-4 border-b border-[#e6ebf2] px-5 py-4 dark:border-white/10">
            <div>
              <h2 className="font-semibold text-[#111827] dark:text-white">
                Top fournisseurs par exposition financière
              </h2>
              <p className="mt-1 text-sm text-[#667085]">
                Le tri favorise l'impact financier, pas seulement le score brut.
              </p>
            </div>
            <BriefcaseBusiness size={20} className="text-[#2f6bff]" />
          </div>
          {vendorsQuery.isLoading ? (
            <TableSkeleton />
          ) : vendorsQuery.error ? (
            <div className="p-5">
              <ActionState
                title="Fournisseurs non chargés"
                body="Vérifiez la variable NEXT_PUBLIC_API_URL ou explorez un scénario préchargé."
                actionHref="/sandbox"
                actionLabel="Voir les scénarios"
              />
            </div>
          ) : (
            <TopVendorsTable rows={vendorsQuery.data ?? []} />
          )}
        </div>

        <div className="rounded-md border border-[#e6ebf2] bg-white p-5 shadow-sm dark:border-white/10 dark:bg-white/[0.04]">
          <div className="flex items-center gap-2 font-semibold text-[#111827] dark:text-white">
            <FileSearch size={19} className="text-[#2f6bff]" />
            Parcours recommandé
          </div>
          <div className="mt-5 space-y-4">
            {[
              ["1", "Qualifier la case", "Vérifier score, source et exposition."],
              ["2", "Ouvrir fournisseur 360", "Valider liens SIREN, IBAN et historique."],
              ["3", "Exporter la preuve", "Signer et archiver la piste d'audit."],
            ].map(([step, title, body]) => (
              <div key={step} className="flex gap-3">
                <div className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-[#eaf1ff] text-xs font-bold text-[#2f6bff]">
                  {step}
                </div>
                <div>
                  <div className="text-sm font-semibold text-[#111827] dark:text-white">
                    {title}
                  </div>
                  <div className="text-sm leading-6 text-[#667085]">{body}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

function KpiSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {["Exposition totale", "Critique", "Cases ouverts", "SLA"].map((label) => (
        <div
          key={label}
          className="h-36 animate-pulse rounded-md border border-[#e6ebf2] bg-white p-5 dark:border-white/10 dark:bg-white/[0.04]"
        >
          <div className="h-10 w-10 rounded-md bg-[#eef3fb]" />
          <div className="mt-5 h-3 w-32 rounded bg-[#eef3fb]" />
          <div className="mt-4 h-8 w-24 rounded bg-[#eef3fb]" />
        </div>
      ))}
    </div>
  );
}

function KpiGrid({ data }: { data: CockpitKPIs }) {
  return (
    <>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KPICard
          label="Exposition totale"
          value={formatEur(data.exposure_total_eur)}
          tone="blue"
          Icon={TrendingUp}
        />
        <KPICard
          label="Exposition critical"
          value={formatEur(data.exposure_critical_eur)}
          tone="risk"
          Icon={ShieldAlert}
        />
        <KPICard
          label="Cases ouverts"
          value={String(data.n_cases_open)}
          tone="amber"
          Icon={FileSearch}
        />
        <KPICard
          label="Retards SLA"
          value={String(data.n_cases_overdue)}
          delta={
            data.n_cases_unassigned_critical > 0
              ? `${data.n_cases_unassigned_critical} non assignés`
              : undefined
          }
          tone="green"
          Icon={Clock3}
        />
      </div>

      <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <TrendCard
          title="Cases créés"
          points={data.trend_cases_created ?? []}
          color="#2f6bff"
        />
        <TrendCard
          title="Cases clôturés"
          points={data.trend_cases_closed ?? []}
          color="#12a876"
        />
        <TrendCard
          title="Alertes critiques"
          points={data.trend_critical_alerts ?? []}
          color="#e5484d"
        />
        <TrendCard
          title="Activité audit"
          points={data.trend_audit_activity ?? []}
          color="#f5a524"
        />
      </div>
    </>
  );
}

function TrendCard({
  title,
  points,
  color,
}: {
  title: string;
  points: { date: string; value: number }[];
  color: string;
}) {
  return (
    <div className="rounded-md border border-[#e6ebf2] bg-white p-4 shadow-sm dark:border-white/10 dark:bg-white/[0.04]">
      <div className="flex items-center justify-between gap-3">
        <div className="text-sm font-semibold text-[#111827] dark:text-white">
          {title}
        </div>
        <BarChart3 size={16} style={{ color }} />
      </div>
      <Sparkline points={points} color={color} />
      <div className="mt-2 text-xs text-[#667085]">Tendance 30 jours</div>
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="space-y-3 p-5">
      {Array.from({ length: 5 }).map((_, index) => (
        <div key={index} className="h-12 animate-pulse rounded bg-[#eef3fb]" />
      ))}
    </div>
  );
}

function TopVendorsTable({ rows }: { rows: TopVendor[] }) {
  if (!rows.length) {
    return (
      <div className="p-5">
        <ActionState
          title="Aucun finding chargé"
          body="Le Top 10 se calcule sur les findings de la session. Lancez un scénario synthétique pour voir le cockpit rempli."
          actionHref="/sandbox"
          actionLabel="Analyser un scénario"
        />
      </div>
    );
  }
  const severityColor: Record<string, string> = {
    critical: "bg-[#fff0f1] text-[#e5484d]",
    high: "bg-[#fff7e8] text-[#b56b00]",
    medium: "bg-[#fff7e8] text-[#9a5b00]",
    low: "bg-[#e8f8f1] text-[#12a876]",
  };
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-[#f7f9fc] text-xs uppercase tracking-wider text-[#667085] dark:bg-white/[0.03]">
          <tr>
            <th className="px-5 py-3 text-left">Fournisseur</th>
            <th className="px-5 py-3 text-right">Exposition</th>
            <th className="px-5 py-3 text-right">Findings</th>
            <th className="px-5 py-3 text-left">Sévérité</th>
            <th className="px-5 py-3 text-right">Action</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.vendor_id}
              className="border-t border-[#e6ebf2] transition-colors hover:bg-[#f7f9fc] dark:border-white/10 dark:hover:bg-white/[0.03]"
            >
              <td className="px-5 py-4 font-mono text-xs font-semibold text-[#111827] dark:text-white">
                {row.vendor_id}
              </td>
              <td className="px-5 py-4 text-right font-semibold">
                {formatEur(row.exposure_eur)}
              </td>
              <td className="px-5 py-4 text-right">{row.n_findings}</td>
              <td className="px-5 py-4">
                <span
                  className={`inline-block rounded px-2 py-1 text-xs font-semibold ${severityColor[row.max_severity] ?? "bg-[#eef3fb] text-[#111827]"}`}
                >
                  {row.max_severity.toUpperCase()}
                </span>
              </td>
              <td className="px-5 py-4 text-right">
                <Link
                  href={`/vendors/${encodeURIComponent(row.vendor_id)}`}
                  className="inline-flex items-center gap-1 text-xs font-semibold text-[#2f6bff] hover:underline"
                >
                  Ouvrir 360 <ArrowRight size={13} />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ActionState({
  title,
  body,
  actionHref,
  actionLabel,
}: {
  title: string;
  body: string;
  actionHref: string;
  actionLabel: string;
}) {
  return (
    <div className="rounded-md border border-[#e6ebf2] bg-white p-5 shadow-sm dark:border-white/10 dark:bg-white/[0.04]">
      <div className="flex items-start gap-3">
        <div className="grid h-10 w-10 place-items-center rounded-md bg-[#fff7e8] text-[#b56b00]">
          <AlertTriangle size={19} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="font-semibold text-[#111827] dark:text-white">
            {title}
          </div>
          <p className="mt-1 text-sm leading-6 text-[#667085]">{body}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Link
              href={actionHref}
              className="inline-flex h-9 items-center gap-2 rounded-md bg-[#2f6bff] px-3 text-sm font-semibold text-white"
            >
              {actionLabel}
              <ArrowRight size={14} />
            </Link>
            <Button
              variant="outline"
              size="sm"
              type="button"
              onClick={() => window.location.reload()}
            >
              <RefreshCw size={14} />
              Réessayer
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
