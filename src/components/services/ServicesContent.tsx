"use client";

import { useTranslations } from "next-intl";
import { motion } from "framer-motion";
import {
  Bot,
  Database,
  MessageSquare,
  RefreshCw,
  Workflow,
  type LucideIcon,
} from "lucide-react";

const SERVICES: { key: string; icon: LucideIcon }[] = [
  { key: "assistants", icon: Bot },
  { key: "automation", icon: Workflow },
  { key: "crm", icon: Database },
  { key: "agents", icon: MessageSquare },
  { key: "support", icon: RefreshCw },
];

const STEPS = ["discovery", "design", "build", "launch", "support"] as const;

const OVERVIEW_KEYS = ["l1", "l2", "l3", "l4", "l5"] as const;

export default function ServicesContent() {
  const t = useTranslations("services");

  return (
    <>
      <section className="mx-auto max-w-6xl px-4 pt-16 sm:px-6 sm:pt-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-3xl"
        >
          <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
            {t("overview.title")}
          </h2>
          <p className="mt-4 leading-relaxed text-muted">{t("overview.text")}</p>
          <ul className="mt-6 space-y-3">
            {OVERVIEW_KEYS.map((key, i) => (
              <motion.li
                key={key}
                initial={{ opacity: 0, x: -12 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.06 }}
                className="flex items-start gap-3 text-sm leading-relaxed text-foreground sm:text-base"
              >
                <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent-bright" />
                {t(`overview.list.${key}`)}
              </motion.li>
            ))}
          </ul>
        </motion.div>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-16 pt-12 sm:px-6 sm:pb-20 sm:pt-16">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {SERVICES.map(({ key, icon: Icon }, i) => (
            <motion.div
              key={key}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ duration: 0.4, delay: i * 0.06 }}
              className="group rounded-2xl border border-border bg-surface p-6 transition-colors hover:border-accent/40 hover:bg-surface-hover lg:last:col-span-1"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent/10 text-accent-bright transition-colors group-hover:bg-accent/20">
                <Icon className="h-5 w-5" />
              </div>
              <h2 className="mt-5 text-xl font-semibold">
                {t(`items.${key}.title`)}
              </h2>
              <p className="mt-3 text-sm leading-relaxed text-muted">
                {t(`items.${key}.description`)}
              </p>
              <ul className="mt-4 space-y-2">
                {(["f1", "f2", "f3"] as const).map((f) => (
                  <li
                    key={f}
                    className="flex items-start gap-2 text-sm text-muted"
                  >
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent-bright" />
                    {t(`items.${key}.features.${f}`)}
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="border-t border-border bg-surface/30">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
          <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
            {t("process.title")}
          </h2>
          <p className="mt-3 max-w-2xl text-muted">{t("process.subtitle")}</p>
          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-5">
            {STEPS.map((step, i) => (
              <motion.div
                key={step}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                className="relative"
              >
                <span className="text-4xl font-bold text-accent/30">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <h3 className="mt-2 font-semibold">
                  {t(`process.steps.${step}.title`)}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">
                  {t(`process.steps.${step}.description`)}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
