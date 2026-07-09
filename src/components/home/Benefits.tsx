"use client";

import { useTranslations } from "next-intl";
import { motion } from "framer-motion";
import { Layers, Target, Wallet, Zap, type LucideIcon } from "lucide-react";

const BENEFITS: { key: string; icon: LucideIcon }[] = [
  { key: "speed", icon: Zap },
  { key: "cost", icon: Wallet },
  { key: "scale", icon: Layers },
  { key: "accuracy", icon: Target },
];

export default function Benefits() {
  const t = useTranslations("home.benefits");

  return (
    <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-28">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.5 }}
        className="max-w-2xl"
      >
        <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
          {t("title")}
        </h2>
        <p className="mt-3 text-base text-muted sm:text-lg">{t("subtitle")}</p>
      </motion.div>

      <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {BENEFITS.map(({ key, icon: Icon }, i) => (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.5, delay: i * 0.08 }}
            className="group rounded-2xl border border-border bg-surface p-6 transition-colors hover:border-accent/40 hover:bg-surface-hover"
          >
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent/10 text-accent-bright transition-colors group-hover:bg-accent/20">
              <Icon className="h-5 w-5" />
            </div>
            <h3 className="mt-5 text-lg font-semibold">
              {t(`items.${key}.title`)}
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              {t(`items.${key}.description`)}
            </p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
