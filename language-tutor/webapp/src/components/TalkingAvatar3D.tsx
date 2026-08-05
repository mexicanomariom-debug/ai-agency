"use client";

import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";

import { getAvatarPreset, STUDIO_LIGHTING } from "@/lib/avatarPresets";

export type TalkingAvatarHandle = {
  speakAudioBase64: (base64: string, text: string, mime?: string) => Promise<void>;
  speakBrowserText: (text: string) => Promise<void>;
  stopSpeaking: () => void;
};

type Props = {
  name: string;
  audience?: string | null;
  isListening?: boolean;
  isSpeaking?: boolean;
  onReadyChange?: (ready: boolean) => void;
  onSpeakEnd?: () => void;
};

type TalkingHeadInstance = {
  showAvatar: (avatar: Record<string, unknown>, onprogress?: (ev: ProgressEvent) => void) => Promise<void>;
  setView: (view: string, opt?: Record<string, number>) => void;
  setMood: (mood: string) => void;
  speakAudio: (audio: Record<string, unknown>, opt?: Record<string, unknown>) => void;
  stopSpeaking?: () => void;
  start?: () => void;
  stop?: () => void;
  playGesture?: (name: string, dur?: number) => void;
  lipsync: Record<string, unknown>;
  audioCtx: AudioContext;
  opt: Record<string, unknown>;
};

