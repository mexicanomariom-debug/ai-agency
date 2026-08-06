import Link from "next/link";

export const metadata = {
  title: "Opus 5 — голос в Telegram",
  description: "Голосовая практика языка через Telegram-бот — без Mini App",
};

export default function VoicePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col items-center justify-center gap-6 p-8 text-center">
      <p className="text-sm uppercase tracking-widest text-[var(--opus-gold-muted)]">
        Opus 5 Concierge
      </p>
      <h1 className="text-2xl font-semibold text-[var(--opus-cream)]">
        Голос — прямо в Telegram
      </h1>
      <p className="text-[var(--opus-cream-muted)]">
        Mini App отключён. Отправьте <strong>голосовое сообщение</strong> боту — он ответит
        живым голосом с текстом в подписи.
      </p>
      <Link
        href="https://t.me/All_languages_bot"
        className="rounded-full bg-[var(--opus-gold)] px-6 py-3 font-medium text-black"
      >
        Открыть бот
      </Link>
      <Link href="/" className="text-sm text-[var(--opus-gold-muted)] hover:underline">
        На главную
      </Link>
    </main>
  );
}
