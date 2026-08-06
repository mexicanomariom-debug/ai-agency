"use client";

import { useCallback, useRef, useState } from "react";
import { Bot, Volume2 } from "lucide-react";
import TalkingAvatar3D, { type TalkingAvatarHandle } from "@/components/TalkingAvatar3D";
import { BOT_USERNAME } from "@/lib/api";

const DEMO_LINES = [
  "Привет! Я Миша. Давай учить язык весело!",
  "Скажи со мной: Hello! How are you?",
  "Отлично! Теперь отправь голосовое в Telegram — бот ответит тебе голосом.",
];

export default function LandingChildDemo() {
  const avatarRef = useRef<TalkingAvatarHandle | null>(null);
  const [ready, setReady] = useState(false);
  const [speaking, setSpeaking] = useState(false);

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

  return (
    <section className="opus-section theme-child landing-child" id="kids">
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
          </div>
          <div className="landing-child-stage">
            <TalkingAvatar3D
              ref={avatarRef}
              name="Миша"
              audience="child"
              isSpeaking={speaking}
              onReadyChange={setReady}
            />
          </div>
        </div>
      </div>
    </section>
  );
}
