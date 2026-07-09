import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { use } from "react";
import { buildPageMetadata } from "@/lib/seo";
import Hero from "@/components/home/Hero";
import MobileHomeContent from "@/components/home/MobileHomeContent";
import TrustSection from "@/components/home/TrustSection";
import IndustriesSection from "@/components/home/IndustriesSection";
import Benefits from "@/components/home/Benefits";
import ServicesPreview from "@/components/home/ServicesPreview";
import CtaSection from "@/components/home/CtaSection";

type Props = {
  params: Promise<{ locale: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "meta.pages.home" });

  return buildPageMetadata({
    locale,
    path: "",
    title: t("title"),
    description: t("description"),
    keywords: t("keywords"),
  });
}

export default function HomePage({ params }: Props) {
  const { locale } = use(params);
  setRequestLocale(locale);

  return (
    <>
      <Hero />
      <MobileHomeContent />
      <div className="hidden sm:contents">
        <TrustSection />
        <IndustriesSection />
        <Benefits />
        <ServicesPreview />
        <CtaSection />
      </div>
    </>
  );
}
