import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://140.84.183.154:8000";
const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY || "";
const OPENAI_API_KEY = process.env.OPENAI_API_KEY || "";

function authHeaders(request: NextRequest): Headers {
  const headers = new Headers({ "Content-Type": "application/json" });
  const initData = request.headers.get("x-telegram-init-data");
  const demo = request.headers.get("x-demo-mode");
  if (initData) headers.set("X-Telegram-Init-Data", initData);
  if (demo) headers.set("X-Demo-Mode", demo);
  return headers;
}

async function localChat(message: string, name: string): Promise<Response> {
  const system = `Ты Илья — харизматичный AI-учитель языков. Ученик: ${name}.
Отвечай кратко (2–4 предложения), по-русски с примерами на изучаемом языке. Без markdown.`;

  if (ANTHROPIC_API_KEY) {
    const res = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: process.env.ANTHROPIC_MODEL || "claude-sonnet-4-20250514",
        max_tokens: 300,
        system,
        messages: [{ role: "user", content: message }],
      }),
    });
    if (!res.ok) throw new Error(`Claude: ${res.status}`);
    const data = (await res.json()) as { content?: { type: string; text?: string }[] };
    const reply = data.content?.find((c) => c.type === "text")?.text?.trim() || "Попробуйте ещё раз.";
    return NextResponse.json({ transcript: message, reply, audio_base64: null });
  }

  if (OPENAI_API_KEY) {
    const res = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${OPENAI_API_KEY}`,
      },
      body: JSON.stringify({
        model: process.env.OPENAI_MODEL || "gpt-4o-mini",
        messages: [
          { role: "system", content: system },
          { role: "user", content: message },
        ],
      }),
    });
    if (!res.ok) throw new Error(`OpenAI: ${res.status}`);
    const data = (await res.json()) as { choices?: { message?: { content?: string } }[] };
    const reply = data.choices?.[0]?.message?.content?.trim() || "Попробуйте ещё раз.";
    return NextResponse.json({ transcript: message, reply, audio_base64: null });
  }

  return NextResponse.json(
    {
      transcript: message,
      reply: "",
      audio_base64: null,
      error: "Нет ANTHROPIC_API_KEY / OPENAI_API_KEY на сервере.",
    },
    { status: 503 },
  );
}

export async function POST(request: NextRequest) {
  const body = (await request.json()) as { message?: string };
  const message = (body.message || "").trim();
  if (!message) {
    return NextResponse.json({
      transcript: "",
      reply: "Пустое сообщение.",
      audio_base64: null,
    });
  }

  try {
    const res = await fetch(`${BACKEND_URL}/api/voice/chat`, {
      method: "POST",
      headers: authHeaders(request),
      body: JSON.stringify({ message }),
      signal: AbortSignal.timeout(60000),
      cache: "no-store",
    });
    if (res.ok) {
      return new NextResponse(await res.text(), {
        status: res.status,
        headers: { "Content-Type": "application/json" },
      });
    }
  } catch {
    /* Oracle down — local LLM */
  }

  let name = "друг";
  try {
    const initData = request.headers.get("x-telegram-init-data") || "";
    const userRaw = new URLSearchParams(initData).get("user");
    if (userRaw) {
      const user = JSON.parse(userRaw) as { first_name?: string };
      if (user.first_name) name = user.first_name;
    }
  } catch {
    /* ignore */
  }

  try {
    return await localChat(message, name);
  } catch (err) {
    return NextResponse.json(
      {
        transcript: message,
        reply: "",
        audio_base64: null,
        error: err instanceof Error ? err.message : "Ошибка чата",
      },
      { status: 500 },
    );
  }
}
