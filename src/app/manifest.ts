import type { MetadataRoute } from "next";
import { SITE_NAME } from "@/lib/seo";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: SITE_NAME,
    short_name: SITE_NAME,
    description:
      "AI agents and business automation agency — AI-Agentes",
    start_url: "/ru",
    display: "standalone",
    background_color: "#050507",
    theme_color: "#6366f1",
    lang: "ru",
    icons: [
      {
        src: "/favicon.ico",
        sizes: "48x48",
        type: "image/x-icon",
      },
    ],
  };
}
