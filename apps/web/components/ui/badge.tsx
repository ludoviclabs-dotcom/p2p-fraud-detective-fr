import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded px-2 py-0.5 text-xs font-medium",
  {
    variants: {
      severity: {
        critical: "bg-[#a23e48] text-white",
        high: "bg-[#c97b1f] text-white",
        medium: "bg-[#e5a93a] text-[#0f1b33]",
        low: "bg-[#3e7c5a] text-white",
        neutral: "bg-[#e1e5ee] text-[#0f1b33]",
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
