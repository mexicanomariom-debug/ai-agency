import { NextRequest, NextResponse } from "next/server";

const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID || "";
const GOOGLE_CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET || "";
const GOOGLE_REDIRECT_URI =
  process.env.GOOGLE_REDIRECT_URI ||
  "https://ai-agency-drab.vercel.app/api/google/oauth/callback";
const PERSONAL_AGENT_BOT_URL =
  process.env.PERSONAL_AGENT_BOT_URL || "http://140.84.183.154:8081";
<<<<<<< HEAD
const PERSONAL_AGENT_INTERNAL_SECRET = process.env.PERSONAL_AGENT_INTERNAL_SECRET || "";

function htmlPage(title: string, message: string, ok: boolean) {
  return `<!DOCTYPE html>
<html lang="ru">
<head><meta charset="utf-8"><title>${title}</title></head>
<body style="font-family:sans-serif;max-width:480px;margin:40px auto;padding:20px">
  <h2>${ok ? "✅" : "❌"} ${title}</h2>
  <p>${message}</p>
  <p>Можете вернуться в Telegram.</p>
</body></html>`;
=======
const PERSONAL_AGENT_INTERNAL_SECRET =
  process.env.PERSONAL_AGENT_INTERNAL_SECRET || "personal-agent-internal-2026";

function callbackPage(options: {
  title: string;
  message: string;
  ok: boolean;
  telegramId?: string;
  code?: string;
}) {
  const { title, message, ok, telegramId, code } = options;
  const botCode = code ? `/google_code ${code}` : "";
  const payload = JSON.stringify({
    telegram_id: telegramId ? parseInt(telegramId, 10) : 0,
    code: code || "",
  });

  return `<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${title}</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 520px; margin: 32px auto; padding: 16px; line-height: 1.5; }
    .box { background: #f4f4f5; border-radius: 12px; padding: 14px; word-break: break-all; font-family: monospace; font-size: 13px; }
    .hint { color: #555; font-size: 14px; }
    #status { margin-top: 12px; font-weight: 600; }
  </style>
</head>
<body>
  <h2>${ok ? "✅" : "❌"} ${title}</h2>
  <p>${message}</p>
  ${code ? `<p class="hint">Если Telegram молчит — отправьте боту:</p>
  <div class="box" id="cmd">${botCode}</div>
  <p><button onclick="navigator.clipboard.writeText(document.getElementById('cmd').textContent)">Скопировать команду</button></p>
  <p id="status">Подключаем календарь…</p>` : ""}
  <p>Можете вернуться в Telegram.</p>
  ${code ? `<script>
    (async function () {
      const status = document.getElementById("status");
      const payload = ${payload};
      if (!payload.telegram_id || !payload.code) {
        status.textContent = "Скопируйте команду выше и отправьте боту.";
        return;
      }
      try {
        const res = await fetch("${PERSONAL_AGENT_BOT_URL}/internal/google-token", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Internal-Secret": "${PERSONAL_AGENT_INTERNAL_SECRET}",
          },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          status.textContent = "Готово! Вернитесь в Telegram — должно прийти сообщение о подключении.";
          return;
        }
        const detail = await res.text();
        status.textContent = "Автоподключение не сработало. Скопируйте команду выше и отправьте боту. (" + detail + ")";
      } catch (e) {
        status.textContent = "Автоподключение не сработало. Скопируйте команду выше и отправьте боту.";
      }
    })();
  </script>` : ""}
</body>
</html>`;
}

async function forwardCodeToBot(telegramId: number, code: string): Promise<boolean> {
  try {
    const botRes = await fetch(`${PERSONAL_AGENT_BOT_URL}/internal/google-token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Internal-Secret": PERSONAL_AGENT_INTERNAL_SECRET,
      },
      body: JSON.stringify({ telegram_id: telegramId, code }),
      signal: AbortSignal.timeout(15000),
    });
    return botRes.ok;
  } catch {
    return false;
  }
>>>>>>> cursor/personal-agent-task-scheduler-64cf
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const error = searchParams.get("error");
  const code = searchParams.get("code");
  const state = searchParams.get("state");

  if (error) {
    return new NextResponse(
<<<<<<< HEAD
      htmlPage("Ошибка авторизации", error, false),
=======
      callbackPage({ title: "Ошибка авторизации", message: error, ok: false }),
>>>>>>> cursor/personal-agent-task-scheduler-64cf
      { status: 400, headers: { "Content-Type": "text/html; charset=utf-8" } },
    );
  }

  if (!code || !state || !/^\d+$/.test(state)) {
    return new NextResponse(
<<<<<<< HEAD
      htmlPage("Ошибка", "Некорректный ответ от Google", false),
=======
      callbackPage({ title: "Ошибка", message: "Некорректный ответ от Google", ok: false }),
>>>>>>> cursor/personal-agent-task-scheduler-64cf
      { status: 400, headers: { "Content-Type": "text/html; charset=utf-8" } },
    );
  }

<<<<<<< HEAD
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
        ...(PERSONAL_AGENT_INTERNAL_SECRET
          ? { "X-Internal-Secret": PERSONAL_AGENT_INTERNAL_SECRET }
          : {}),
      },
      body: JSON.stringify({
        telegram_id: parseInt(state, 10),
        refresh_token: refreshToken,
      }),
      signal: AbortSignal.timeout(15000),
    });

    if (!botRes.ok) {
      const detail = await botRes.text();
      return new NextResponse(
        htmlPage("Ошибка бота", `Бот не принял токен: ${detail}`, false),
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
=======
  const telegramId = parseInt(state, 10);

  // Server-side attempt (may fail if Vercel blocks outbound HTTP to Oracle IP)
  const serverOk = await forwardCodeToBot(telegramId, code);

  if (serverOk) {
    return new NextResponse(
      callbackPage({
        title: "Google Calendar подключён!",
        message: "Новые задачи будут синхронизироваться. Вернитесь в Telegram.",
        ok: true,
        telegramId: state,
        code,
      }),
      { status: 200, headers: { "Content-Type": "text/html; charset=utf-8" } },
    );
  }

  // Browser-side retry + /google_code fallback (always show code)
  return new NextResponse(
    callbackPage({
      title: "Завершите подключение в Telegram",
      message:
        "Вход в Google выполнен. Сейчас страница попробует подключить календарь автоматически. " +
        "Если в Telegram не придёт «Google Calendar подключён» — скопируйте команду ниже и отправьте боту.",
      ok: true,
      telegramId: state,
      code,
    }),
>>>>>>> cursor/personal-agent-task-scheduler-64cf
    { status: 200, headers: { "Content-Type": "text/html; charset=utf-8" } },
  );
}
