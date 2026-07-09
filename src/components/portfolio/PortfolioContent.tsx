"use client";

import { useTranslations } from "next-intl";
import { motion } from "framer-motion";
import {
  Building2,
  CreditCard,
  Mail,
  Phone,
  ShoppingBag,
  Train,
  type LucideIcon,
} from "lucide-react";

const CASES: { key: string; icon: LucideIcon }[] = [
  { key: "cp", icon: Train },
  { key: "siemens", icon: Phone },
  { key: "stannp", icon: Mail },
  { key: "retailer", icon: ShoppingBag },
  { key: "klarna", icon: CreditCard },
  { key: "logistics", icon: Building2 },
];

const METRICS = ["m1", "m2", "m3"] as const;
const STACK = ["s1", "s2", "s3"] as const;

export default function PortfolioContent() {
  const t = useTranslations("portfolio");

  return (
    <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
      <motion.p
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-3xl text-lg leading-relaxed text-muted"
      >
        {t("intro")}
      </motion.p>

      <div className="mt-12 space-y-8">
        {CASES.map(({ key, icon: Icon }, i) => (
          <motion.article
            key={key}
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ duration: 0.45, delay: i * 0.05 }}
            className="overflow-hidden rounded-2xl border border-border bg-surface"
          >
            <div className="border-b border-border px-6 py-5 sm:px-8">
              <div className="flex flex-wrap items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent/10 text-accent-bright">
                  <Icon className="h-5 w-5" />
                </div>
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-xl font-semibold">
                      {t(`cases.${key}.company`)}
                    </h2>
                    <span className="rounded-full border border-border bg-background px-2.5 py-0.5 text-xs text-muted">
                      {t(`cases.${key}.industry`)}
                    </span>
                    <span className="text-xs text-muted">
                      {t(`cases.${key}.year`)}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-accent-bright">
                    {t(`cases.${key}.title`)}
                  </p>
                </div>
              </div>
            </div>

            <div className="grid gap-6 px-6 py-6 sm:px-8 lg:grid-cols-2">
              <div>
                <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">
                  {t("labels.challenge")}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-foreground">
                  {t(`cases.${key}.challenge`)}
                </p>
                <h3 className="mt-5 text-sm font-semibold uppercase tracking-wider text-muted">
                  {t("labels.solution")}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-foreground">
                  {t(`cases.${key}.solution`)}
                </p>
              </div>

              <div>
                <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">
                  {t("labels.results")}
                </h3>
                <dl className="mt-3 grid grid-cols-3 gap-3">
                  {METRICS.map((m) => (
                    <div
                      key={m}
                      className="rounded-xl border border-border bg-background p-3 text-center"
                    >
                      <dt className="sr-only">
                        {t(`cases.${key}.results.${m}.label`)}
                      </dt>
                      <dd className="text-lg font-bold text-accent-bright">
                        {t(`cases.${key}.results.${m}.value`)}
                      </dd>
                      <dd className="mt-1 text-xs text-muted">
                        {t(`cases.${key}.results.${m}.label`)}
                      </dd>
                    </div>
                  ))}
                </dl>

                <h3 className="mt-5 text-sm font-semibold uppercase tracking-wider text-muted">
                  {t("labels.stack")}
                </h3>
                <div className="mt-2 flex flex-wrap gap-2">
                  {STACK.map((s) => (
                    <span
                      key={s}
                      className="rounded-lg border border-border bg-background px-2.5 py-1 text-xs text-muted"
                    >
                      {t(`cases.${key}.stack.${s}`)}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </motion.article>
        ))}
      </div>

      <motion.p
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        className="mt-10 text-center text-xs text-muted"
      >
        {t("disclaimer")}
      </motion.p>
    </section>
  );
}
