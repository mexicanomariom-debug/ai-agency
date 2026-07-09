"use client";

import { motion } from "framer-motion";

type Props = {
  title: string;
  subtitle: string;
  description?: string;
};

export default function PageHeader({ title, subtitle, description }: Props) {
  return (
    <section className="relative overflow-hidden border-b border-border">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_-20%,var(--accent-glow),transparent)]"
      />
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-28"
      >
        <p className="text-sm font-semibold uppercase tracking-widest text-accent-bright">
          {subtitle}
        </p>
        <h1 className="mt-3 max-w-3xl text-4xl font-bold tracking-tight sm:text-5xl">
          {title}
        </h1>
        {description && (
          <p className="mt-6 max-w-2xl text-lg leading-relaxed text-muted">
            {description}
          </p>
        )}
      </motion.div>
    </section>
  );
}
