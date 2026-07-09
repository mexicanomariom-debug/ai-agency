"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { motion } from "framer-motion";
import { Mail, MessageCircle, Send, User } from "lucide-react";

export default function ContactForm() {
  const t = useTranslations("contact.form");
  const [sent, setSent] = useState(false);

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const data = new FormData(form);
    const name = data.get("name") as string;
    const email = data.get("email") as string;
    const company = data.get("company") as string;
    const message = data.get("message") as string;

    const subject = encodeURIComponent(
      `AI-Agentes — ${t("emailSubject")} (${name})`,
    );
    const body = encodeURIComponent(
      `${t("emailBody.name")}: ${name}\n${t("emailBody.email")}: ${email}\n${t("emailBody.company")}: ${company || "—"}\n\n${message}`,
    );

    window.location.href = `mailto:hello@ai-agentes.com?subject=${subject}&body=${body}`;
    setSent(true);
  }

  if (sent) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        className="rounded-2xl border border-accent/30 bg-accent/5 p-8 text-center"
      >
        <p className="text-lg font-semibold">{t("success.title")}</p>
        <p className="mt-2 text-sm text-muted">{t("success.message")}</p>
      </motion.div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label htmlFor="name" className="mb-1.5 block text-sm font-medium">
          {t("name")}
        </label>
        <input
          id="name"
          name="name"
          type="text"
          required
          className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none transition-colors focus:border-accent"
        />
      </div>
      <div>
        <label htmlFor="email" className="mb-1.5 block text-sm font-medium">
          {t("email")}
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none transition-colors focus:border-accent"
        />
      </div>
      <div>
        <label htmlFor="company" className="mb-1.5 block text-sm font-medium">
          {t("company")}
        </label>
        <input
          id="company"
          name="company"
          type="text"
          className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none transition-colors focus:border-accent"
        />
      </div>
      <div>
        <label htmlFor="message" className="mb-1.5 block text-sm font-medium">
          {t("message")}
        </label>
        <textarea
          id="message"
          name="message"
          rows={5}
          required
          className="w-full resize-none rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none transition-colors focus:border-accent"
        />
      </div>
      <button
        type="submit"
        className="w-full rounded-xl bg-accent px-6 py-3.5 text-sm font-semibold text-white shadow-[0_0_24px_var(--accent-glow)] transition-colors hover:bg-accent-bright"
      >
        {t("submit")}
      </button>
    </form>
  );
}

export function ContactInfo() {
  const t = useTranslations("contact");

  const channels = [
    {
      icon: Mail,
      label: "Email",
      value: "hello@ai-agentes.com",
      href: "mailto:hello@ai-agentes.com",
    },
    {
      icon: Send,
      label: "Telegram",
      value: "@aiagentes",
      href: "https://t.me/aiagentes",
    },
    {
      icon: MessageCircle,
      label: "WhatsApp",
      value: t("channels.whatsapp"),
      href: "https://wa.me/0000000000",
    },
  ];

  return (
    <div className="space-y-8">
      <div className="rounded-2xl border border-border bg-surface p-6">
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-accent/10">
            <User className="h-7 w-7 text-accent-bright" />
          </div>
          <div>
            <p className="font-semibold">{t("person")}</p>
            <p className="text-sm text-muted">{t("role")}</p>
          </div>
        </div>
        <p className="mt-4 text-sm leading-relaxed text-muted">
          {t("personBio")}
        </p>
      </div>

      <div className="space-y-3">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">
          {t("channelsTitle")}
        </h3>
        {channels.map(({ icon: Icon, label, value, href }) => (
          <a
            key={label}
            href={href}
            target={href.startsWith("http") ? "_blank" : undefined}
            rel={href.startsWith("http") ? "noopener noreferrer" : undefined}
            className="flex items-center gap-3 rounded-xl border border-border bg-surface px-4 py-3 transition-colors hover:border-accent/40 hover:bg-surface-hover"
          >
            <Icon className="h-5 w-5 text-accent-bright" />
            <div>
              <p className="text-xs text-muted">{label}</p>
              <p className="text-sm font-medium">{value}</p>
            </div>
          </a>
        ))}
      </div>

      <div className="rounded-2xl border border-border bg-surface p-6">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">
          {t("hours.title")}
        </h3>
        <p className="mt-3 text-sm text-foreground">{t("hours.schedule")}</p>
        <p className="mt-1 text-sm text-muted">{t("hours.note")}</p>
      </div>
    </div>
  );
}
