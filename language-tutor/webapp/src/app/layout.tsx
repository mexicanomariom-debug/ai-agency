import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Opus 5 Concierge — AI language studio",
  description:
    "Голосовые уроки в Telegram, Persona Lounge, CEFR-путь и FSRS-словарь — одна экосистема Opus 5.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
