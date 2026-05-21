import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Severity = "critical" | "high" | "medium" | "low" | "neutral";

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  severity?: Severity;
}

export function Badge({ className, severity = "neutral", ...props }: BadgeProps) {
  const sev = severity === "neutral" ? "" : severity;
  return <span className={cn("fx-tag", sev, className)} {...props} />;
}

export function SeverityBadge({ value }: { value: string }) {
  const n = value.toLowerCase();
  const severity: Severity =
    n === "critical" || n === "high" || n === "medium" || n === "low"
      ? (n as Severity)
      : "neutral";
  return <Badge severity={severity}>{value.toUpperCase()}</Badge>;
}
