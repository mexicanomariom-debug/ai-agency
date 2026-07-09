"use client";

import { useLocale } from "next-intl";
import { usePathname, useRouter } from "@/i18n/navigation";
import { routing, type Locale } from "@/i18n/routing";

const LOCALE_LABELS: Record<Locale, string> = {
  ru: "ru",
  es: "es",
  en: "eng",
};

export default function LanguageSwitcher() {
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();

  function switchTo(nextLocale: Locale) {
    router.replace(pathname, { locale: nextLocale });
  }

  return (
    <div className="flex items-center rounded-full border border-border bg-surface p-0.5">
      {routing.locales.map((l) => (
        <button
          key={l}
          type="button"
          onClick={() => switchTo(l)}
          aria-pressed={locale === l}
          aria-label={l === "en" ? "English" : l}
          className={`rounded-full px-2.5 py-1 text-xs font-semibold uppercase tracking-wider transition-colors sm:px-3 ${
            locale === l
              ? "bg-accent text-white"
              : "text-muted hover:text-foreground"
          }`}
        >
          {LOCALE_LABELS[l]}
        </button>
      ))}
    </div>
  );
}
