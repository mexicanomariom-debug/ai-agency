"use client";

import Link from "next/link";
import { Bot, Globe, MessageSquare, Sparkles } from "lucide-react";
import { BOT_USERNAME } from "@/lib/api";

export function Header() {
  return (
    <header className="fixed top-0 z-50 w-full border-b border-zinc-800/50 bg-zinc-950/80 backdrop-blur-lg">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2 text-lg font-bold">
          <Globe className="h-5 w-5 text-indigo-400" />
          <span className="gradient-text">Language Tutor</span>
        </Link>
        <nav className="flex items-center gap-6">
          <Link href="/pricing" className="text-sm text-zinc-400 transition hover:text-white">
            Pricing
          </Link>
          <a
            href={`https://t.me/${BOT_USERNAME}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-500"
          >
            <Bot className="h-4 w-4" />
            Open Bot
          </a>
        </nav>
      </div>
    </header>
  );
}

export function Hero() {
  return (
    <section className="relative overflow-hidden px-4 pb-24 pt-32">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-900/20 via-transparent to-transparent" />
      <div className="relative mx-auto max-w-4xl text-center">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-4 py-1.5 text-sm text-indigo-300">
          <Sparkles className="h-4 w-4" />
          AI-Powered Language Learning
        </div>
        <h1 className="text-5xl font-bold tracking-tight sm:text-6xl">
          Learn languages through{" "}
          <span className="gradient-text">real conversations</span>
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-zinc-400">
          Practice with AI tutors tailored to your level. Choose from unique personas in our Web App,
          or start chatting instantly on Telegram.
        </p>
        <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <a
            href={`https://t.me/${BOT_USERNAME}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 rounded-xl bg-indigo-600 px-8 py-3.5 text-base font-semibold text-white transition hover:bg-indigo-500"
          >
            <Bot className="h-5 w-5" />
            Start on Telegram
          </a>
          <Link
            href="/app"
            className="flex items-center gap-2 rounded-xl border border-zinc-700 px-8 py-3.5 text-base font-semibold text-white transition hover:border-zinc-600 hover:bg-zinc-900"
          >
            <MessageSquare className="h-5 w-5" />
            Open Web App
          </Link>
        </div>
      </div>
    </section>
  );
}

export function Features() {
  const features = [
    {
      icon: MessageSquare,
      title: "Natural Conversations",
      description: "Practice speaking and writing through realistic dialogues adapted to your level.",
    },
    {
      icon: Sparkles,
      title: "Unique Personas",
      description: "Choose from culturally-rich tutors — María for Spanish, Pierre for French, and more.",
    },
    {
      icon: Bot,
      title: "Telegram Integration",
      description: "Quick onboarding on Telegram: pick your language, set your level, and start chatting.",
    },
  ];

  return (
    <section className="px-4 py-24">
      <div className="mx-auto max-w-6xl">
        <h2 className="mb-12 text-center text-3xl font-bold">Why Language Tutor?</h2>
        <div className="grid gap-8 md:grid-cols-3">
          {features.map((f) => (
            <div
              key={f.title}
              className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6"
            >
              <f.icon className="mb-4 h-8 w-8 text-indigo-400" />
              <h3 className="mb-2 text-lg font-semibold">{f.title}</h3>
              <p className="text-sm leading-relaxed text-zinc-400">{f.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="border-t border-zinc-800 px-4 py-8">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 sm:flex-row">
        <p className="text-sm text-zinc-500">
          &copy; {new Date().getFullYear()} Language Tutor. All rights reserved.
        </p>
        <div className="flex gap-6">
          <Link href="/pricing" className="text-sm text-zinc-500 hover:text-zinc-300">
            Pricing
          </Link>
          <a
            href={`https://t.me/${BOT_USERNAME}`}
            className="text-sm text-zinc-500 hover:text-zinc-300"
          >
            @{BOT_USERNAME}
          </a>
        </div>
      </div>
    </footer>
  );
}
