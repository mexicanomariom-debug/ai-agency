"use client";

import { useLocale, useTranslations } from "next-intl";
import { motion } from "framer-motion";
import type { Locale } from "@/i18n/routing";
import {
  COMPETITORS_BY_MARKET,
  getMarketForLocale,
} from "@/lib/market";

const PACKAGES = ["starter", "business", "pro", "enterprise"] as const;

export default function MarketPricing() {
  const locale = useLocale() as Locale;
  const market = getMarketForLocale(locale);
  const competitors = COMPETITORS_BY_MARKET[market];
  const t = useTranslations("services.pricing");

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
        <div className="mb-6 border-b border-border pb-4 text-center">
          <h3 className="text-lg font-semibold">
            {t(`markets.${market}.name`)}
          </h3>
          <p className="mt-1 text-xs text-muted">
            {t(`markets.${market}.currency`)}
          </p>
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
                  {t(`markets.${market}.packages.${pkg}.price`)}
                </p>
                <p className="mt-1 min-h-[2rem] text-xs leading-relaxed text-muted">
                  {t(`markets.${market}.packages.${pkg}.support`)}
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
                    {t(`competitors.items.${key}.company`)}
                  </td>
                  <td className="px-4 py-3 text-muted">
                    {t(`competitors.items.${key}.theirPrice`)}
                  </td>
                  <td className="px-4 py-3 font-semibold text-accent-bright">
                    {t(`competitors.items.${key}.ourPrice`)}
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
