import { setRequestLocale } from "next-intl/server";
import { useTranslations } from "next-intl";
import { use } from "react";

type Props = {
  params: Promise<{ locale: string }>;
};

// Placeholder — full page will be implemented later.
export default function AboutPage({ params }: Props) {
  const { locale } = use(params);
  setRequestLocale(locale);

  const t = useTranslations("about");

  return (
    <section className="mx-auto max-w-6xl px-4 py-24 sm:px-6">
      <h1 className="text-4xl font-bold tracking-tight">{t("title")}</h1>
      <p className="mt-4 text-lg text-muted">{t("subtitle")}</p>
    </section>
  );
}
