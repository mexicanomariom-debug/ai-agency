"use client";

import { useTranslations } from "next-intl";
import { motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";
import { Link } from "@/i18n/navigation";

const container = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.12 } },
};

const item = {
  hidden: { opacity: 0, y: 24 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] as const },
  },
};

export default function Hero() {
  const t = useTranslations("home.hero");
  const tStats = useTranslations("home.stats");

  return (
    <section className="relative overflow-hidden">
      {/* Background: radial glow + subtle grid */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_-10%,var(--accent-glow),transparent)]"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,var(--border)_1px,transparent_1px),linear-gradient(to_bottom,var(--border)_1px,transparent_1px)] bg-[size:56px_56px] opacity-20 [mask-image:radial-gradient(ellipse_70%_60%_at_50%_0%,black,transparent)]"
      />

      <motion.div
        variants={container}
        initial="hidden"
        animate="visible"
        className="relative mx-auto flex max-w-6xl flex-col items-center px-4 pb-20 pt-24 text-center sm:px-6 sm:pb-28 sm:pt-32"
      >
        <motion.div
          variants={item}
          className="flex items-center gap-2 rounded-full border border-border bg-surface px-4 py-1.5 text-xs font-medium text-muted sm:text-sm"
        >
          <Sparkles className="h-3.5 w-3.5 text-accent-bright" />
          {t("badge")}
        </motion.div>

        <motion.h1
          variants={item}
          className="mt-8 max-w-4xl text-4xl font-bold leading-[1.1] tracking-tight sm:text-6xl lg:text-7xl"
        >
          <span className="bg-gradient-to-b from-foreground to-muted bg-clip-text text-transparent">
            {t("title")}
          </span>
        </motion.h1>

        <motion.p
          variants={item}
          className="mt-6 max-w-2xl text-base leading-relaxed text-muted sm:text-lg"
        >
          {t("subtitle")}
        </motion.p>

        <motion.div
          variants={item}
          className="mt-10 flex w-full flex-col items-center gap-3 sm:w-auto sm:flex-row"
        >
          <Link
            href="/contact"
            className="group flex w-full items-center justify-center gap-2 rounded-xl bg-accent px-7 py-3.5 text-sm font-semibold text-white shadow-[0_0_32px_var(--accent-glow)] transition-all hover:bg-accent-bright hover:shadow-[0_0_48px_var(--accent-glow)] sm:w-auto"
          >
            {t("ctaPrimary")}
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
          </Link>
          <Link
            href="/services"
            className="flex w-full items-center justify-center rounded-xl border border-border bg-surface px-7 py-3.5 text-sm font-semibold text-foreground transition-colors hover:border-accent/50 hover:bg-surface-hover sm:w-auto"
          >
            {t("ctaSecondary")}
          </Link>
        </motion.div>

        <motion.dl
          variants={item}
          className="mt-20 grid w-full max-w-3xl grid-cols-1 gap-4 sm:grid-cols-3"
        >
          {(["cost", "uptime", "speed"] as const).map((key) => (
            <div
              key={key}
              className="rounded-2xl border border-border bg-surface/60 px-6 py-5 backdrop-blur-sm"
            >
              <dt className="sr-only">{tStats(`${key}.label`)}</dt>
              <dd className="text-3xl font-bold text-accent-bright">
                {tStats(`${key}.value`)}
              </dd>
              <dd className="mt-1.5 text-xs leading-relaxed text-muted">
                {tStats(`${key}.label`)}
              </dd>
            </div>
          ))}
        </motion.dl>
      </motion.div>
    </section>
  );
}
