import { NextRequest, NextResponse } from "next/server";
import { buildVoiceFallbackSystemPrompt } from "@/lib/tutorPedagogy";

const BACKEND_URL = process.env.BACKEND_URL || "http://140.84.183.154:8000";
const OPENAI_API_KEY = process.env.OPENAI_API_KEY || "";
const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY || "";
const OPENAI_MODEL = process.env.OPENAI_MODEL || "gpt-4o-mini";
const ANTHROPIC_MODEL = process.env.ANTHROPIC_MODEL || "claude-sonnet-5";
const TTS_VOICE = process.env.OPENAI_TTS_VOICE || "onyx";

async function tryOracle(request: NextRequest, form: FormData): Promise<NextResponse | null> {
  const headers = new Headers();
  const initData = request.headers.get("x-telegram-init-data");
  const demo = request.headers.get("x-demo-mode");
  if (initData) headers.set("X-Telegram-Init-Data", initData);
  if (demo) headers.set("X-Demo-Mode", demo);

  // Whisper + LLM + TTS on Oracle regularly exceeds 8s — do not treat timeout as "port closed"
  const res = await fetch(`${BACKEND_URL}/api/voice/talk`, {
    method: "POST",
    headers,
    body: form,
    signal: AbortSignal.timeout(90000),
    cache: "no-store",
  });
  if (!res.ok && res.status >= 500) {
    return null;
  }
  const text = await res.text();
  return new NextResponse(text, {
    status: res.status,
    headers: { "Content-Type": res.headers.get("content-type") || "application/json" },
  });
}

function firstNameFromInit(request: NextRequest): string {
  const initData = request.headers.get("x-telegram-init-data") || "";
  try {
    const userRaw = new URLSearchParams(initData).get("user");
    if (userRaw) {
      const user = JSON.parse(userRaw) as { first_name?: string };
      if (user.first_name) return user.first_name;
    }
  } catch {
    /* ignore */
  }
  return "друг";
}

async function transcribe(audio: Blob): Promise<string> {
  const form = new FormData();
  form.append("file", audio, "voice.webm");
  form.append("model", "whisper-1");
  form.append("language", "ru");

  const res = await fetch("https://api.openai.com/v1/audio/transcriptions", {
    method: "POST",
    headers: { Authorization: `Bearer ${OPENAI_API_KEY}` },
    body: form,
  });
  if (!res.ok) throw new Error(`Whisper: ${res.status}`);
  const data = (await res.json()) as { text?: string };
  return (data.text || "").trim();
}

async function chatReply(transcript: string, name: string): Promise<string> {
  const system = buildVoiceFallbackSystemPrompt(name);

  if (ANTHROPIC_API_KEY) {
    const res = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: ANTHROPIC_MODEL,
        max_tokens: 300,
        system,
        messages: [{ role: "user", content: transcript }],
      }),
    });
    if (!res.ok) throw new Error(`Claude: ${res.status}`);
    const data = (await res.json()) as { content?: { type: string; text?: string }[] };
    return data.content?.find((c) => c.type === "text")?.text?.trim() || "Попробуйте ещё раз.";
  }

  const res = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${OPENAI_API_KEY}`,
    },
    body: JSON.stringify({
      model: OPENAI_MODEL,
      messages: [
        { role: "system", content: system },
        { role: "user", content: transcript },
      ],
    }),
  });
  if (!res.ok) throw new Error(`OpenAI chat: ${res.status}`);
  const data = (await res.json()) as {
    choices?: { message?: { content?: string } }[];
  };
  return data.choices?.[0]?.message?.content?.trim() || "Попробуйте ещё раз.";
}

async function synthesize(text: string): Promise<string | null> {
  const res = await fetch("https://api.openai.com/v1/audio/speech", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${OPENAI_API_KEY}`,
    },
    body: JSON.stringify({
      model: "tts-1",
      voice: TTS_VOICE,
      input: text,
    }),
  });
  if (!res.ok) return null;
  const buf = Buffer.from(await res.arrayBuffer());
  return buf.toString("base64");
}

async function localVoicePipeline(request: NextRequest, audio: Blob) {
  if (!OPENAI_API_KEY) {
    return NextResponse.json(
      {
        transcript: "",
        reply: "",
        audio_base64: null,
        error:
          "Сервер учителя временно не ответил, а на Vercel нет OPENAI_API_KEY для запасного распознавания. Удерживайте микрофон (браузерный режим) или добавьте OPENAI_API_KEY в Vercel → webapp → Environment Variables. Если не помогает — откройте TCP 8000 в Oracle Cloud Security List.",
      },
      { status: 503 },
    );
  }

  const transcript = await transcribe(audio);
  if (!transcript) {
    return NextResponse.json({
      transcript: "",
      reply: "Я вас не расслышала. Попробуйте говорить чуть громче.",
      audio_base64: null,
    });
  }

  const name = firstNameFromInit(request);
  const reply = await chatReply(transcript, name);
  const audio_base64 = await synthesize(reply);

  return NextResponse.json({
    transcript,
    reply,
    audio_base64,
    audio_mime: audio_base64 ? "audio/mpeg" : null,
  });
}

export async function POST(request: NextRequest) {
  const form = await request.formData();
  const audio = form.get("audio");

  // Prefer Oracle when reachable (full tutor context + DB)
  try {
    const oracleRes = await tryOracle(request, form);
    if (oracleRes) return oracleRes;
  } catch {
    /* fall through to Vercel-local pipeline */
  }

  if (!(audio instanceof Blob)) {
    return NextResponse.json(
      { transcript: "", reply: "", audio_base64: null, error: "Нет аудио" },
      { status: 400 },
    );
  }

  try {
    return await localVoicePipeline(request, audio);
  } catch (err) {
    return NextResponse.json(
      {
        transcript: "",
        reply: "",
        audio_base64: null,
        error: err instanceof Error ? err.message : "Ошибка голосового API",
      },
      { status: 500 },
    );
  }
}
