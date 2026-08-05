// In production, requests go through Vercel proxy (HTTPS → Oracle HTTP)
export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== "undefined" ? "/api/proxy" : "http://140.84.183.154:8000");
export const TWA_URL = process.env.NEXT_PUBLIC_TWA_URL || "https://webapp-bay-three-75.vercel.app";
export const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === "true";
export const BOT_USERNAME = process.env.NEXT_PUBLIC_BOT_USERNAME || "All_languages_bot";

export interface Persona {
  id: number;
  slug: string;
  name: string;
  description: string;
  avatar_url: string | null;
  language: string | null;
}

export interface User {
  id: number;
  telegram_id: number;
  username: string | null;
  first_name: string | null;
  language: string | null;
  level: string | null;
  is_onboarded: boolean;
  subscription_tier: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface VoiceTutor {
  name: string;
  slug: string;
  description: string;
  language: string | null;
  level: string | null;
  audience?: string | null;
  greeting: string;
}

export interface VoiceTalkResult {
  transcript: string;
  reply: string;
  audio_base64: string | null;
  audio_mime: string | null;
  error?: string | null;
}

export interface VoiceSessionAssessment {
  assessed: boolean;
  skipped_reason?: string | null;
  speaking_cefr?: string | null;
  mapped_level?: string | null;
  confidence?: string | null;
  strengths?: string[];
  weaknesses?: string[];
  grammar_focus?: string[];
  recommendation?: string | null;
  summary?: string | null;
  level_updated?: boolean;
}

export function getAuthHeaders(initData?: string): HeadersInit {
  const headers: HeadersInit = { "Content-Type": "application/json" };
  if (initData) {
    headers["X-Telegram-Init-Data"] = initData;
  } else if (DEMO_MODE) {
    headers["X-Demo-Mode"] = "true";
  }
  return headers;
}

export async function fetchPersonas(initData?: string): Promise<Persona[]> {
  const res = await fetch(`${API_URL}/api/personas`, {
    headers: getAuthHeaders(initData),
  });
  if (!res.ok) throw new Error("Failed to fetch personas");
  return res.json();
}

export async function fetchUser(initData?: string): Promise<User> {
  const res = await fetch(`${API_URL}/api/users/me`, {
    headers: getAuthHeaders(initData),
  });
  if (!res.ok) throw new Error("Failed to fetch user");
  return res.json();
}

export async function* streamChat(
  message: string,
  personaSlug: string | null,
  initData?: string,
): AsyncGenerator<{ content?: string; done?: boolean; error?: string }> {
  const res = await fetch(`${API_URL}/api/chat/stream`, {
    method: "POST",
    headers: getAuthHeaders(initData),
    body: JSON.stringify({ message, persona_slug: personaSlug }),
  });

  if (!res.ok) {
    yield { error: `Request failed: ${res.status}` };
    return;
  }

  const reader = res.body?.getReader();
  if (!reader) {
    yield { error: "No response body" };
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          yield data;
        } catch {
          /* skip malformed */
        }
      }
    }
  }
}

/** Voice routes are Next.js handlers (with Oracle fallback), not the generic proxy. */
const VOICE_API = "/api/voice";

export interface VoiceCapabilities {
  llm: boolean;
  stt: boolean;
  tts: boolean;
  provider: string | null;
}

export async function fetchVoiceCapabilities(initData?: string): Promise<VoiceCapabilities> {
  try {
    const res = await fetch(`${VOICE_API}/capabilities`, {
      headers: getAuthHeaders(initData),
      cache: "no-store",
    });
    if (!res.ok) throw new Error("capabilities failed");
    return res.json();
  } catch {
    return { llm: true, stt: false, tts: false, provider: null };
  }
}

export async function fetchVoiceTutor(initData?: string): Promise<VoiceTutor> {
  const res = await fetch(`${VOICE_API}/tutor`, {
    headers: getAuthHeaders(initData),
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Не удалось загрузить учителя");
  return res.json();
}

export async function voiceTalk(audio: Blob, initData?: string): Promise<VoiceTalkResult> {
  const form = new FormData();
  form.append("audio", audio, "voice.webm");

  const headers: HeadersInit = {};
  if (initData) {
    headers["X-Telegram-Init-Data"] = initData;
  } else if (DEMO_MODE) {
    headers["X-Demo-Mode"] = "true";
  }

  const res = await fetch(`${VOICE_API}/talk`, {
    method: "POST",
    headers,
    body: form,
  });
  const data = (await res.json()) as VoiceTalkResult;
  if (!res.ok && !data.reply) {
    throw new Error(data.error || `Ошибка: ${res.status}`);
  }
  return data;
}

export async function voiceChat(message: string, initData?: string): Promise<VoiceTalkResult> {
  const res = await fetch(`${VOICE_API}/chat`, {
    method: "POST",
    headers: getAuthHeaders(initData),
    body: JSON.stringify({ message }),
  });
  const data = (await res.json()) as VoiceTalkResult;
  if (!res.ok && !data.reply) {
    throw new Error(data.error || `Ошибка: ${res.status}`);
  }
  return data;
}

export async function closeVoiceSession(
  initData?: string,
  personaSlug?: string | null,
): Promise<VoiceSessionAssessment> {
  const res = await fetch(`${VOICE_API}/session/close`, {
    method: "POST",
    headers: getAuthHeaders(initData),
    body: JSON.stringify({ persona_slug: personaSlug ?? "voice-teacher" }),
  });
  const data = (await res.json()) as VoiceSessionAssessment;
  if (!res.ok && !data.assessed) {
    return { assessed: false, skipped_reason: data.skipped_reason || "request_failed" };
  }
  return data;
}