function estimateWordTimings(text: string, durationMs: number) {
  const words = text
    .replace(/[^\p{L}\p{N}\s'-]/gu, " ")
    .split(/\s+/)
    .filter(Boolean);
  if (!words.length) {
    return { words: [text || "…"], wtimes: [0], wdurations: [durationMs] };
  }
  const totalChars = words.reduce((s, w) => s + Math.max(w.length, 1), 0);
  let t = 40;
  const wtimes: number[] = [];
  const wdurations: number[] = [];
  const usable = Math.max(durationMs - 80, words.length * 80);
  for (const word of words) {
    const share = Math.max(word.length, 1) / totalChars;
    const dur = Math.max(70, usable * share);
    wtimes.push(t);
    wdurations.push(dur);
    t += dur;
  }
  return { words, wtimes, wdurations };
}

async function decodeBase64Audio(
  ctx: AudioContext,
  base64: string,
  mime = "audio/mpeg",
): Promise<AudioBuffer> {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  const copy = bytes.buffer.slice(0);
  return ctx.decodeAudioData(copy);
}

const TalkingAvatar3D = forwardRef<TalkingAvatarHandle, Props>(function TalkingAvatar3D(
  { name, audience, isListening, isSpeaking, onReadyChange, onSpeakEnd },
  ref,
) {
  const mountRef = useRef<HTMLDivElement>(null);
  const headRef = useRef<TalkingHeadInstance | null>(null);
  const [ready, setReady] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const speakEndRef = useRef(onSpeakEnd);
  const onReadyChangeRef = useRef(onReadyChange);
  speakEndRef.current = onSpeakEnd;
  onReadyChangeRef.current = onReadyChange;

  useEffect(() => {
    let cancelled = false;
    let head: TalkingHeadInstance | null = null;

    async function init() {
      if (!mountRef.current) return;
      try {
        const [{ TalkingHead }, { LipsyncEn }, { LipsyncDe }] = await Promise.all([
          import("@met4citizen/talkinghead/modules/talkinghead.mjs"),
          import("@met4citizen/talkinghead/modules/lipsync-en.mjs"),
          import("@met4citizen/talkinghead/modules/lipsync-de.mjs"),
        ]);

        if (cancelled || !mountRef.current) return;

        mountRef.current.innerHTML = "";
        head = new TalkingHead(mountRef.current, {
          lipsyncModules: [],
          lipsyncLang: "en",
          cameraView: "upper",
          cameraDistance: -0.15,
          modelFPS: 30,
          // Library multiplies by devicePixelRatio — keep 1 for crisp retina without overdraw
          modelPixelRatio: 1,
          ...STUDIO_LIGHTING,
          avatarIdleHeadMove: 0.45,
          avatarSpeakingHeadMove: 0.55,
          avatarSpeakingEyeContact: 0.65,
        }) as TalkingHeadInstance;

        head.lipsync.en = new LipsyncEn();
        head.lipsync.de = new LipsyncDe();

        const preset = getAvatarPreset(audience);

        await head.showAvatar(
          {
            url: preset.url,
            body: preset.body,
            avatarMood: preset.avatarMood,
            lipsyncLang: preset.lipsyncLang,
            retarget: preset.retarget,
            baseline: preset.baseline,
          },
          (ev) => {
            if (ev.lengthComputable && ev.total > 0) {
              setProgress(Math.round((ev.loaded / ev.total) * 100));
            }
          },
        );

        if (cancelled) {
          head.stop?.();
          return;
        }

        head.setView("upper", { cameraDistance: -0.12, cameraY: 0.02 });
        headRef.current = head;
        setReady(true);
        onReadyChangeRef.current?.(true);
      } catch (err) {
        console.error("TalkingHead init failed", err);
        if (!cancelled) {
          setLoadError("Не удалось загрузить 3D-модель");
          onReadyChangeRef.current?.(false);
        }
      }
    }

    void init();

    return () => {
      cancelled = true;
      try {
        head?.stopSpeaking?.();
        head?.stop?.();
      } catch {
        /* ignore */
      }
      headRef.current = null;
      if (mountRef.current) mountRef.current.innerHTML = "";
    };
    // Re-init when audience changes (child vs adult avatar)
  }, [audience]);

  useEffect(() => {
    const head = headRef.current;
    if (!head || !ready) return;
    try {
      if (isListening) {
        head.setMood("curious");
        head.playGesture?.("handup", 2);
      } else if (isSpeaking) {
        head.setMood(audience === "child" ? "happy" : "neutral");
      } else {
        head.setMood(audience === "child" ? "happy" : "neutral");
      }
    } catch {
      /* mood optional */
    }
  }, [isListening, isSpeaking, ready, audience]);

  useImperativeHandle(
    ref,
    () => ({
      async speakAudioBase64(base64, text, mime = "audio/mpeg") {
        const head = headRef.current;
        if (!head) throw new Error("Avatar not ready");
        if (head.audioCtx.state === "suspended") {
          await head.audioCtx.resume();
        }
        const buffer = await decodeBase64Audio(head.audioCtx, base64, mime);
        const durationMs = buffer.duration * 1000;
        const timing = estimateWordTimings(text, durationMs);
        const lipsyncLang = /[äöüß]|der |die |das /i.test(text) ? "de" : "en";

        await new Promise<void>((resolve) => {
          let settled = false;
          const done = () => {
            if (settled) return;
            settled = true;
            speakEndRef.current?.();
            resolve();
          };
          const safety = window.setTimeout(done, durationMs + 1200);
          head.speakAudio(
            {
              audio: buffer,
              words: timing.words,
              wtimes: timing.wtimes,
              wdurations: timing.wdurations,
              markers: [
                () => {
                  window.clearTimeout(safety);
                  done();
                },
              ],
              mtimes: [Math.max(durationMs - 30, 0)],
            },
            { lipsyncLang },
          );
        });
      },

      async speakBrowserText(text) {
        const head = headRef.current;
        if (!("speechSynthesis" in window)) {
          speakEndRef.current?.();
          return;
        }
        window.speechSynthesis.cancel();
        const utter = new SpeechSynthesisUtterance(text);
        utter.lang = "ru-RU";
        utter.rate = 1.02;
        const voices = window.speechSynthesis.getVoices();
        const ru = voices.find((v) => v.lang.startsWith("ru"));
        if (ru) utter.voice = ru;

        // Drive 3D lips with a silent buffer timed to estimated speech length
        if (head) {
          const approxMs = Math.max(1200, text.split(/\s+/).length * 320);
          const timing = estimateWordTimings(text, approxMs);
          const sampleRate = head.audioCtx.sampleRate || 22050;
          const frames = Math.ceil((approxMs / 1000) * sampleRate);
          const silent = head.audioCtx.createBuffer(1, frames, sampleRate);
          try {
            if (head.audioCtx.state === "suspended") await head.audioCtx.resume();
            head.speakAudio(
              {
                audio: silent,
                words: timing.words,
                wtimes: timing.wtimes,
                wdurations: timing.wdurations,
              },
              { lipsyncLang: "en" },
            );
          } catch {
            /* lip-sync optional for browser TTS */
          }
        }

        await new Promise<void>((resolve) => {
          utter.onend = () => {
            speakEndRef.current?.();
            resolve();
          };
          utter.onerror = () => {
            speakEndRef.current?.();
            resolve();
          };
          window.speechSynthesis.speak(utter);
        });
      },

      stopSpeaking() {
        try {
          headRef.current?.stopSpeaking?.();
          window.speechSynthesis?.cancel();
        } catch {
          /* ignore */
        }
      },
    }),
    [],
  );

  const statusLine =
    loadError ||
    (!ready ? `Загрузка 3D-учителя${progress ? ` · ${progress}%` : "…"}` : null);

  return (
    <div className="avatar3d-wrap">
      <div
        ref={mountRef}
        className={`avatar3d-stage ${isSpeaking ? "is-speaking" : ""} ${
          isListening ? "is-listening" : ""
        }`}
        aria-label={`3D учитель ${name}`}
      />
      {statusLine && <p className="avatar3d-status">{statusLine}</p>}
      {ready && (
        <>
          <p className="avatar3d-name">{name}</p>
          <p className="avatar3d-role">
            {isListening
              ? "Слушаю…"
              : isSpeaking
                ? "Говорю…"
                : audience === "child"
                  ? "Твой учитель · живой 3D"
                  : "Премиум-репетитор · 3D"}
          </p>
        </>
      )}
    </div>
  );
});

export default TalkingAvatar3D;
