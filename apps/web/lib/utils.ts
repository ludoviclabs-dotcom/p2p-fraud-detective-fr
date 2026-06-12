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

/**
 * Locale FR — date + heure horodatée, fuseau Europe/Paris épinglé.
 *
 * Le fuseau explicite est requis pour le rendu SSR : sans lui, le serveur
 * (UTC) et le client (navigateur) produisent un texte différent, ce qui
 * déclenche une erreur d'hydratation React #418. Ne jamais revenir à un
 * `.toLocaleString()` nu sur une valeur rendue côté serveur.
 */
const _DATE_TIME = new Intl.DateTimeFormat("fr-FR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  timeZone: "Europe/Paris",
});

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return _DATE_TIME.format(new Date(iso));
  } catch {
    return iso ?? "—";
  }
}
