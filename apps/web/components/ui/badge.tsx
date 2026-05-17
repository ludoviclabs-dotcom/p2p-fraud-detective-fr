import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded px-2 py-0.5 text-xs font-semibold",
  {
    variants: {
      severity: {
        critical: "bg-[#fff0f1] text-[#e5484d]",
        high: "bg-[#fff7e8] text-[#b56b00]",
        medium: "bg-[#fff7e8] text-[#9a5b00]",
        low: "bg-[#e8f8f1] text-[#12a876]",
        neutral: "bg-[#eef3fb] text-[#111827]",
      },
    },
    defaultVariants: { severity: "neutral" },
  },
);

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, severity, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ severity }), className)} {...props} />
  );
}

export function SeverityBadge({ value }: { value: string }) {
  const normalized = value.toLowerCase();
  const map: Record<string, "critical" | "high" | "medium" | "low" | "neutral"> = {
    critical: "critical",
    high: "high",
    medium: "medium",
    low: "low",
  };
  return (
    <Badge severity={map[normalized] ?? "neutral"}>
      {value.toUpperCase()}
    </Badge>
  );
}
