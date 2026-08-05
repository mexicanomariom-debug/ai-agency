"use client";

import { MessageCircle } from "lucide-react";
import type { Persona } from "@/lib/api";

interface CharacterCardProps {
  persona: Persona;
  selected?: boolean;
  onSelect: (persona: Persona) => void;
}

const LANGUAGE_COLORS: Record<string, string> = {
  spanish: "from-red-500/20 to-yellow-500/20",
  french: "from-blue-500/20 to-white/10",
  japanese: "from-red-500/20 to-pink-500/20",
  german: "from-yellow-500/20 to-red-500/20",
  english: "from-blue-500/20 to-indigo-500/20",
};

export default function CharacterCard({ persona, selected, onSelect }: CharacterCardProps) {
  const gradient = LANGUAGE_COLORS[persona.language || ""] || "from-indigo-500/20 to-cyan-500/20";

  return (
    <button
      onClick={() => onSelect(persona)}
      className={`group relative w-full rounded-2xl border p-5 text-left transition-all ${
        selected
          ? "border-indigo-500 bg-indigo-500/10 ring-2 ring-indigo-500/50"
          : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700 hover:bg-zinc-900"
      }`}
    >
      <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${gradient} opacity-50`} />
      <div className="relative">
        <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-zinc-800 text-2xl">
          {persona.avatar_url ? (
            <span role="img" aria-label={persona.name}>
              {persona.name.charAt(0)}
            </span>
          ) : (
            <MessageCircle className="h-6 w-6 text-indigo-400" />
          )}
        </div>
        <h3 className="text-lg font-semibold text-white">{persona.name}</h3>
        {persona.language && (
          <span className="mt-1 inline-block rounded-full bg-zinc-800 px-2 py-0.5 text-xs capitalize text-zinc-400">
            {persona.language}
          </span>
        )}
        <p className="mt-2 text-sm leading-relaxed text-zinc-400">{persona.description}</p>
      </div>
    </button>
  );
}
