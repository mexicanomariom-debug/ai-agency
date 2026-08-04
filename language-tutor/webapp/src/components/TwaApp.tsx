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
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-400" />
      </div>
    );
  }

  if (view === "personas") {
    return (
      <div className="min-h-screen px-4 py-6">
        <div className="mx-auto max-w-2xl">
          <h1 className="mb-1 text-2xl font-bold">Choose Your Tutor</h1>
          <p className="mb-6 text-sm text-zinc-400">
            {user
              ? `Hello, ${user.first_name}! Pick a persona to start practicing.`
              : DEMO_MODE
                ? "Demo mode — pick a persona to start practicing."
                : "Pick a persona to start practicing."}
          </p>
          {error && (
            <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">
              {error}
            </div>
          )}
          <div className="grid gap-4">
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
    <div className="flex min-h-screen flex-col">
      <header className="flex items-center gap-3 border-b border-zinc-800 px-4 py-3">
        <button
          onClick={() => setView("personas")}
          className="rounded-lg p-1.5 text-zinc-400 transition hover:bg-zinc-800 hover:text-white"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div>
          <h2 className="font-semibold">{selectedPersona?.name}</h2>
          <p className="text-xs capitalize text-zinc-500">{selectedPersona?.language}</p>
        </div>
      </header>

      <div className="chat-scroll flex-1 overflow-y-auto px-4 py-4">
        <div className="mx-auto max-w-2xl space-y-4">
          {messages.length === 0 && (
            <p className="text-center text-sm text-zinc-500">
              Start a conversation with {selectedPersona?.name}!
            </p>
          )}
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-indigo-600 text-white"
                    : "bg-zinc-800 text-zinc-100"
                }`}
              >
                {msg.content || (streaming && i === messages.length - 1 ? "..." : "")}
              </div>
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>
      </div>

      <div className="border-t border-zinc-800 px-4 py-3">
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
            placeholder="Type your message..."
            disabled={streaming}
            className="flex-1 rounded-xl border border-zinc-700 bg-zinc-900 px-4 py-2.5 text-sm text-white placeholder-zinc-500 outline-none focus:border-indigo-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={streaming || !input.trim()}
            className="flex items-center justify-center rounded-xl bg-indigo-600 px-4 py-2.5 text-white transition hover:bg-indigo-500 disabled:opacity-50"
          >
            {streaming ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
