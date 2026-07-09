import type { Metadata } from "next";

export const SITE_URL = "https://ai-agentes.com";
export const SITE_NAME = "AI-Agentes";

const ROUTES = ["", "/services", "/solutions", "/portfolio", "/about", "/contact"] as const;

type BuildPageMetadataOptions = {
  locale: string;
  path: (typeof ROUTES)[number];
  title: string;
  description: string;
  keywords: string;
};

export function buildPageMetadata({
  locale,
  path,
  title,
  description,
  keywords,
}: BuildPageMetadataOptions): Metadata {
  const canonicalPath = `/${locale}${path}`;
  const url = `${SITE_URL}${canonicalPath}`;

  return {
    title: path === "" ? { absolute: title } : title,
    description,
    keywords: keywords.split(",").map((k) => k.trim()),
    alternates: {
      canonical: canonicalPath,
      languages: {
        ru: `/ru${path}`,
        es: `/es${path}`,
        "x-default": `/ru${path}`,
      },
    },
    openGraph: {
      type: "website",
      url,
      title,
      description,
      siteName: SITE_NAME,
      locale: locale === "ru" ? "ru_RU" : "es_ES",
      alternateLocale: locale === "ru" ? ["es_ES"] : ["ru_RU"],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
    },
    robots: {
      index: true,
      follow: true,
      googleBot: {
        index: true,
        follow: true,
        "max-video-preview": -1,
        "max-image-preview": "large",
        "max-snippet": -1,
      },
    },
  };
}

export { ROUTES };
