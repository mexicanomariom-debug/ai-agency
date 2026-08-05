import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://140.84.183.154:8000";

export async function POST(request: NextRequest) {
  try {
    const form = await request.formData();
    const headers = new Headers();
    const initData = request.headers.get("x-telegram-init-data");
    const demo = request.headers.get("x-demo-mode");
    if (initData) headers.set("X-Telegram-Init-Data", initData);
    if (demo) headers.set("X-Demo-Mode", demo);

    const res = await fetch(`${BACKEND_URL}/api/voice/talk`, {
      method: "POST",
      headers,
      body: form,
      signal: AbortSignal.timeout(90000),
      cache: "no-store",
    });

    const text = await res.text();
    return new NextResponse(text, {
      status: res.status,
      headers: { "Content-Type": res.headers.get("content-type") || "application/json" },
    });
  } catch (err) {
    const message =
      err instanceof Error && err.name === "TimeoutError"
        ? "Сервер учителя не отвечает (таймаут). Откройте TCP 8000 в Oracle Cloud Security List."
        : "Нет связи с API учителя на Oracle (порт 8000 закрыт или API не запущен).";
    return NextResponse.json(
      {
        transcript: "",
        reply: "",
        audio_base64: null,
        audio_mime: null,
        error: message,
      },
      { status: 503 },
    );
  }
}
