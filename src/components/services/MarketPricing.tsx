"use client";

import { useLocale, useTranslations } from "next-intl";
import { motion } from "framer-motion";
import type { Locale } from "@/i18n/routing";
import { useLatamCountry } from "@/hooks/useLatamCountry";
import {
  COMPETITORS_BY_MARKET,
  getMarketForLocale,
} from "@/lib/market";
import LatamCountryPicker from "./LatamCountryPicker";

const PACKAGES = ["starter", "business", "pro", "enterprise"] as const;

export default function MarketPricing() {
  const locale = useLocale() as Locale;
  const market = getMarketForLocale(locale);
  const { country, setCountry, isLatam } = useLatamCountry();
  const competitors = COMPETITORS_BY_MARKET[market];
  const t = useTranslations("services.pricing");
  const tLatam = useTranslations("services.latamCountries");

  const marketName = isLatam
    ? tLatam(`${country}.name`)
    : t(`markets.${market}.name`);

  const marketCurrency = isLatam
    ? tLatam(`${country}.currency`)
    : t(`markets.${market}.currency`);

  const packagePrice = (pkg: (typeof PACKAGES)[number]) =>
    isLatam
      ? tLatam(`${country}.packages.${pkg}.price`)
      : t(`markets.${market}.packages.${pkg}.price`);

  const packageSupport = (pkg: (typeof PACKAGES)[number]) =>
    isLatam
      ? tLatam(`${country}.packages.${pkg}.support`)
      : t(`markets.${market}.packages.${pkg}.support`);

  return (
    <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
      <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
        {t("title")}
      </h2>
      <p className="mt-3 max-w-3xl text-muted">{t("subtitle")}</p>
      <p className="mt-2 text-sm text-muted">{t("note")}</p>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="mx-auto mt-10 max-w-5xl rounded-2xl border border-border bg-surface p-6 sm:p-8"
      >
        {isLatam && (
          <LatamCountryPicker country={country} onChange={setCountry} />
        )}

        <div className="mb-6 border-b border-border pb-4 text-center">
          <h3 className="text-lg font-semibold">{marketName}</h3>
          <p className="mt-1 text-xs text-muted">{marketCurrency}</p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {PACKAGES.map((pkg) => (
            <div
              key={pkg}
              className={`flex h-full min-h-[8.5rem] flex-col rounded-xl border p-4 ${
                pkg === "business"
                  ? "border-accent/40 bg-accent/5"
                  : "border-border bg-background"
              }`}
            >
              <div className="flex min-h-6 items-center justify-between gap-2">
                <span className="text-sm font-medium">
                  {t(`packages.${pkg}.name`)}
                </span>
                {pkg === "business" ? (
                  <span className="shrink-0 rounded-full bg-accent px-2 py-0.5 text-[10px] font-semibold text-white">
                    {t("popular")}
                  </span>
                ) : (
                  <span className="h-5 w-14 shrink-0" aria-hidden />
                )}
              </div>
              <div className="mt-auto pt-4">
                <p className="text-xl font-bold leading-tight text-accent-bright">
                  {packagePrice(pkg)}
                </p>
                <p className="mt-1 min-h-[2rem] text-xs leading-relaxed text-muted">
                  {packageSupport(pkg)}
                </p>
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      <div className="mt-16">
        <h3 className="text-xl font-bold tracking-tight">
          {t("competitors.title")}
        </h3>
        <p className="mt-2 max-w-3xl text-sm text-muted">
          {t("competitors.subtitle")}
        </p>
        <div className="mt-6 overflow-x-auto rounded-2xl border border-border">
          <table className="w-full min-w-[480px] text-left text-sm">
            <thead>
              <tr className="border-b border-border bg-surface">
                <th className="px-4 py-3 font-semibold">
                  {t("competitors.headers.company")}
                </th>
                <th className="px-4 py-3 font-semibold">
                  {t("competitors.headers.theirPrice")}
                </th>
                <th className="px-4 py-3 font-semibold text-accent-bright">
                  {t("competitors.headers.ourPrice")}
                </th>
              </tr>
            </thead>
            <tbody>
              {competitors.map((key) => (
                <tr key={key} className="border-b border-border last:border-0">
                  <td className="px-4 py-3 font-medium">
                    {isLatam
                      ? tLatam(`${country}.competitors.${key}.company`)
                      : t(`competitors.items.${key}.company`)}
                  </td>
                  <td className="px-4 py-3 text-muted">
                    {isLatam
                      ? tLatam(`${country}.competitors.${key}.theirPrice`)
                      : t(`competitors.items.${key}.theirPrice`)}
                  </td>
                  <td className="px-4 py-3 font-semibold text-accent-bright">
                    {isLatam
                      ? tLatam(`${country}.competitors.${key}.ourPrice`)
                      : t(`competitors.items.${key}.ourPrice`)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-4 text-xs text-muted">{t("competitors.disclaimer")}</p>
      </div>
    </section>
  );
}
