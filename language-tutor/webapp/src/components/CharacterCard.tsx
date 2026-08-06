"use client";

import { MessageCircle } from "lucide-react";
import type { Persona } from "@/lib/api";

interface CharacterCardProps {
  persona: Persona;
  selected?: boolean;
  onSelect: (persona: Persona) => void;
}

const LANGUAGE_ACCENT: Record<string, string> = {
  spanish: "from-red-500/15 to-amber-500/10",
  french: "from-blue-500/15 to-white/5",
  japanese: "from-rose-500/15 to-pink-500/10",
  german: "from-amber-500/15 to-red-500/10",
  english: "from-[var(--gold)]/15 to-cyan-500/10",
};

export default function CharacterCard({ persona, selected, onSelect }: CharacterCardProps) {
  const gradient = LANGUAGE_ACCENT[persona.language || ""] || "from-[var(--gold)]/12 to-cyan-500/8";

  return (
    <button
      type="button"
      onClick={() => onSelect(persona)}
      className={`opus-persona-card ${selected ? "opus-persona-card--selected" : ""}`}
    >
      <div
        className={`absolute inset-0 rounded-[1.25rem] bg-gradient-to-br ${gradient} opacity-60`}
        aria-hidden
      />
      <div className="relative">
        <div
          className="mb-3 flex h-12 w-12 items-center justify-center rounded-full border border-[var(--panel-border)] bg-[color-mix(in_srgb,var(--background)_70%,transparent)] text-xl font-semibold text-[var(--gold)]"
        >
          {persona.avatar_url ? (
            <span role="img" aria-label={persona.name}>{persona.name.charAt(0)}</span>
          ) : (
            <MessageCircle className="h-5 w-5" />
          )}
        </div>
        <h3 className="text-lg font-semibold">{persona.name}</h3>
        {persona.language && (
          <span className="mt-1 inline-block rounded-full border border-[var(--panel-border)] px-2 py-0.5 text-xs capitalize text-[var(--muted-fg)]">
            {persona.language}
          </span>
        )}
        <p className="mt-2 text-sm leading-relaxed text-[var(--muted-fg)]">{persona.description}</p>
      </div>
    </button>
  );
}
