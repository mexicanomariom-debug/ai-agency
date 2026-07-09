import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { useTranslations } from "next-intl";
import { use } from "react";
import { buildPageMetadata } from "@/lib/seo";
import PageHeader from "@/components/ui/PageHeader";
import ServicesContent from "@/components/services/ServicesContent";
import CtaBanner from "@/components/ui/CtaBanner";

type Props = {
  params: Promise<{ locale: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "meta.pages.services" });

  return buildPageMetadata({
    locale,
    path: "/services",
    title: t("title"),
    description: t("description"),
    keywords: t("keywords"),
  });
}

export default function ServicesPage({ params }: Props) {
  const { locale } = use(params);
  setRequestLocale(locale);

  const t = useTranslations("services");

  return (
    <>
      <PageHeader
        title={t("title")}
        subtitle={t("subtitle")}
        description={t("description")}
      />
      <ServicesContent />
      <CtaBanner namespace="services.cta" />
    </>
  );
}
