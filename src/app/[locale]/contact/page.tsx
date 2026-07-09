import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { useTranslations } from "next-intl";
import { use } from "react";
import { buildPageMetadata } from "@/lib/seo";
import PageHeader from "@/components/ui/PageHeader";
import ContactForm, { ContactInfo } from "@/components/contact/ContactContent";
import CtaBanner from "@/components/ui/CtaBanner";

type Props = {
  params: Promise<{ locale: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "meta.pages.contact" });

  return buildPageMetadata({
    locale,
    path: "/contact",
    title: t("title"),
    description: t("description"),
    keywords: t("keywords"),
  });
}

export default function ContactPage({ params }: Props) {
  const { locale } = use(params);
  setRequestLocale(locale);

  const t = useTranslations("contact");

  return (
    <>
      <PageHeader
        title={t("title")}
        subtitle={t("subtitle")}
        description={t("description")}
      />
      <section className="mx-auto grid max-w-6xl gap-12 px-4 py-16 sm:px-6 sm:py-20 lg:grid-cols-2">
        <div>
          <h2 className="text-xl font-semibold">{t("form.title")}</h2>
          <div className="mt-6">
            <ContactForm />
          </div>
        </div>
        <ContactInfo />
      </section>
      <CtaBanner
        namespace="contact.cta"
        href="https://t.me/aiagentes"
        external
      />
    </>
  );
}
