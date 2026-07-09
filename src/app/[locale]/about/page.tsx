import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { useTranslations } from "next-intl";
import { use } from "react";
import { buildPageMetadata } from "@/lib/seo";
import PageHeader from "@/components/ui/PageHeader";
import AboutContent from "@/components/about/AboutContent";
import CtaBanner from "@/components/ui/CtaBanner";

type Props = {
  params: Promise<{ locale: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "meta.pages.about" });

  return buildPageMetadata({
    locale,
    path: "/about",
    title: t("title"),
    description: t("description"),
    keywords: t("keywords"),
  });
}

export default function AboutPage({ params }: Props) {
  const { locale } = use(params);
  setRequestLocale(locale);

  const t = useTranslations("about");

  return (
    <>
      <PageHeader
        title={t("title")}
        subtitle={t("subtitle")}
        description={t("description")}
      />
      <AboutContent />
      <CtaBanner namespace="about.cta" />
    </>
  );
}
