"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";
import { Link } from "@/i18n/navigation";

const SLIDES = [
  "dental",
  "medical",
  "beauty",
  "food",
  "logistics",
  "realestate",
] as const;

const SLIDE_INTERVAL_MS = 5000;

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

const slideVariants = {
  enter: { opacity: 0, y: 20 },
  center: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -16 },
};

export default function Hero() {
  const t = useTranslations("home.hero");
  const tStats = useTranslations("home.stats");
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % SLIDES.length);
    }, SLIDE_INTERVAL_MS);

    return () => clearInterval(timer);
  }, []);

  const activeSlide = SLIDES[activeIndex];

  return (
    <section className="relative overflow-hidden">
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
        <motion.div variants={item} className="flex flex-col items-center gap-3">
          <div className="flex items-center gap-2 rounded-full border border-border bg-surface px-4 py-1.5 text-xs font-medium text-muted sm:text-sm">
            <Sparkles className="h-3.5 w-3.5 text-accent-bright" />
            {t("badge")}
          </div>

          <AnimatePresence mode="wait">
            <motion.div
              key={activeSlide}
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
              transition={{ duration: 0.25 }}
              className="rounded-full border border-accent/30 bg-accent/10 px-4 py-1 text-xs font-semibold text-accent-bright sm:text-sm"
            >
              {t(`slides.${activeSlide}.label`)}
            </motion.div>
          </AnimatePresence>
        </motion.div>

        <div className="relative mt-8 min-h-[9rem] w-full max-w-4xl sm:min-h-[11rem] lg:min-h-[12rem]">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeSlide}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
              className="absolute inset-0 flex flex-col items-center justify-center"
            >
              <h1 className="text-4xl font-bold leading-[1.1] tracking-tight sm:text-6xl lg:text-7xl">
                <span className="bg-gradient-to-b from-foreground to-muted bg-clip-text text-transparent">
                  {t(`slides.${activeSlide}.title`)}
                </span>
              </h1>
              <p className="mt-6 max-w-2xl text-base leading-relaxed text-muted sm:text-lg">
                {t(`slides.${activeSlide}.subtitle`)}
              </p>
            </motion.div>
          </AnimatePresence>
        </div>

        <motion.div
          variants={item}
          className="mt-4 flex items-center gap-2"
          role="tablist"
          aria-label={t("slidesAria")}
        >
          {SLIDES.map((slide, index) => (
            <button
              key={slide}
              type="button"
              role="tab"
              aria-selected={index === activeIndex}
              aria-label={t(`slides.${slide}.label`)}
              onClick={() => setActiveIndex(index)}
              className={`h-2 rounded-full transition-all ${
                index === activeIndex
                  ? "w-8 bg-accent-bright"
                  : "w-2 bg-border hover:bg-muted"
              }`}
            />
          ))}
        </motion.div>

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
