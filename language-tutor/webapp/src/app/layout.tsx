import type { Metadata } from "next";
import { Share_Tech_Mono } from "next/font/google";
import "./globals.css";

const shareTechMono = Share_Tech_Mono({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-matrix",
});

export const metadata: Metadata = {
  title: "Opus 5 Concierge — AI language studio",
  description:
    "Opus Studio voice lessons, Persona Lounge chat, Telegram concierge, and a CEFR learning path with FSRS vocabulary.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body className={`${shareTechMono.variable} min-h-screen antialiased`}>
        {children}
      </body>
    </html>
  );
}
