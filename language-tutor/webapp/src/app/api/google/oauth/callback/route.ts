import { NextRequest, NextResponse } from "next/server";

const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID || "";
const GOOGLE_CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET || "";
const GOOGLE_REDIRECT_URI =
  process.env.GOOGLE_REDIRECT_URI ||
  "https://ai-agency-drab.vercel.app/api/google/oauth/callback";
const PERSONAL_AGENT_BOT_URL =
  process.env.PERSONAL_AGENT_BOT_URL || "http://140.84.183.154:8081";
const PERSONAL_AGENT_INTERNAL_SECRET =
  process.env.PERSONAL_AGENT_INTERNAL_SECRET || "personal-agent-internal-2026";

function htmlPage(title: string, message: string, ok: boolean) {
  return `<!DOCTYPE html>
<html lang="ru">
<head><meta charset="utf-8"><title>${title}</title></head>
<body style="font-family:sans-serif;max-width:480px;margin:40px auto;padding:20px">
  <h2>${ok ? "✅" : "❌"} ${title}</h2>
  <p>${message}</p>
  <p>Можете вернуться в Telegram.</p>
</body></html>`;
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const error = searchParams.get("error");
  const code = searchParams.get("code");
  const state = searchParams.get("state");

  if (error) {
    return new NextResponse(
      htmlPage("Ошибка авторизации", error, false),
      { status: 400, headers: { "Content-Type": "text/html; charset=utf-8" } },
    );
  }

  if (!code || !state || !/^\d+$/.test(state)) {
    return new NextResponse(
      htmlPage("Ошибка", "Некорректный ответ от Google", false),
      { status: 400, headers: { "Content-Type": "text/html; charset=utf-8" } },
    );
  }

  if (!GOOGLE_CLIENT_ID || !GOOGLE_CLIENT_SECRET) {
    return new NextResponse(
      htmlPage("Не настроено", "Добавьте GOOGLE_CLIENT_ID и GOOGLE_CLIENT_SECRET в Vercel", false),
      { status: 500, headers: { "Content-Type": "text/html; charset=utf-8" } },
    );
  }

  const tokenRes = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      code,
      client_id: GOOGLE_CLIENT_ID,
      client_secret: GOOGLE_CLIENT_SECRET,
      redirect_uri: GOOGLE_REDIRECT_URI,
      grant_type: "authorization_code",
    }),
  });

  const tokens = await tokenRes.json();
  const refreshToken = tokens.refresh_token as string | undefined;

  if (!refreshToken) {
    return new NextResponse(
      htmlPage("Ошибка", "Не удалось получить токен Google. Попробуйте /calendar снова.", false),
      { status: 400, headers: { "Content-Type": "text/html; charset=utf-8" } },
    );
  }

  try {
    const botRes = await fetch(`${PERSONAL_AGENT_BOT_URL}/internal/google-token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Internal-Secret": PERSONAL_AGENT_INTERNAL_SECRET,
      },
      body: JSON.stringify({
        telegram_id: parseInt(state, 10),
        refresh_token: refreshToken,
      }),
      signal: AbortSignal.timeout(15000),
    });

    if (!botRes.ok) {
      const detail = await botRes.text();
      let hint = detail;
      if (detail.includes("unauthorized")) {
        hint = "Секрет PERSONAL_AGENT_INTERNAL_SECRET не совпадает в Vercel и на сервере бота.";
      } else if (detail.includes("user not found")) {
        hint = "Сначала напишите боту /start, затем снова /calendar.";
      }
      return new NextResponse(
        htmlPage("Ошибка бота", `Бот не принял токен: ${hint}`, false),
        { status: 502, headers: { "Content-Type": "text/html; charset=utf-8" } },
      );
    }
  } catch {
    return new NextResponse(
      htmlPage(
        "Сервер недоступен",
        "Не удалось связаться с ботом на Oracle. Проверьте порт 8081.",
        false,
      ),
      { status: 502, headers: { "Content-Type": "text/html; charset=utf-8" } },
    );
  }

  return new NextResponse(
    htmlPage("Google Calendar подключён!", "Новые задачи будут синхронизироваться.", true),
    { status: 200, headers: { "Content-Type": "text/html; charset=utf-8" } },
  );
}
