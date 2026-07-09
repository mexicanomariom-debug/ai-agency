"use client";

import { useLocale } from "next-intl";
import { usePathname, useRouter } from "@/i18n/navigation";
import { routing, type Locale } from "@/i18n/routing";

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
          className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wider transition-colors ${
            locale === l
              ? "bg-accent text-white"
              : "text-muted hover:text-foreground"
          }`}
        >
          {l}
        </button>
      ))}
    </div>
  );
}
