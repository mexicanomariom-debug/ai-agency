import { getTranslations } from "next-intl/server";
import { SITE_URL, SITE_NAME } from "@/lib/seo";

type Props = {
  locale: string;
};

export default async function JsonLd({ locale }: Props) {
  const t = await getTranslations({ locale, namespace: "meta" });

  const organization = {
    "@context": "https://schema.org",
    "@type": "ProfessionalService",
    "@id": `${SITE_URL}/#organization`,
    name: SITE_NAME,
    url: SITE_URL,
    logo: `${SITE_URL}/favicon.ico`,
    image: `${SITE_URL}/favicon.ico`,
    description: t("description"),
    email: "hello@ai-agentes.com",
    areaServed: ["RU", "ES", "MX", "EU"],
    knowsLanguage: ["ru", "es", "en"],
    contactPoint: {
      "@type": "ContactPoint",
      contactType: "sales",
      email: "hello@ai-agentes.com",
      availableLanguage: ["Russian", "Spanish"],
    },
    sameAs: [
      "https://t.me/aiagentes",
      "https://github.com/mexicanomariom-debug/ai-agency",
    ],
  };

  const website = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "@id": `${SITE_URL}/#website`,
    name: SITE_NAME,
    url: SITE_URL,
    description: t("description"),
    inLanguage: ["ru-RU", "es-ES", "en-US"],
    publisher: { "@id": `${SITE_URL}/#organization` },
  };

  const graph = [organization, website];

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(graph) }}
    />
  );
}
