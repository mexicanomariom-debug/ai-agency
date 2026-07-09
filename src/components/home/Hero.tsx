"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";
import { Link } from "@/i18n/navigation";
import FallingStars from "./FallingStars";

const SLIDES = [
  "dental",
  "medical",
  "beauty",
  "food",
  "logistics",
  "realestate",
] as const;

const SLIDE_INTERVAL_MS = 5500;

export default function Hero() {
  const t = useTranslations("home.hero");
  const tStats = useTranslations("home.stats");
  const [activeIndex, setActiveIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    if (isPaused) return;

    const timer = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % SLIDES.length);
    }, SLIDE_INTERVAL_MS);

    return () => clearInterval(timer);
  }, [isPaused]);

  const activeSlide = SLIDES[activeIndex];

  return (
    <section className="relative overflow-hidden">
      <FallingStars slideIndex={activeIndex} />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_-10%,var(--accent-glow),transparent)]"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,var(--border)_1px,transparent_1px),linear-gradient(to_bottom,var(--border)_1px,transparent_1px)] bg-[size:56px_56px] opacity-20 [mask-image:radial-gradient(ellipse_70%_60%_at_50%_0%,black,transparent)]"
      />

      <div className="relative z-10 mx-auto flex max-w-6xl flex-col items-center px-4 pb-10 pt-16 text-center sm:px-6 sm:pb-28 sm:pt-32">
        <div className="flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1 text-[11px] font-medium text-muted sm:px-4 sm:py-1.5 sm:text-sm">
          <Sparkles className="h-3.5 w-3.5 shrink-0 text-accent-bright" />
          {t("badge")}
        </div>

        <div
          className="mt-5 w-full max-w-4xl sm:mt-8"
          onMouseEnter={() => setIsPaused(true)}
          onMouseLeave={() => setIsPaused(false)}
          onFocusCapture={() => setIsPaused(true)}
          onBlurCapture={() => setIsPaused(false)}
        >
          {/* Fixed-height slide area — no absolute positioning */}
          <div className="overflow-hidden">
            <div className="flex min-h-[9rem] flex-col items-center justify-center sm:min-h-[15.5rem] lg:min-h-[16.5rem]">
              <AnimatePresence mode="wait" initial={false}>
                <motion.div
                  key={activeSlide}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.35, ease: "easeInOut" }}
                  className="flex w-full flex-col items-center"
                >
                  <span className="mb-3 inline-flex rounded-full border border-accent/30 bg-accent/10 px-3 py-0.5 text-[11px] font-semibold text-accent-bright sm:mb-5 sm:px-4 sm:py-1 sm:text-sm">
                    {t(`slides.${activeSlide}.label`)}
                  </span>

                  <h1 className="text-2xl font-bold leading-[1.15] tracking-tight sm:text-5xl lg:text-6xl">
                    <span className="bg-gradient-to-b from-foreground to-muted bg-clip-text text-transparent">
                      {t(`slides.${activeSlide}.title`)}
                    </span>
                  </h1>

                  <p className="mt-3 line-clamp-2 max-w-2xl text-xs leading-relaxed text-muted sm:mt-5 sm:line-clamp-none sm:text-base lg:text-lg">
                    {t(`slides.${activeSlide}.subtitle`)}
                  </p>
                </motion.div>
              </AnimatePresence>
            </div>
          </div>

          {/* Dots — static layout, outside animated area */}
          <div
            className="mt-4 flex items-center justify-center gap-2 sm:mt-6 sm:gap-2.5"
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
                className="flex h-6 w-6 items-center justify-center"
              >
                <span
                  className={`block rounded-full transition-all duration-300 ${
                    index === activeIndex
                      ? "h-2 w-7 bg-accent-bright"
                      : "h-2 w-2 bg-border hover:bg-muted"
                  }`}
                />
              </button>
            ))}
          </div>
        </div>

        <div className="mt-6 flex w-full flex-col items-stretch gap-2 sm:mt-10 sm:w-auto sm:flex-row sm:items-center sm:gap-3">
          <Link
            href="/contact"
            className="group flex w-full items-center justify-center gap-2 rounded-xl bg-accent px-5 py-2.5 text-sm font-semibold text-white shadow-[0_0_32px_var(--accent-glow)] transition-all hover:bg-accent-bright hover:shadow-[0_0_48px_var(--accent-glow)] sm:w-auto sm:px-7 sm:py-3.5"
          >
            {t("ctaPrimary")}
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
          </Link>
          <Link
            href="/services"
            className="flex w-full items-center justify-center rounded-xl border border-border bg-surface px-5 py-2.5 text-sm font-semibold text-foreground transition-colors hover:border-accent/50 hover:bg-surface-hover sm:w-auto sm:px-7 sm:py-3.5"
          >
            {t("ctaSecondary")}
          </Link>
        </div>

        <dl className="mt-8 grid w-full max-w-3xl grid-cols-3 gap-2 sm:mt-20 sm:gap-4">
          {(["cost", "uptime", "speed"] as const).map((key) => (
            <div
              key={key}
              className="rounded-xl border border-border bg-surface/60 px-2 py-3 backdrop-blur-sm sm:rounded-2xl sm:px-6 sm:py-5"
            >
              <dt className="sr-only">{tStats(`${key}.label`)}</dt>
              <dd className="text-lg font-bold text-accent-bright sm:text-3xl">
                {tStats(`${key}.value`)}
              </dd>
              <dd className="mt-0.5 text-[9px] leading-snug text-muted sm:mt-1.5 sm:text-xs sm:leading-relaxed">
                {tStats(`${key}.label`)}
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}
