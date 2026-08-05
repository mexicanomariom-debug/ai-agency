"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2, Mic, MicOff } from "lucide-react";
import VirtualTeacherAvatar from "@/components/VirtualTeacherAvatar";
import { useAudioLipSync } from "@/hooks/useAudioLipSync";
import { useTelegram } from "@/hooks/useTelegram";
import { fetchVoiceTutor, voiceTalk, type VoiceTutor } from "@/lib/api";

type Status = "idle" | "recording" | "processing" | "speaking";

export default function VoiceTeacher() {
  const { initData, user, isReady, webApp } = useTelegram();
  const [tutor, setTutor] = useState<VoiceTutor | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [lastUser, setLastUser] = useState("");
  const [lastReply, setLastReply] = useState("");
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioEl, setAudioEl] = useState<HTMLAudioElement | null>(null);

  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const mouthOpen = useAudioLipSync(isPlaying, audioEl);

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isReady) return;
    let cancelled = false;
    setLoading(true);
    fetchVoiceTutor(initData || undefined)
      .then((t) => {
        if (!cancelled) setTutor(t);
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Ошибка загрузки");
          setTutor({
            name: "Илья",
            slug: "voice-teacher",
            description: "Голосовой AI-учитель",
            language: null,
            level: null,
            greeting: "Не удалось связаться с сервером. Проверьте API на Oracle (порт 8000).",
          });
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

    if (audioBase64) {
      const bytes = Uint8Array.from(atob(audioBase64), (c) => c.charCodeAt(0));
      const blob = new Blob([bytes], { type: "audio/mpeg" });
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      setAudioEl(audio);
      audio.onended = () => {
        setIsPlaying(false);
        setAudioEl(null);
        setStatus("idle");
        URL.revokeObjectURL(url);
      };
      setIsPlaying(true);
      await audio.play();
      return;
    }

    // Fallback: browser TTS
    if ("speechSynthesis" in window) {
      const utter = new SpeechSynthesisUtterance(reply);
      utter.lang = "ru-RU";
      utter.onstart = () => setIsPlaying(true);
      utter.onend = () => {
        setIsPlaying(false);
        setStatus("idle");
      };
      window.speechSynthesis.speak(utter);
      return;
    }

    setStatus("idle");
  }, []);

  const sendAudio = useCallback(
    async (blob: Blob) => {
      setStatus("processing");
      setError(null);
      try {
        const result = await voiceTalk(blob, initData || undefined);
        if (result.error) {
          setError(result.error);
        }
        if (!result.reply && result.error) {
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
      webApp?.MainButton?.hide();
    } catch {
      setError("Нужен доступ к микрофону");
    }
  }, [status, sendAudio, webApp]);

  const stopRecording = useCallback(() => {
    if (mediaRef.current?.state === "recording") {
      mediaRef.current.stop();
    }
  }, []);

  if (loading || !tutor) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 px-4">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-400" />
        <p className="text-sm text-zinc-400">Загрузка учителя…</p>
        {error && (
          <p className="max-w-sm text-center text-sm text-red-300">{error}</p>
        )}
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-[#0a0a0c] via-[#141210] to-[#0c0c0e] px-4 py-6">
      <header className="mb-4 text-center">
        <p className="text-xs uppercase tracking-[0.2em] text-amber-400/80">AI Учитель · Репетитор</p>
        <h1 className="text-xl font-bold text-white">Голосовое общение</h1>
        {user && (
          <p className="mt-1 text-sm text-zinc-400">
            {user.first_name}
            {tutor.language ? ` · ${tutor.language}` : ""}
            {tutor.level ? ` · ${tutor.level}` : ""}
          </p>
        )}
      </header>

      <div className="flex flex-1 flex-col items-center justify-center gap-6">
        <VirtualTeacherAvatar
          name={tutor.name}
          mouthOpen={mouthOpen}
          isSpeaking={status === "speaking"}
          isListening={status === "recording"}
        />

        <p className="max-w-sm text-center text-sm leading-relaxed text-zinc-400">
          {status === "idle" && tutor.greeting}
          {status === "recording" && "Говорите… отпустите кнопку, когда закончите"}
          {status === "processing" && "Думаю над ответом…"}
          {status === "speaking" && lastReply}
        </p>

        {lastUser && status === "idle" && (
          <p className="max-w-sm rounded-xl bg-zinc-800/60 px-4 py-2 text-center text-sm text-zinc-300">
            Вы: {lastUser}
          </p>
        )}

        {error && (
          <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-300">
            {error}
          </p>
        )}
      </div>

      <div className="flex flex-col items-center gap-3 pb-6">
        <button
          type="button"
          onPointerDown={startRecording}
          onPointerUp={stopRecording}
          onPointerLeave={stopRecording}
          disabled={status === "processing" || status === "speaking"}
          className={`flex h-20 w-20 items-center justify-center rounded-full transition-all ${
            status === "recording"
              ? "scale-110 bg-red-500 shadow-lg shadow-red-500/40"
              : "bg-gradient-to-b from-amber-400 to-amber-600 shadow-lg shadow-amber-500/25 hover:from-amber-300 hover:to-amber-500"
          } disabled:opacity-50`}
        >
          {status === "processing" ? (
            <Loader2 className="h-8 w-8 animate-spin text-black" />
          ) : status === "recording" ? (
            <MicOff className="h-8 w-8 text-white" />
          ) : (
            <Mic className="h-8 w-8 text-black" />
          )}
        </button>
        <p className="text-xs text-zinc-500">
          {status === "recording" ? "Отпустите для отправки" : "Удерживайте и говорите"}
        </p>
      </div>
    </div>
  );
}
