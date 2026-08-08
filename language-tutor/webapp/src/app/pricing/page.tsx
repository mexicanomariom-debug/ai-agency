import Link from "next/link";
import { Check, Bot } from "lucide-react";
import { BOT_USERNAME } from "@/lib/api";
import { Footer, Header } from "@/components/Landing";

const PLANS = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "Telegram onboarding and daily practice.",
    features: [
      "Telegram bot + placement test",
      "Default tutor Opus",
      "Basic chat practice",
      "/progress snapshot",
    ],
    cta: "Start Free",
    href: `https://t.me/${BOT_USERNAME}`,
    highlighted: false,
  },
  {
    name: "Basic",
    price: "$9",
    period: "/month",
    description: "Persona Lounge and richer sessions.",
    features: [
      "All persona tutors",
      "Web App streaming chat",
      "Opus Studio voice access",
      "FSRS /review in Telegram",
      "Session CEFR recap",
    ],
    cta: "Get Basic",
    href: `https://t.me/${BOT_USERNAME}`,
    highlighted: true,
  },
  {
    name: "Premium",
    price: "$19",
    period: "/month",
    description: "Unlimited concierge learning.",
    features: [
      "Unlimited messages",
      "Priority model tier",
      "Full cognitive profile",
      "RAG textbook context",
      "Learning program updates",
    ],
    cta: "Get Premium",
    href: `https://t.me/${BOT_USERNAME}`,
    highlighted: false,
  },
];

export default function PricingPage() {
  return (
    <div className="opus-marketing">
      <Header />
      <main className="px-4 pb-24 pt-32">
        <div className="opus-container text-center">
          <p className="opus-kicker">Plans</p>
          <h1 className="mt-2 font-[family-name:var(--font-display)] text-4xl font-semibold sm:text-5xl">
            Simple <span className="gradient-text">concierge</span> pricing
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-[var(--muted-fg)]">
            Start free on Telegram. Upgrade for Persona Lounge, Studio voice, and the full learning path.
          </p>
        </div>

        <div className="opus-container mt-16 grid max-w-5xl gap-6 md:grid-cols-3">
          {PLANS.map((plan) => (
            <div
              key={plan.name}
              className={`opus-pricing-card ${plan.highlighted ? "opus-pricing-card--highlight" : ""}`}
            >
              {plan.highlighted && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-[var(--gold)] px-3 py-0.5 text-xs font-semibold text-[#12100e]">
                  Most popular
                </span>
              )}
              <h3 className="text-xl font-semibold">{plan.name}</h3>
              <div className="mt-4 flex items-baseline gap-1">
                <span className="text-4xl font-bold">{plan.price}</span>
                <span className="text-[var(--muted-fg)]">{plan.period}</span>
              </div>
              <p className="mt-2 text-sm text-[var(--muted-fg)]">{plan.description}</p>
              <ul className="mt-6 space-y-3">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm text-[var(--foreground)]">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-[var(--gold)]" />
                    {feature}
                  </li>
                ))}
              </ul>
              <a
                href={plan.href}
                target="_blank"
                rel="noopener noreferrer"
                className={`opus-btn mt-8 w-full ${plan.highlighted ? "opus-btn--primary" : "opus-btn--ghost"}`}
              >
                <Bot className="h-4 w-4" />
                {plan.cta}
              </a>
            </div>
          ))}
        </div>

        <p className="opus-container mt-12 text-center text-sm text-[var(--muted-fg)]">
          Subscriptions via Telegram.{" "}
          <Link href="/app" className="text-[var(--gold)] hover:underline">
            Try Persona Lounge
          </Link>
        </p>
      </main>
      <Footer />
    </div>
  );
}
