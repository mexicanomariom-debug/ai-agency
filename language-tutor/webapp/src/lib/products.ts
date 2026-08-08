import { BOT_USERNAME } from "@/lib/api";

export type ProductId = "studio" | "lounge" | "telegram" | "path";

export type Product = {
  id: ProductId;
  name: string;
  tagline: string;
  description: string;
  features: string[];
  href: string;
  external?: boolean;
  accent: "gold" | "teal" | "violet" | "rose";
  badge?: string;
};

export const PRODUCTS: Product[] = [
  {
    id: "studio",
    name: "Opus Voice",
    tagline: "Голос в Telegram",
    description:
      "Голосовое в чат бота → ответ живым TTS. Whisper, короткие реплики, премиальный голос.",
    features: ["Voice in / voice out", "Whisper STT", "TTS shimmer"],
    href: `https://t.me/${BOT_USERNAME}`,
    external: true,
    accent: "gold",
    badge: "Flagship",
  },
  {
    id: "lounge",
    name: "Persona Lounge",
    tagline: "Text & stream chat",
    description:
      "María, Pierre, Hans and more — streamed replies with pedagogy, RAG textbooks, and cognitive profile.",
    features: ["SSE streaming", "Level-aware", "Multi-language"],
    href: "/app",
    accent: "violet",
  },
  {
    id: "telegram",
    name: "Telegram Concierge",
    tagline: "Always-on coach",
    description:
      "Онбординг, голосовые в чат, /review FSRS, /progress, /test на русском.",
    features: ["/review · /progress", "/test · /program", "🎙 голосовые"],
    href: `https://t.me/${BOT_USERNAME}`,
    external: true,
    accent: "teal",
    badge: "Start here",
  },
  {
    id: "path",
    name: "Learning Path",
    tagline: "Measure & remember",
    description:
      "Post-session CEFR estimates, streaks, spaced repetition vocabulary, and a four-week program after placement.",
    features: ["CEFR tracking", "FSRS vocabulary", "Adaptive prompts"],
    href: `https://t.me/${BOT_USERNAME}?start=progress`,
    external: true,
    accent: "rose",
  },
];

export const PRODUCT_JOURNEY = [
  { step: "01", title: "Discover", text: "Mini-test in Russian or pick your level" },
  { step: "02", title: "Practice", text: "Голосовые в Telegram или текст в Lounge" },
  { step: "03", title: "Review", text: "FSRS words and session recap in Telegram" },
  { step: "04", title: "Grow", text: "Progress dashboard and program updates" },
];
