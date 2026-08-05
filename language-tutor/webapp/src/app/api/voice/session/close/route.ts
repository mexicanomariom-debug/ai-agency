import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://140.84.183.154:8000";

export async function POST(request: NextRequest) {
  const headers = new Headers({ "Content-Type": "application/json" });
  const initData = request.headers.get("x-telegram-init-data");
  const demo = request.headers.get("x-demo-mode");
  if (initData) headers.set("X-Telegram-Init-Data", initData);
  if (demo) headers.set("X-Demo-Mode", demo);

  let body = "{}";
  try {
    body = await request.text();
  } catch {
    /* empty */
  }

  try {
    const res = await fetch(`${BACKEND_URL}/api/voice/session/close`, {
      method: "POST",
      headers,
      body: body || "{}",
      signal: AbortSignal.timeout(60000),
      cache: "no-store",
    });
    const text = await res.text();
    return new NextResponse(text, {
      status: res.status,
      headers: { "Content-Type": res.headers.get("content-type") || "application/json" },
    });
  } catch {
    return NextResponse.json(
      { assessed: false, skipped_reason: "backend_unreachable" },
      { status: 503 },
    );
  }
}
