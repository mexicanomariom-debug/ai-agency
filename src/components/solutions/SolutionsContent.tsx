"use client";

import { useTranslations } from "next-intl";
import { motion } from "framer-motion";
import {
  Clock,
  FileText,
  Headphones,
  ShoppingCart,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";

const CASES = [
  { key: "support", icon: Headphones },
  { key: "leads", icon: TrendingUp },
  { key: "documents", icon: FileText },
  { key: "ecommerce", icon: ShoppingCart },
  { key: "scheduling", icon: Clock },
] as const;

export default function SolutionsContent() {
  const t = useTranslations("solutions");

  return (
    <>
      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
        <p className="max-w-3xl text-lg leading-relaxed text-muted">
          {t("intro")}
        </p>

        <div className="mt-12 space-y-6">
          {CASES.map(({ key, icon: Icon }, i) => (
            <motion.article
              key={key}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ duration: 0.4, delay: i * 0.06 }}
              className="rounded-2xl border border-border bg-surface p-6 sm:p-8"
            >
              <div className="flex flex-col gap-6 sm:flex-row sm:items-start">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-accent/10 text-accent-bright">
                  <Icon className="h-6 w-6" />
                </div>
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-3">
                    <h2 className="text-xl font-semibold">
                      {t(`cases.${key}.title`)}
                    </h2>
                    <span className="rounded-full border border-accent/30 bg-accent/10 px-3 py-0.5 text-xs font-medium text-accent-bright">
                      {t(`cases.${key}.industry`)}
                    </span>
                  </div>
                  <p className="mt-3 leading-relaxed text-muted">
                    {t(`cases.${key}.problem`)}
                  </p>
                  <p className="mt-3 leading-relaxed text-foreground">
                    {t(`cases.${key}.solution`)}
                  </p>
                  <dl className="mt-6 grid grid-cols-3 gap-4 rounded-xl border border-border bg-background p-4">
                    {(["metric1", "metric2", "metric3"] as const).map((m) => (
                      <div key={m}>
                        <dt className="text-xs text-muted">
                          {t(`cases.${key}.results.${m}.label`)}
                        </dt>
                        <dd className="mt-1 text-lg font-bold text-accent-bright">
                          {t(`cases.${key}.results.${m}.value`)}
                        </dd>
                      </div>
                    ))}
                  </dl>
                </div>
              </div>
            </motion.article>
          ))}
        </div>
      </section>

      <section className="border-t border-border bg-surface/30">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
          <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
            {t("impact.title")}
          </h2>
          <p className="mt-3 max-w-2xl text-muted">{t("impact.subtitle")}</p>
          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {(["time", "cost", "quality", "scale"] as const).map((key, i) => (
              <motion.div
                key={key}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                className="rounded-2xl border border-border bg-surface p-6 text-center"
              >
                <p className="text-3xl font-bold text-accent-bright">
                  {t(`impact.items.${key}.value`)}
                </p>
                <p className="mt-2 text-sm text-muted">
                  {t(`impact.items.${key}.label`)}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
