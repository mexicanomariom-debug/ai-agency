"use client";

import { useTranslations } from "next-intl";
import { motion } from "framer-motion";
import {
  Eye,
  Heart,
  Lightbulb,
  Shield,
  type LucideIcon,
} from "lucide-react";

const VALUES: { key: string; icon: LucideIcon }[] = [
  { key: "innovation", icon: Lightbulb },
  { key: "transparency", icon: Eye },
  { key: "results", icon: Heart },
  { key: "security", icon: Shield },
];

const TECH = ["llm", "automation", "integrations", "cloud"] as const;

export default function AboutContent() {
  const t = useTranslations("about");

  return (
    <>
      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-3xl"
        >
          <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
            {t("story.title")}
          </h2>
          <p className="mt-4 leading-relaxed text-muted">{t("story.p1")}</p>
          <p className="mt-4 leading-relaxed text-muted">{t("story.p2")}</p>
        </motion.div>

        <div className="mt-16 grid gap-8 lg:grid-cols-2">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="rounded-2xl border border-border bg-surface p-8"
          >
            <h3 className="text-lg font-semibold text-accent-bright">
              {t("mission.label")}
            </h3>
            <p className="mt-3 leading-relaxed text-muted">{t("mission.text")}</p>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="rounded-2xl border border-border bg-surface p-8"
          >
            <h3 className="text-lg font-semibold text-accent-bright">
              {t("vision.label")}
            </h3>
            <p className="mt-3 leading-relaxed text-muted">{t("vision.text")}</p>
          </motion.div>
        </div>
      </section>

      <section className="border-t border-border bg-surface/30">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
          <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
            {t("values.title")}
          </h2>
          <p className="mt-3 max-w-2xl text-muted">{t("values.subtitle")}</p>
          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {VALUES.map(({ key, icon: Icon }, i) => (
              <motion.div
                key={key}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08 }}
                className="rounded-2xl border border-border bg-surface p-6"
              >
                <Icon className="h-6 w-6 text-accent-bright" />
                <h3 className="mt-4 font-semibold">
                  {t(`values.items.${key}.title`)}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">
                  {t(`values.items.${key}.description`)}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
        <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
          {t("tech.title")}
        </h2>
        <p className="mt-3 max-w-2xl text-muted">{t("tech.subtitle")}</p>
        <div className="mt-10 grid gap-4 sm:grid-cols-2">
          {TECH.map((key, i) => (
            <motion.div
              key={key}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              className="rounded-2xl border border-border bg-surface p-6"
            >
              <h3 className="font-semibold">{t(`tech.items.${key}.title`)}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">
                {t(`tech.items.${key}.description`)}
              </p>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mt-16 rounded-2xl border border-accent/30 bg-accent/5 p-8"
        >
          <h3 className="text-xl font-semibold">{t("founder.title")}</h3>
          <p className="mt-1 text-accent-bright">{t("founder.name")}</p>
          <p className="mt-1 text-sm text-muted">{t("founder.role")}</p>
          <p className="mt-4 leading-relaxed text-muted">{t("founder.bio")}</p>
        </motion.div>
      </section>
    </>
  );
}
