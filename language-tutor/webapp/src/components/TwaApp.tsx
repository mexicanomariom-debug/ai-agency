"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowLeft, Loader2, Send } from "lucide-react";
import CharacterCard from "@/components/CharacterCard";
import {
  DEMO_MODE,
  fetchPersonas,
  type ChatMessage,
  type Persona,
  streamChat,
} from "@/lib/api";
import { useTelegram } from "@/hooks/useTelegram";

type View = "personas" | "chat";

export default function TwaApp() {
  const { initData, user, isReady } = useTelegram();
  const [view, setView] = useState<View>("personas");
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [selectedPersona, setSelectedPersona] = useState<Persona | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isReady) return;
    fetchPersonas(initData || undefined)
      .then(setPersonas)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [isReady, initData]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSelectPersona = (persona: Persona) => {
    setSelectedPersona(persona);
    setMessages([]);
    setView("chat");
  };

  const handleSend = useCallback(async () => {
    if (!input.trim() || streaming) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setStreaming(true);

    let assistantContent = "";
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      for await (const chunk of streamChat(
        userMessage,
        selectedPersona?.slug ?? null,
        initData || undefined,
      )) {
        if (chunk.error) {
          setError(chunk.error);
          break;
        }
        if (chunk.content) {
          assistantContent += chunk.content;
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = { role: "assistant", content: assistantContent };
            return updated;
          });
        }
        if (chunk.done) break;
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Stream failed");
    } finally {
      setStreaming(false);
    }
  }, [input, streaming, selectedPersona, initData]);

  if (loading) {
    return (
      <div className="opus-app flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-[var(--gold)]" />
      </div>
    );
  }

  if (view === "personas") {
    return (
      <div className="opus-app min-h-screen px-4 py-6">
        <div className="mx-auto max-w-2xl">
          <p className="opus-kicker">Persona Lounge</p>
          <h1 className="mt-1 font-[family-name:var(--font-display)] text-2xl font-semibold">
            Choose your tutor
          </h1>
          <p className="mb-6 mt-2 text-sm text-[var(--muted-fg)]">
            {user
              ? `Hello, ${user.first_name} — pick a voice and start practicing.`
              : DEMO_MODE
                ? "Demo mode — pick a persona to start."
                : "Pick a persona to start practicing."}
          </p>
          {error && (
            <div className="mb-4 rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">
              {error}
            </div>
          )}
          <div className="grid gap-3">
            {personas.map((p) => (
              <CharacterCard
                key={p.slug}
                persona={p}
                selected={selectedPersona?.slug === p.slug}
                onSelect={handleSelectPersona}
              />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="opus-app flex min-h-screen flex-col">
      <header className="opus-app-header flex items-center gap-3 px-4 py-3">
        <button
          type="button"
          onClick={() => setView("personas")}
          className="rounded-lg p-1.5 text-[var(--muted-fg)] transition hover:bg-[var(--surface)] hover:text-white"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div>
          <h2 className="font-semibold">{selectedPersona?.name}</h2>
          <p className="text-xs capitalize text-[var(--muted-fg)]">{selectedPersona?.language}</p>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-4 py-4">
        <div className="mx-auto max-w-2xl space-y-4">
          {messages.length === 0 && (
            <p className="text-center text-sm text-[var(--muted-fg)]">
              Start a conversation with {selectedPersona?.name}
            </p>
          )}
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                  msg.role === "user" ? "opus-chat-bubble-user" : "opus-chat-bubble-assistant"
                }`}
              >
                {msg.content || (streaming && i === messages.length - 1 ? "…" : "")}
              </div>
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>
      </div>

      <div className="border-t border-[var(--panel-border)] px-4 py-3">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="mx-auto flex max-w-2xl gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message…"
            disabled={streaming}
            className="opus-input"
          />
          <button
            type="submit"
            disabled={streaming || !input.trim()}
            className="opus-btn opus-btn--primary opus-btn--sm disabled:opacity-50"
          >
            {streaming ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
          </button>
        </form>
      </div>
    </div>
  );
}
