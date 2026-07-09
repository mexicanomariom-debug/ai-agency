import type { Locale } from "@/i18n/routing";

export type Market = "ru" | "es" | "latam";

export type LatamCountry = "sp" | "mx" | "co" | "ar" | "cl" | "pe";

export const LATAM_COUNTRIES: readonly LatamCountry[] = [
  "sp",
  "mx",
  "co",
  "ar",
  "cl",
  "pe",
] as const;

export const DEFAULT_LATAM_COUNTRY: LatamCountry = "mx";

export const LATAM_COUNTRY_STORAGE_KEY = "ai-agentes-latam-country";

export function getMarketForLocale(locale: Locale): Market {
  if (locale === "ru") return "ru";
  return "latam";
}

/** Country picker is shown for the Spanish locale (LATAM + España). */
export function hasCountryPicker(locale: Locale): boolean {
  return locale === "es";
}

export const COMPETITORS_BY_MARKET: Record<Market, readonly string[]> = {
  ru: ["c1", "c2", "c3"],
  es: ["c4", "c5", "c6"],
  latam: ["c7", "c8", "c9"],
};

export function isLatamCountry(value: string): value is LatamCountry {
  return (LATAM_COUNTRIES as readonly string[]).includes(value);
}
