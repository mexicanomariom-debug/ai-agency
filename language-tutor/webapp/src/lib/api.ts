export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
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
