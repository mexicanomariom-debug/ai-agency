import Link from "next/link";
import { Check, Bot } from "lucide-react";
import { BOT_USERNAME } from "@/lib/api";
import { Footer, Header } from "@/components/Landing";

const PLANS = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "Get started with basic language practice.",
    features: [
      "10 messages per day",
      "Default AI tutor",
      "Telegram bot access",
      "Basic conversation practice",
    ],
    cta: "Start Free",
    href: `https://t.me/${BOT_USERNAME}`,
    highlighted: false,
  },
  {
    name: "Basic",
    price: "$9",
    period: "/month",
    description: "More practice with persona tutors.",
    features: [
      "100 messages per day",
      "All persona tutors",
      "Web App access",
      "Conversation history",
      "Cognitive profiling",
    ],
    cta: "Get Basic",
    href: `https://t.me/${BOT_USERNAME}`,
    highlighted: true,
  },
  {
    name: "Premium",
    price: "$19",
    period: "/month",
    description: "Unlimited learning with full features.",
    features: [
      "Unlimited messages",
      "All persona tutors",
      "Priority responses",
      "Advanced cognitive profiling",
      "RAG-enhanced tutoring",
      "Early access to new personas",
    ],
    cta: "Get Premium",
    href: `https://t.me/${BOT_USERNAME}`,
    highlighted: false,
  },
];

export default function PricingPage() {
  return (
    <>
      <Header />
      <main className="px-4 pb-24 pt-32">
        <div className="mx-auto max-w-5xl text-center">
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
            Simple, transparent <span className="gradient-text">pricing</span>
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-zinc-400">
            Start free on Telegram. Upgrade when you&apos;re ready for persona tutors and unlimited practice.
          </p>
        </div>

        <div className="mx-auto mt-16 grid max-w-5xl gap-8 md:grid-cols-3">
          {PLANS.map((plan) => (
            <div
              key={plan.name}
              className={`relative rounded-2xl border p-8 ${
                plan.highlighted
                  ? "border-indigo-500 bg-indigo-500/5 ring-2 ring-indigo-500/30"
                  : "border-zinc-800 bg-zinc-900/50"
              }`}
            >
              {plan.highlighted && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-indigo-600 px-3 py-0.5 text-xs font-medium text-white">
                  Most Popular
                </span>
              )}
              <h3 className="text-xl font-semibold">{plan.name}</h3>
              <div className="mt-4 flex items-baseline gap-1">
                <span className="text-4xl font-bold">{plan.price}</span>
                <span className="text-zinc-500">{plan.period}</span>
              </div>
              <p className="mt-2 text-sm text-zinc-400">{plan.description}</p>
              <ul className="mt-6 space-y-3">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm text-zinc-300">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-indigo-400" />
                    {feature}
                  </li>
                ))}
              </ul>
              <a
                href={plan.href}
                target="_blank"
                rel="noopener noreferrer"
                className={`mt-8 flex w-full items-center justify-center gap-2 rounded-xl py-3 text-sm font-semibold transition ${
                  plan.highlighted
                    ? "bg-indigo-600 text-white hover:bg-indigo-500"
                    : "border border-zinc-700 text-white hover:border-zinc-600 hover:bg-zinc-800"
                }`}
              >
                <Bot className="h-4 w-4" />
                {plan.cta}
              </a>
            </div>
          ))}
        </div>

        <p className="mt-12 text-center text-sm text-zinc-500">
          Subscriptions are managed through the Telegram bot.{" "}
          <Link href="/app" className="text-indigo-400 hover:underline">
            Or try the Web App
          </Link>
        </p>
      </main>
      <Footer />
    </>
  );
}
