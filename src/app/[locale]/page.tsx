import { setRequestLocale } from "next-intl/server";
import { use } from "react";
import Hero from "@/components/home/Hero";
import Benefits from "@/components/home/Benefits";
import CtaSection from "@/components/home/CtaSection";

type Props = {
  params: Promise<{ locale: string }>;
};

export default function HomePage({ params }: Props) {
  const { locale } = use(params);
  setRequestLocale(locale);

  return (
    <>
      <Hero />
      <Benefits />
      <CtaSection />
    </>
  );
}
