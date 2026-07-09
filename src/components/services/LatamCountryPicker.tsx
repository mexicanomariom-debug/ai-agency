"use client";

import { useTranslations } from "next-intl";
import { LATAM_COUNTRIES, type LatamCountry } from "@/lib/market";

type Props = {
  country: LatamCountry;
  onChange: (country: LatamCountry) => void;
};

export default function LatamCountryPicker({ country, onChange }: Props) {
  const t = useTranslations("services.latamCountries");

  return (
    <div className="mb-6">
      <p className="mb-3 text-center text-xs font-medium text-muted">
        {t("label")}
      </p>
      <div className="flex flex-wrap justify-center gap-2">
        {LATAM_COUNTRIES.map((code) => (
          <button
            key={code}
            type="button"
            onClick={() => onChange(code)}
            className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors sm:px-4 sm:text-sm ${
              country === code
                ? "border-accent bg-accent/10 text-accent-bright"
                : "border-border bg-background text-muted hover:border-accent/40 hover:text-foreground"
            }`}
          >
            {t(`${code}.shortName`)}
          </button>
        ))}
      </div>
    </div>
  );
}
