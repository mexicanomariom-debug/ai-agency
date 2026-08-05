import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Language Tutor — Learn Languages with AI",
  description: "Practice languages through AI-powered conversations with personalized tutors.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
