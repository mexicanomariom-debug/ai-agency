import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://140.84.183.154:8000";

export async function GET(request: NextRequest) {
  try {
    const headers = new Headers();
    const initData = request.headers.get("x-telegram-init-data");
    const demo = request.headers.get("x-demo-mode");
    if (initData) headers.set("X-Telegram-Init-Data", initData);
    if (demo) headers.set("X-Demo-Mode", demo);

    const res = await fetch(`${BACKEND_URL}/api/voice/capabilities`, {
      headers,
      signal: AbortSignal.timeout(4000),
      cache: "no-store",
    });
    if (res.ok) return NextResponse.json(await res.json());
  } catch {
    /* fall through */
  }

  return NextResponse.json({
    llm: Boolean(process.env.ANTHROPIC_API_KEY || process.env.OPENAI_API_KEY),
    stt: Boolean(process.env.OPENAI_API_KEY),
    tts: Boolean(process.env.OPENAI_API_KEY),
    provider: process.env.ANTHROPIC_API_KEY
      ? "anthropic"
      : process.env.OPENAI_API_KEY
        ? "openai"
        : null,
    chat_model: process.env.ANTHROPIC_API_KEY
      ? process.env.ANTHROPIC_MODEL || "claude-sonnet-5"
      : process.env.OPENAI_API_KEY
        ? process.env.OPENAI_MODEL || "gpt-4o"
        : null,
  });
}
