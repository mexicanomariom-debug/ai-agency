"use client";

import { useTranslations } from "next-intl";
import { motion } from "framer-motion";
import {
  Building2,
  Headphones,
  HeartPulse,
  Pizza,
  Scissors,
  Stethoscope,
  type LucideIcon,
} from "lucide-react";

const INDUSTRIES: { key: string; icon: LucideIcon }[] = [
  { key: "dental", icon: Stethoscope },
  { key: "medical", icon: HeartPulse },
  { key: "beauty", icon: Scissors },
  { key: "food", icon: Pizza },
  { key: "delivery", icon: Building2 },
  { key: "operators", icon: Headphones },
];

export default function IndustriesSection() {
  const t = useTranslations("home.industries");

  return (
    <section className="border-t border-border bg-surface/30">
      <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-28">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-3xl"
        >
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            {t("title")}
          </h2>
          <p className="mt-4 text-lg leading-relaxed text-muted">
            {t("subtitle")}
          </p>
        </motion.div>

        <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {INDUSTRIES.map(({ key, icon: Icon }, i) => (
            <motion.div
              key={key}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ delay: i * 0.06 }}
              className="rounded-2xl border border-border bg-surface p-6"
            >
              <Icon className="h-6 w-6 text-accent-bright" />
              <h3 className="mt-4 font-semibold">{t(`items.${key}.title`)}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">
                {t(`items.${key}.description`)}
              </p>
              <ul className="mt-4 space-y-1.5">
                {(["e1", "e2", "e3"] as const).map((e) => (
                  <li
                    key={e}
                    className="flex items-start gap-2 text-xs text-muted"
                  >
                    <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-accent-bright" />
                    {t(`items.${key}.examples.${e}`)}
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
