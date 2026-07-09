"use client";

import { useTranslations } from "next-intl";
import { motion } from "framer-motion";
import { Bot, Database, Workflow, type LucideIcon } from "lucide-react";
import { Link } from "@/i18n/navigation";

const PREVIEW: { key: string; icon: LucideIcon }[] = [
  { key: "assistants", icon: Bot },
  { key: "automation", icon: Workflow },
  { key: "crm", icon: Database },
];

export default function ServicesPreview() {
  const t = useTranslations("home.servicesPreview");

  return (
    <section className="border-t border-border bg-surface/30">
      <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-28">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-end"
        >
          <div>
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              {t("title")}
            </h2>
            <p className="mt-3 max-w-xl text-muted">{t("subtitle")}</p>
          </div>
          <Link
            href="/services"
            className="shrink-0 text-sm font-semibold text-accent-bright transition-colors hover:text-accent"
          >
            {t("link")} →
          </Link>
        </motion.div>

        <div className="mt-10 grid gap-4 sm:grid-cols-3">
          {PREVIEW.map(({ key, icon: Icon }, i) => (
            <motion.div
              key={key}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              className="rounded-2xl border border-border bg-surface p-6"
            >
              <Icon className="h-6 w-6 text-accent-bright" />
              <h3 className="mt-4 font-semibold">{t(`items.${key}.title`)}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">
                {t(`items.${key}.description`)}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
