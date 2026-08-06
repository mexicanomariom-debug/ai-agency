"use client";

import Link from "next/link";
import {
  Bot,
  BookOpen,
  Globe,
  Mic,
  Sparkles,
  MessageSquare,
  BarChart3,
} from "lucide-react";
import { BOT_USERNAME } from "@/lib/api";
import { PRODUCT_JOURNEY, PRODUCTS } from "@/lib/products";
import ProductCard from "@/components/ProductCard";

export function Header() {
  return (
    <header className="opus-header">
      <div className="opus-container opus-header-inner">
        <Link href="/" className="opus-logo">
          <Globe className="h-5 w-5" aria-hidden />
          <span>
            <span className="opus-logo-mark">Opus 5</span>
            <span className="opus-logo-sub">Concierge</span>
          </span>
        </Link>
        <nav className="opus-nav">
          <Link href="#products">Products</Link>
          <Link href="#kids">Kids</Link>
          <Link href="/pricing">Pricing</Link>
          <a
            href={`https://t.me/${BOT_USERNAME}`}
            target="_blank"
            rel="noopener noreferrer"
            className="opus-btn opus-btn--primary opus-btn--sm"
          >
            <Bot className="h-4 w-4" />
            Telegram
          </a>
        </nav>
      </div>
    </header>
  );
}

export function Hero() {
  return (
    <section className="opus-hero">
      <div className="opus-hero-orb opus-hero-orb--a" aria-hidden />
      <div className="opus-hero-orb opus-hero-orb--b" aria-hidden />
      <div className="opus-container opus-hero-inner">
        <div className="opus-hero-badge">
          <Sparkles className="h-4 w-4" aria-hidden />
          AI language concierge · voice + chat + memory
        </div>
        <h1 className="opus-hero-title">
          One ecosystem for
          <span className="gradient-text"> living language practice</span>
        </h1>
        <p className="opus-hero-lead">
          Opus 5 is not a single chatbot — it is a studio for 3D voice lessons, persona tutors,
          Telegram coaching, and a learning path that remembers your level, words, and progress.
        </p>
        <div className="opus-hero-actions">
          <a
            href={`https://t.me/${BOT_USERNAME}`}
            target="_blank"
            rel="noopener noreferrer"
            className="opus-btn opus-btn--primary"
          >
            <Bot className="h-5 w-5" />
            Start on Telegram
          </a>
          <Link href="/app" className="opus-btn opus-btn--ghost">
            <MessageSquare className="h-5 w-5" />
            Persona Lounge
          </Link>
        </div>
        <div className="opus-hero-pills" aria-label="Product highlights">
          <span><Mic className="h-3.5 w-3.5" /> 3D Studio</span>
          <span><MessageSquare className="h-3.5 w-3.5" /> Personas</span>
          <span><BookOpen className="h-3.5 w-3.5" /> FSRS vocab</span>
          <span><BarChart3 className="h-3.5 w-3.5" /> CEFR path</span>
        </div>
      </div>
    </section>
  );
}

export function ProductShowcase() {
  return (
    <section id="products" className="opus-section">
      <div className="opus-container">
        <div className="opus-section-head">
          <p className="opus-kicker">Product suite</p>
          <h2 className="opus-section-title">Four surfaces, one brain</h2>
          <p className="opus-section-lead">
            Each product shares pedagogy, cognitive profile, and session memory — so Elena in
            Studio and María in Lounge know the same student.
          </p>
        </div>
        <div className="product-grid">
          {PRODUCTS.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      </div>
    </section>
  );
}

export function Journey() {
  return (
    <section className="opus-section opus-section--muted">
      <div className="opus-container">
        <div className="opus-section-head">
          <p className="opus-kicker">How it flows</p>
          <h2 className="opus-section-title">From &ldquo;I don&apos;t know my level&rdquo; to a plan</h2>
        </div>
        <ol className="journey-grid">
          {PRODUCT_JOURNEY.map((item) => (
            <li key={item.step} className="journey-step">
              <span className="journey-step-num">{item.step}</span>
              <h3 className="journey-step-title">{item.title}</h3>
              <p className="journey-step-text">{item.text}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

export function Features() {
  const items = [
    {
      icon: Sparkles,
      title: "Evidence-grounded pedagogy",
      description:
        "Retrieve-first coaching, hint ladder, error diagnosis — not a translation dump.",
    },
    {
      icon: Mic,
      title: "Studio voice",
      description:
        "Elena in WebGL with lip-sync, transcripts that stay on screen, session CEFR recap.",
    },
    {
      icon: Bot,
      title: "Telegram-native",
      description: "/test placement in Russian, /review FSRS, /progress dashboard, blue voice TWA.",
    },
  ];

  return (
    <section className="opus-section">
      <div className="opus-container">
        <h2 className="opus-section-title opus-section-title--center">Built for real learners</h2>
        <div className="feature-grid">
          {items.map((f) => (
            <article key={f.title} className="opus-feature-card">
              <f.icon className="h-7 w-7 text-[var(--gold)]" aria-hidden />
              <h3>{f.title}</h3>
              <p>{f.description}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="opus-footer">
      <div className="opus-container opus-footer-inner">
        <p className="opus-footer-copy">
          &copy; {new Date().getFullYear()} Opus 5 Concierge · Language Tutor
        </p>
        <div className="opus-footer-links">
          <Link href="/pricing">Pricing</Link>
          <Link href="/app">Web App</Link>
          <a href={`https://t.me/${BOT_USERNAME}`}>@{BOT_USERNAME}</a>
        </div>
      </div>
    </footer>
  );
}
