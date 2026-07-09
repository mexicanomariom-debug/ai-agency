"use client";

import { useTranslations } from "next-intl";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { Link } from "@/i18n/navigation";

export default function CtaSection() {
  const t = useTranslations("home.cta");

  return (
    <section className="mx-auto max-w-6xl px-4 pb-24 sm:px-6">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.6 }}
        className="relative overflow-hidden rounded-3xl border border-border bg-surface px-6 py-16 text-center sm:px-12 sm:py-20"
      >
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_50%_80%_at_50%_120%,var(--accent-glow),transparent)]"
        />
        <div className="relative">
          <h2 className="mx-auto max-w-2xl text-3xl font-bold tracking-tight sm:text-4xl">
            {t("title")}
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-base text-muted sm:text-lg">
            {t("subtitle")}
          </p>
          <Link
            href="/contact"
            className="group mt-8 inline-flex items-center gap-2 rounded-xl bg-accent px-8 py-4 text-sm font-semibold text-white shadow-[0_0_32px_var(--accent-glow)] transition-all hover:bg-accent-bright hover:shadow-[0_0_48px_var(--accent-glow)]"
          >
            {t("button")}
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
          </Link>
        </div>
      </motion.div>
    </section>
  );
}
