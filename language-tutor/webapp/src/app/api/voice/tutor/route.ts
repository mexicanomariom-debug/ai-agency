import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://140.84.183.154:8000";

function fallbackTutor(req: NextRequest) {
  const initData = req.headers.get("x-telegram-init-data") || "";
  let firstName = "друг";
  try {
    const params = new URLSearchParams(initData);
    const userRaw = params.get("user");
    if (userRaw) {
      const user = JSON.parse(userRaw) as { first_name?: string };
      if (user.first_name) firstName = user.first_name;
    }
  } catch {
    /* ignore */
  }

  return {
    name: "Елена",
    slug: "voice-teacher",
    description: "Голосовой AI-учитель",
    language: null,
    level: null,
    greeting: `Привет, ${firstName}! Я Елена, ваш учитель. Нажмите на микрофон и говорите — я отвечу голосом.`,
  };
}

export async function GET(request: NextRequest) {
  try {
    const headers = new Headers();
    const initData = request.headers.get("x-telegram-init-data");
    const demo = request.headers.get("x-demo-mode");
    if (initData) headers.set("X-Telegram-Init-Data", initData);
    if (demo) headers.set("X-Demo-Mode", demo);

    const res = await fetch(`${BACKEND_URL}/api/voice/tutor`, {
      headers,
      signal: AbortSignal.timeout(4000),
      cache: "no-store",
    });
    if (res.ok) {
      return NextResponse.json(await res.json());
    }
  } catch {
    /* Oracle unreachable — serve local fallback so Mini App does not spin forever */
  }

  return NextResponse.json(fallbackTutor(request));
}
