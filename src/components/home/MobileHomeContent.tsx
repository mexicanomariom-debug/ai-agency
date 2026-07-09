"use client";

import { useTranslations } from "next-intl";
import {
  Bot,
  Building2,
  CheckCircle2,
  Database,
  Headphones,
  HeartPulse,
  Layers,
  Pizza,
  Scissors,
  Stethoscope,
  Target,
  User,
  Wallet,
  Workflow,
  Zap,
  type LucideIcon,
} from "lucide-react";
import { Link } from "@/i18n/navigation";

const TRUST = ["t1", "t2", "t3", "t4"] as const;
const STEPS = ["audit", "build", "launch"] as const;

const INDUSTRIES: { key: string; icon: LucideIcon }[] = [
  { key: "dental", icon: Stethoscope },
  { key: "medical", icon: HeartPulse },
  { key: "beauty", icon: Scissors },
  { key: "food", icon: Pizza },
  { key: "delivery", icon: Building2 },
  { key: "operators", icon: Headphones },
];

const BENEFITS: { key: string; icon: LucideIcon }[] = [
  { key: "speed", icon: Zap },
  { key: "cost", icon: Wallet },
  { key: "scale", icon: Layers },
  { key: "accuracy", icon: Target },
];

const SERVICES: { key: string; icon: LucideIcon }[] = [
  { key: "assistants", icon: Bot },
  { key: "automation", icon: Workflow },
  { key: "crm", icon: Database },
];

export default function MobileHomeContent() {
  const tTrust = useTranslations("home.trust");
  const tIndustries = useTranslations("home.industries");
  const tBenefits = useTranslations("home.benefits");
  const tServices = useTranslations("home.servicesPreview");
  const tCta = useTranslations("home.cta");
  const tNav = useTranslations("nav");

  return (
    <div className="mx-auto max-w-6xl px-4 pb-12 sm:hidden">
      {/* Trust + process */}
      <section className="rounded-2xl border border-border bg-surface/60 p-4">
        <h2 className="text-lg font-bold tracking-tight">{tTrust("title")}</h2>
        <ul className="mt-3 grid grid-cols-2 gap-x-2 gap-y-2">
          {TRUST.map((key) => (
            <li key={key} className="flex items-start gap-1.5 text-[11px] leading-snug">
              <CheckCircle2 className="mt-0.5 h-3 w-3 shrink-0 text-accent-bright" />
              <span>{tTrust(`points.${key}`)}</span>
            </li>
          ))}
        </ul>

        <div className="mt-4 flex items-center gap-2.5 border-t border-border pt-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent/10">
            <User className="h-4 w-4 text-accent-bright" />
          </div>
          <div className="min-w-0 text-xs">
            <p className="truncate font-semibold">{tTrust("founder.name")}</p>
            <p className="truncate text-muted">{tTrust("founder.role")}</p>
          </div>
        </div>

        <ol className="mt-3 grid grid-cols-3 gap-2">
          {STEPS.map((step, i) => (
            <li
              key={step}
              className="rounded-xl border border-border bg-background/50 px-2 py-2 text-center"
            >
              <span className="text-sm font-bold text-accent-bright">{i + 1}</span>
              <p className="mt-0.5 text-[10px] font-medium leading-tight">
                {tTrust(`steps.${step}.title`)}
              </p>
            </li>
          ))}
        </ol>
      </section>

      {/* Industries */}
      <section className="mt-4">
        <div className="flex items-end justify-between gap-3">
          <h2 className="text-lg font-bold tracking-tight">{tIndustries("title")}</h2>
          <Link
            href="/solutions"
            className="shrink-0 text-xs font-semibold text-accent-bright"
          >
            {tNav("solutions")} →
          </Link>
        </div>
        <div className="mt-3 grid grid-cols-2 gap-2">
          {INDUSTRIES.map(({ key, icon: Icon }) => (
            <div
              key={key}
              className="rounded-xl border border-border bg-surface p-3"
            >
              <Icon className="h-4 w-4 text-accent-bright" />
              <h3 className="mt-2 text-xs font-semibold leading-tight">
                {tIndustries(`items.${key}.title`)}
              </h3>
              <p className="mt-1 line-clamp-2 text-[10px] leading-snug text-muted">
                {tIndustries(`items.${key}.description`)}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Benefits */}
      <section className="mt-4">
        <h2 className="text-lg font-bold tracking-tight">{tBenefits("title")}</h2>
        <div className="mt-3 grid grid-cols-2 gap-2">
          {BENEFITS.map(({ key, icon: Icon }) => (
            <div
              key={key}
              className="flex gap-2.5 rounded-xl border border-border bg-surface p-3"
            >
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent/10">
                <Icon className="h-3.5 w-3.5 text-accent-bright" />
              </div>
              <div className="min-w-0">
                <h3 className="text-xs font-semibold leading-tight">
                  {tBenefits(`items.${key}.title`)}
                </h3>
                <p className="mt-0.5 line-clamp-2 text-[10px] leading-snug text-muted">
                  {tBenefits(`items.${key}.description`)}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Services — horizontal strip */}
      <section className="mt-4">
        <div className="flex items-end justify-between gap-3">
          <h2 className="text-lg font-bold tracking-tight">{tServices("title")}</h2>
          <Link
            href="/services"
            className="shrink-0 text-xs font-semibold text-accent-bright"
          >
            {tServices("link")} →
          </Link>
        </div>
        <div className="-mx-4 mt-3 flex gap-2 overflow-x-auto px-4 pb-1 snap-x snap-mandatory [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {SERVICES.map(({ key, icon: Icon }) => (
            <div
              key={key}
              className="w-[72%] shrink-0 snap-start rounded-xl border border-border bg-surface p-3"
            >
              <Icon className="h-4 w-4 text-accent-bright" />
              <h3 className="mt-2 text-xs font-semibold">
                {tServices(`items.${key}.title`)}
              </h3>
              <p className="mt-1 line-clamp-2 text-[10px] leading-snug text-muted">
                {tServices(`items.${key}.description`)}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="mt-5">
        <div className="relative overflow-hidden rounded-2xl border border-border bg-surface px-4 py-6 text-center">
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_50%_80%_at_50%_120%,var(--accent-glow),transparent)]"
          />
          <div className="relative">
            <h2 className="text-lg font-bold tracking-tight">{tCta("title")}</h2>
            <p className="mt-2 text-xs leading-relaxed text-muted">
              {tCta("subtitle")}
            </p>
            <Link
              href="/contact"
              className="mt-4 inline-flex w-full items-center justify-center rounded-xl bg-accent px-5 py-3 text-sm font-semibold text-white shadow-[0_0_24px_var(--accent-glow)]"
            >
              {tCta("button")}
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
