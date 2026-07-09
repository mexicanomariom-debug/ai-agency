"use client";

import { useLocale } from "next-intl";
import { useCallback, useEffect, useState } from "react";
import type { Locale } from "@/i18n/routing";
import {
  DEFAULT_LATAM_COUNTRY,
  hasCountryPicker,
  isLatamCountry,
  LATAM_COUNTRY_STORAGE_KEY,
  type LatamCountry,
} from "@/lib/market";

const LATAM_COUNTRY_EVENT = "latam-country-change";

export function useLatamCountry() {
  const locale = useLocale() as Locale;
  const isLatam = hasCountryPicker(locale);
  const [country, setCountryState] = useState<LatamCountry>(DEFAULT_LATAM_COUNTRY);

  useEffect(() => {
    if (!isLatam) return;

    const stored = localStorage.getItem(LATAM_COUNTRY_STORAGE_KEY);
    if (stored && isLatamCountry(stored)) {
      setCountryState(stored);
    }

    const onCountryChange = (event: Event) => {
      const next = (event as CustomEvent<LatamCountry>).detail;
      if (next && isLatamCountry(next)) {
        setCountryState(next);
      }
    };

    window.addEventListener(LATAM_COUNTRY_EVENT, onCountryChange);
    return () => window.removeEventListener(LATAM_COUNTRY_EVENT, onCountryChange);
  }, [isLatam]);

  const setCountry = useCallback((next: LatamCountry) => {
    setCountryState(next);
    localStorage.setItem(LATAM_COUNTRY_STORAGE_KEY, next);
    window.dispatchEvent(
      new CustomEvent(LATAM_COUNTRY_EVENT, { detail: next }),
    );
  }, []);

  return { country, setCountry, isLatam };
}
