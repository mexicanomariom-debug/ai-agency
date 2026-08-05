"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2, Mic, MicOff } from "lucide-react";
import type { TalkingAvatarHandle } from "@/components/TalkingAvatar3D";
import { useTelegram } from "@/hooks/useTelegram";
import {
  fetchVoiceCapabilities,
  fetchVoiceTutor,
  voiceChat,
  voiceTalk,
  type VoiceTutor,
} from "@/lib/api";

const TalkingAvatar3D = dynamic(() => import("@/components/TalkingAvatar3D"), {
  ssr: false,
  loading: () => (
    <div className="flex h-72 w-full items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-[var(--gold)]" />
    </div>
  ),
});

type Status = "idle" | "recording" | "processing" | "speaking";

type SpeechRec = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start: () => void;
  stop: () => void;
  onresult: ((ev: { results: { [i: number]: { [j: number]: { transcript: string } } } }) => void) | null;
  onerror: ((ev: { error: string }) => void) | null;
  onend: (() => void) | null;
};

function getSpeechRecognition(): (new () => SpeechRec) | null {
  const w = window as unknown as {
    SpeechRecognition?: new () => SpeechRec;
    webkitSpeechRecognition?: new () => SpeechRec;
  };
  return w.SpeechRecognition || w.webkitSpeechRecognition || null;
}

