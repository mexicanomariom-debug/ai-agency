import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Opus 5 Concierge — AI language studio",
  description:
    "Opus Studio voice lessons, Persona Lounge chat, Telegram concierge, and a CEFR learning path with FSRS vocabulary.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
