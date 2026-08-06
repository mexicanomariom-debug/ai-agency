"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2, Mic, MicOff } from "lucide-react";
import MatrixIntelligence from "@/components/MatrixIntelligence";
import { useTelegram } from "@/hooks/useTelegram";
import {
  closeVoiceSession,
  fetchProgress,
  fetchVoiceCapabilities,
  fetchVoiceTutor,
  voiceChat,
  voiceTalk,
  type ProgressSnapshot,
  type VoiceSessionAssessment,
  type VoiceTutor,
} from "@/lib/api";

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

function statusLabel(status: Status, isChild: boolean): string {
  if (status === "recording") {
    return isChild ? "Слушаю… отпусти кнопку" : "Слушаю… отпустите микрофон";
  }
  if (status === "processing") return "NEURAL · processing";
  if (status === "speaking") return "NEURAL · transmitting";
  return "NEURAL · standby";
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
  const [sessionSummary, setSessionSummary] = useState<VoiceSessionAssessment | null>(null);
  const [closingSession, setClosingSession] = useState(false);
  const [userTurnCount, setUserTurnCount] = useState(0);
  const [progress, setProgress] = useState<ProgressSnapshot | null>(null);
  const [chatModel, setChatModel] = useState<string | null>(null);
  const [hasSpoken, setHasSpoken] = useState(false);

  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const recognitionRef = useRef<SpeechRec | null>(null);
  const transcriptRef = useRef("");
  const userTurnCountRef = useRef(0);
  const closingRef = useRef(false);

  useEffect(() => {
    if (!isReady) return;
    let cancelled = false;
    setLoading(true);

    Promise.all([
      fetchVoiceTutor(initData || undefined),
      fetchVoiceCapabilities(initData || undefined),
      fetchProgress(initData || undefined).catch(() => null),
    ])
      .then(([t, caps, prog]) => {
        if (cancelled) return;
        setTutor(t);
        setProgress(prog);
        setChatModel(caps.chat_model ?? caps.provider ?? null);
        setUseBrowserStt(!caps.stt);
        if (!caps.llm) {
          setError("Нет LLM ключа на сервере. Добавьте ANTHROPIC/OPENAI в Secrets.");
        } else {
          setError(null);
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Ошибка загрузки");
          setTutor({
            name: "Opus Neural",
            slug: "voice-teacher",
            description: "Нейро-интерфейс",
            language: null,
            level: null,
            audience: null,
            greeting: "Связь с нейро-ядром…",
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

  const runSessionClose = useCallback(
    async (silent = false) => {
      if (closingRef.current || userTurnCountRef.current < 2) return;
      closingRef.current = true;
      if (!silent) setClosingSession(true);
      try {
        const result = await closeVoiceSession(initData || undefined, "voice-teacher");
        if (result.assessed) {
          setSessionSummary(result);
          void fetchProgress(initData || undefined)
            .then(setProgress)
            .catch(() => undefined);
        }
      } catch {
        /* best-effort */
      } finally {
        if (!silent) setClosingSession(false);
      }
    },
    [initData],
  );

  useEffect(() => {
    const onPageHide = () => {
      if (userTurnCountRef.current >= 2) void runSessionClose(true);
    };
    window.addEventListener("pagehide", onPageHide);
    return () => {
      window.removeEventListener("pagehide", onPageHide);
      if (userTurnCountRef.current >= 2) void runSessionClose(true);
    };
  }, [runSessionClose]);

  const playReply = useCallback(async (reply: string, audioBase64: string | null) => {
    setLastReply(reply);
    setHasSpoken(true);
    setStatus("speaking");

    try {
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
      } else if ("speechSynthesis" in window) {
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
  }, []);

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
        userTurnCountRef.current += 1;
        setUserTurnCount(userTurnCountRef.current);
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
        if (
          result.error?.includes("OPENAI_API_KEY") ||
          result.error?.includes("Security List") ||
          result.error?.includes("не ответил")
        ) {
          setUseBrowserStt(true);
          setError(
            result.error.includes("не ответил")
              ? "Таймаут — переключаю на браузерное распознавание."
              : "Нет OpenAI STT — удерживайте микрофон (браузерный режим).",
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
          setError("Пустой ответ нейро-ядра");
          setStatus("idle");
          return;
        }
        setLastUser(result.transcript || "");
        userTurnCountRef.current += 1;
        setUserTurnCount(userTurnCountRef.current);
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
        setError("Распознавание речи недоступно в браузере.");
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
        for (let i = 0; i < results.length; i++) text += results[i][0].transcript;
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
        void sendAudio(new Blob(chunksRef.current, { type: "audio/webm" }));
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
        if (text) void handleTranscript(text);
        else {
          setError("Не расслышал — говорите чётче.");
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
    if (mediaRef.current?.state === "recording") mediaRef.current.stop();
  }, [useBrowserStt, handleTranscript]);

  const audience = tutor?.audience || null;
  const isChild = audience === "child";

  if (loading || !tutor) {
    return (
      <div className="matrix-shell matrix-shell--loading">
        <Loader2 className="h-8 w-8 animate-spin text-[var(--matrix-green)]" />
        <p className="matrix-muted">Инициализация Opus Neural…</p>
        {error && <p className="matrix-error">{error}</p>}
      </div>
    );
  }

  return (
    <div className="matrix-shell">
      <div className="matrix-stage">
        <MatrixIntelligence status={status} />
      </div>

      <div className="matrix-overlay">
        <header className="matrix-header">
          <div>
            <p className="matrix-kicker">Opus 5 · Neural Interface</p>
            <p className="matrix-status">{statusLabel(status, isChild)}</p>
          </div>
          <div className="matrix-meta">
            {user?.first_name && <span>{user.first_name}</span>}
            {tutor.language && <span>{tutor.language}</span>}
            {tutor.level && <span>{tutor.level}</span>}
            {chatModel && <span className="matrix-model">{chatModel}</span>}
          </div>
        </header>

        {status === "idle" && !hasSpoken && (
          <p className="matrix-greeting">{tutor.greeting}</p>
        )}

        {(lastUser || lastReply) && (
          <div className="matrix-transcript" aria-live="polite">
            {lastUser && (
              <p className="matrix-line matrix-line--user">
                <span className="matrix-tag">INPUT</span>
                {lastUser}
              </p>
            )}
            {lastReply && (
              <p className="matrix-line matrix-line--ai">
                <span className="matrix-tag">NEURAL</span>
                {lastReply}
              </p>
            )}
          </div>
        )}

        {error && <p className="matrix-error">{error}</p>}

        {sessionSummary?.assessed && (
          <div className="matrix-recap">
            <p className="matrix-recap-title">
              SESSION LOG
              {sessionSummary.speaking_cefr ? ` · CEFR ${sessionSummary.speaking_cefr}` : ""}
            </p>
            {sessionSummary.summary && <p>{sessionSummary.summary}</p>}
            {sessionSummary.recommendation && (
              <p className="matrix-recap-next">NEXT: {sessionSummary.recommendation}</p>
            )}
          </div>
        )}

        {progress && (
          <p className="matrix-stats">
            streak {progress.streak_days}d
            {progress.speaking_cefr ? ` · ${progress.speaking_cefr}` : ""}
            {progress.vocab_due > 0 ? ` · review ${progress.vocab_due}` : ""}
          </p>
        )}

        <div className="matrix-controls">
          {userTurnCount >= 2 && !sessionSummary && (
            <button
              type="button"
              className="matrix-finish"
              disabled={closingSession || status !== "idle"}
              onClick={() => void runSessionClose(false)}
            >
              {closingSession ? "CLOSING…" : "CLOSE SESSION"}
            </button>
          )}
          <button
            type="button"
            onPointerDown={startRecording}
            onPointerUp={stopRecording}
            onPointerLeave={stopRecording}
            disabled={status === "processing" || status === "speaking"}
            className={`matrix-mic ${status === "recording" ? "recording" : ""}`}
            aria-label="Микрофон"
          >
            {status === "processing" ? (
              <Loader2 className="h-7 w-7 animate-spin" />
            ) : status === "recording" ? (
              <MicOff className="h-7 w-7" />
            ) : (
              <Mic className="h-7 w-7" />
            )}
          </button>
          <p className="matrix-mic-hint">
            {status === "recording" ? "release to send" : "hold to speak"}
          </p>
        </div>
      </div>
    </div>
  );
}
