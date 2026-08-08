"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { Bot, Volume2 } from "lucide-react";
import type { TalkingAvatarHandle } from "@/components/TalkingAvatar3D";
import { BOT_USERNAME } from "@/lib/api";

// WebGL + TalkingHead + a ~2 MB GLB: keep it off the server render and out of
// the initial bundle for visitors who never scroll to this section.
const TalkingAvatar3D = dynamic(() => import("@/components/TalkingAvatar3D"), {
  ssr: false,
  loading: () => <div className="landing-child-placeholder" aria-hidden />,
});

const DEMO_LINES = [
  "Привет! Я Миша. Давай учить язык весело!",
  "Скажи со мной: Hello! How are you?",
  "Отлично! Теперь отправь голосовое в Telegram — бот ответит тебе голосом.",
];

export default function LandingChildDemo() {
  const avatarRef = useRef<TalkingAvatarHandle | null>(null);
  const sectionRef = useRef<HTMLElement>(null);
  const [visible, setVisible] = useState(false);
  const [ready, setReady] = useState(false);
  const [speaking, setSpeaking] = useState(false);

  useEffect(() => {
    const node = sectionRef.current;
    if (!node || visible) return;
    if (typeof IntersectionObserver === "undefined") {
      setVisible(true);
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [visible]);

  const playDemo = useCallback(async () => {
    if (!avatarRef.current || !ready) return;
    setSpeaking(true);
    try {
      for (const line of DEMO_LINES) {
        await avatarRef.current.speakBrowserText(line);
      }
    } finally {
      setSpeaking(false);
    }
  }, [ready]);

  const status = speaking ? "Говорю…" : ready ? "Готов к демо" : "Загружаю 3D-учителя…";

  return (
    <section className="opus-section theme-child landing-child" id="kids" ref={sectionRef}>
      <div className="opus-container">
        <div className="landing-child-grid">
          <div className="landing-child-copy">
            <p className="opus-kicker">Для детей</p>
            <h2 className="opus-section-title">Миша — твой учитель в 3D</h2>
            <p className="opus-section-lead">
              Мультяшный друг на лендинге показывает, как звучит живой урок. В Telegram —
              голосовые сообщения: говоришь — бот отвечает тёплым голосом.
            </p>
            <div className="landing-child-actions">
              <button
                type="button"
                className="opus-btn opus-btn--primary"
                disabled={!ready || speaking}
                aria-busy={speaking}
                onClick={() => void playDemo()}
              >
                <Volume2 className="h-5 w-5" />
                {speaking ? "Говорю…" : "Слушать демо"}
              </button>
              <a
                href={`https://t.me/${BOT_USERNAME}`}
                target="_blank"
                rel="noopener noreferrer"
                className="opus-btn opus-btn--ghost"
              >
                <Bot className="h-5 w-5" />
                Говорить в Telegram
              </a>
            </div>
            <p className="landing-child-status" aria-live="polite">
              {visible ? status : ""}
            </p>
          </div>
          <div className="landing-child-stage">
            {visible ? (
              <TalkingAvatar3D
                ref={avatarRef}
                name="Миша"
                audience="child"
                isSpeaking={speaking}
                onReadyChange={setReady}
              />
            ) : (
              <div className="landing-child-placeholder" aria-hidden />
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