export default function VoiceTeacher() {
  const { initData, user, isReady, webApp } = useTelegram();
  const [tutor, setTutor] = useState<VoiceTutor | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [lastUser, setLastUser] = useState("");
  const [lastReply, setLastReply] = useState("");
  const [useBrowserStt, setUseBrowserStt] = useState(true);
  const [loading, setLoading] = useState(true);
  const [avatarReady, setAvatarReady] = useState(false);

  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const recognitionRef = useRef<SpeechRec | null>(null);
  const transcriptRef = useRef("");
  const avatarRef = useRef<TalkingAvatarHandle | null>(null);

  useEffect(() => {
    if (!isReady) return;
    let cancelled = false;
    setLoading(true);

    Promise.all([
      fetchVoiceTutor(initData || undefined),
      fetchVoiceCapabilities(initData || undefined),
    ])
      .then(([t, caps]) => {
        if (cancelled) return;
        setTutor(t);
        setUseBrowserStt(!caps.stt);
        if (!caps.llm) {
          setError("Нет LLM ключа (ANTHROPIC/OPENAI). Добавьте в GitHub Secrets и задеплойте Oracle.");
        } else {
          setError(null);
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Ошибка загрузки");
          setTutor({
            name: "Илья",
            slug: "voice-teacher",
            description: "Премиальный 3D-учитель",
            language: null,
            level: null,
            audience: null,
            greeting: "Не удалось связаться с сервером.",
          });
          setUseBrowserStt(true);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [isReady, initData]);

  const playReply = useCallback(async (reply: string, audioBase64: string | null) => {
    setLastReply(reply);
    setStatus("speaking");

    try {
      if (audioBase64 && avatarRef.current && avatarReady) {
        await avatarRef.current.speakAudioBase64(audioBase64, reply);
        setStatus("idle");
        return;
      }

      if (audioBase64) {
        const bytes = Uint8Array.from(atob(audioBase64), (c) => c.charCodeAt(0));
        const blob = new Blob([bytes], { type: "audio/mpeg" });
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        await new Promise<void>((resolve) => {
          audio.onended = () => {
            URL.revokeObjectURL(url);
            resolve();
          };
          audio.onerror = () => {
            URL.revokeObjectURL(url);
            resolve();
          };
          void audio.play();
        });
        setStatus("idle");
        return;
      }

      if (avatarRef.current && avatarReady) {
        await avatarRef.current.speakBrowserText(reply);
        setStatus("idle");
        return;
      }

      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
        const utter = new SpeechSynthesisUtterance(reply);
        utter.lang = "ru-RU";
        await new Promise<void>((resolve) => {
          utter.onend = () => resolve();
          utter.onerror = () => resolve();
          window.speechSynthesis.speak(utter);
        });
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка озвучки");
    }
    setStatus("idle");
  }, [avatarReady]);

  const handleTranscript = useCallback(
    async (transcript: string) => {
      setStatus("processing");
      setError(null);
      setLastUser(transcript);
      try {
        const result = await voiceChat(transcript, initData || undefined);
        if (result.error && !result.reply) {
          setError(result.error);
          setStatus("idle");
          return;
        }
        await playReply(result.reply, result.audio_base64);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Ошибка связи");
        setStatus("idle");
      }
    },
    [initData, playReply],
  );

  const sendAudio = useCallback(
    async (blob: Blob) => {
      setStatus("processing");
      setError(null);
      try {
        const result = await voiceTalk(blob, initData || undefined);
        if (result.error?.includes("OPENAI_API_KEY") || result.error?.includes("Security List") || result.error?.includes("не ответил")) {
          setUseBrowserStt(true);
          setError(
            result.error.includes("не ответил")
              ? "Сервер думал слишком долго — переключаю на браузерное распознавание. Удерживайте микрофон и говорите."
              : "Нет OpenAI для распознавания — используйте удержание микрофона (браузерный режим).",
          );
          setStatus("idle");
          return;
        }
        if (result.error && !result.reply) {
          setError(result.error);
          setStatus("idle");
          return;
        }
        if (!result.reply) {
          setError("Пустой ответ учителя");
          setStatus("idle");
          return;
        }
        setLastUser(result.transcript || "");
        await playReply(result.reply, result.audio_base64);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Ошибка связи");
        setStatus("idle");
      }
    },
    [initData, playReply],
  );

  const startRecording = useCallback(async () => {
    if (status !== "idle") return;
    setError(null);
    webApp?.MainButton?.hide();

    if (useBrowserStt) {
      const SR = getSpeechRecognition();
      if (!SR) {
        setError("Распознавание речи недоступно. Добавьте OPENAI_API_KEY в GitHub Secrets.");
        return;
      }
      const rec = new SR();
      rec.lang = "ru-RU";
      rec.continuous = true;
      rec.interimResults = true;
      transcriptRef.current = "";
      rec.onresult = (ev) => {
        const results = ev.results as unknown as ArrayLike<{ 0: { transcript: string } }>;
        let text = "";
        for (let i = 0; i < results.length; i++) {
          text += results[i][0].transcript;
        }
        transcriptRef.current = text.trim();
      };
      rec.onerror = (ev) => {
        if (ev.error !== "aborted" && ev.error !== "no-speech") {
          setError(`Распознавание: ${ev.error}`);
        }
      };
      recognitionRef.current = rec;
      rec.start();
      setStatus("recording");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        void sendAudio(blob);
      };
      mediaRef.current = recorder;
      recorder.start();
      setStatus("recording");
    } catch {
      setError("Нужен доступ к микрофону");
    }
  }, [status, useBrowserStt, sendAudio, webApp]);

  const stopRecording = useCallback(() => {
    if (useBrowserStt && recognitionRef.current) {
      recognitionRef.current.onend = () => {
        const text = transcriptRef.current.trim();
        recognitionRef.current = null;
        if (text) {
          void handleTranscript(text);
        } else {
          setError("Не расслышал — попробуйте ещё раз, говорите чётче.");
          setStatus("idle");
        }
      };
      try {
        recognitionRef.current.stop();
      } catch {
        setStatus("idle");
      }
      return;
    }
    if (mediaRef.current?.state === "recording") {
      mediaRef.current.stop();
    }
  }, [useBrowserStt, handleTranscript]);

  const audience = tutor?.audience || null;
  const isChild = audience === "child";

  if (loading || !tutor) {
    return (
      <div className="premium-shell flex min-h-screen flex-col items-center justify-center gap-3 px-4">
        <Loader2 className="h-8 w-8 animate-spin text-[var(--gold)]" />
        <p className="text-sm text-[var(--muted-fg)]">Открываем студию учителя…</p>
        {error && <p className="max-w-sm text-center text-sm text-red-300">{error}</p>}
      </div>
    );
  }

  return (
    <div className={`premium-shell ${isChild ? "theme-child" : "theme-adult"}`}>
      <div className="premium-glow" aria-hidden />
      <header className="premium-header">
        <p className="premium-kicker">{isChild ? "Opus Kids · Studio" : "Opus 5 · Concierge"}</p>
        <h1 className="premium-title">Илья</h1>
        <p className="premium-sub">
          {user?.first_name ? `${user.first_name}` : "Гость"}
          {tutor.language ? ` · ${tutor.language}` : ""}
          {tutor.level ? ` · ${tutor.level}` : ""}
          {audience ? ` · ${audience}` : ""}
        </p>
      </header>

      <div className="premium-stage">
        <TalkingAvatar3D
          ref={avatarRef}
          name={tutor.name}
          audience={audience}
          isListening={status === "recording"}
          isSpeaking={status === "speaking"}
          onReadyChange={setAvatarReady}
        />

        <p className="premium-caption">
          {status === "idle" && tutor.greeting}
          {status === "recording" && (isChild ? "Говори… отпусти кнопку, когда закончишь" : "Говорите… отпустите, когда закончите")}
          {status === "processing" && (isChild ? "Илья думает…" : "Формирую ответ…")}
          {status === "speaking" && lastReply}
        </p>

        {lastUser && status === "idle" && (
          <p className="premium-echo">Вы: {lastUser}</p>
        )}

        {error && <p className="premium-error">{error}</p>}
      </div>

      <div className="premium-mic-block">
        <button
          type="button"
          onPointerDown={startRecording}
          onPointerUp={stopRecording}
          onPointerLeave={stopRecording}
          disabled={status === "processing" || status === "speaking"}
          className={`premium-mic ${status === "recording" ? "recording" : ""}`}
          aria-label="Микрофон"
        >
          {status === "processing" ? (
            <Loader2 className="h-8 w-8 animate-spin" />
          ) : status === "recording" ? (
            <MicOff className="h-8 w-8" />
          ) : (
            <Mic className="h-8 w-8" />
          )}
        </button>
        <p className="premium-mic-hint">
          {status === "recording" ? "Отпустите для отправки" : "Удерживайте и говорите"}
        </p>
      </div>
    </div>
  );
}
