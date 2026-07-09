"use client";

import { useTranslations } from "next-intl";
import { motion } from "framer-motion";
import { CheckCircle2, User } from "lucide-react";
import { Link } from "@/i18n/navigation";

const STEPS = ["audit", "build", "launch"] as const;
const TRUST = ["t1", "t2", "t3", "t4"] as const;

export default function TrustSection() {
  const t = useTranslations("home.trust");

  return (
    <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
      <div className="grid gap-10 lg:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
            {t("title")}
          </h2>
          <p className="mt-4 leading-relaxed text-muted">{t("subtitle")}</p>
          <ul className="mt-6 space-y-3">
            {TRUST.map((key) => (
              <li key={key} className="flex items-start gap-3 text-sm">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-accent-bright" />
                <span className="text-foreground">{t(`points.${key}`)}</span>
              </li>
            ))}
          </ul>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.1 }}
          className="rounded-2xl border border-border bg-surface p-6 sm:p-8"
        >
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-accent/10">
              <User className="h-6 w-6 text-accent-bright" />
            </div>
            <div>
              <p className="font-semibold">{t("founder.name")}</p>
              <p className="text-sm text-muted">{t("founder.role")}</p>
            </div>
          </div>
          <p className="mt-4 text-sm leading-relaxed text-muted">
            {t("founder.bio")}
          </p>
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            {STEPS.map((step, i) => (
              <div key={step}>
                <span className="text-2xl font-bold text-accent/40">
                  {i + 1}
                </span>
                <p className="mt-1 text-sm font-medium">
                  {t(`steps.${step}.title`)}
                </p>
                <p className="mt-1 text-xs text-muted">
                  {t(`steps.${step}.description`)}
                </p>
              </div>
            ))}
          </div>
          <Link
            href="/contact"
            className="mt-6 inline-block text-sm font-semibold text-accent-bright transition-colors hover:text-accent"
          >
            {t("cta")} →
          </Link>
        </motion.div>
      </div>
    </section>
  );
}
