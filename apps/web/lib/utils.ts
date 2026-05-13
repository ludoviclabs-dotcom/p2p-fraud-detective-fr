import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Helper shadcn/ui — merge Tailwind classes en évitant les conflits. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Locale FR — formatage monétaire € (jamais .toLocaleString() nu). */
const _EUR = new Intl.NumberFormat("fr-FR", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 0,
});

export function formatEur(value: number | null | undefined): string {
  if (value == null) return "—";
  return _EUR.format(value);
}

/** Locale FR — date courte. */
const _DATE = new Intl.DateTimeFormat("fr-FR", {
  dateStyle: "medium",
});

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return _DATE.format(new Date(iso));
  } catch {
    return iso;
  }
}
