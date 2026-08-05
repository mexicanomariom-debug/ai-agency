"use client";

interface VirtualTeacherAvatarProps {
  name: string;
  mouthOpen: number;
  isSpeaking: boolean;
  isListening: boolean;
}

export default function VirtualTeacherAvatar({
  name,
  mouthOpen,
  isSpeaking,
  isListening,
}: VirtualTeacherAvatarProps) {
  const mouthHeight = 4 + mouthOpen * 22;
  const mouthWidth = 28 + mouthOpen * 14;
  const glow = isSpeaking ? "drop-shadow(0 0 24px rgba(99,102,241,0.5))" : "none";

  return (
    <div className="flex flex-col items-center">
      <div
        className="relative transition-all duration-300"
        style={{ filter: glow }}
      >
        {/* Glow ring when speaking */}
        {isSpeaking && (
          <div className="absolute inset-0 animate-pulse rounded-full bg-indigo-500/20 blur-xl" />
        )}

        <svg
          viewBox="0 0 200 240"
          className="relative h-56 w-48"
          aria-label={`Учитель ${name}`}
        >
          {/* Hair */}
          <ellipse cx="100" cy="72" rx="62" ry="58" fill="#3d2b1f" />
          <ellipse cx="100" cy="80" rx="54" ry="48" fill="#4a3728" />

          {/* Face */}
          <ellipse cx="100" cy="105" rx="52" ry="58" fill="#f5d0b5" />

          {/* Ears */}
          <ellipse cx="48" cy="108" rx="10" ry="14" fill="#edb896" />
          <ellipse cx="152" cy="108" rx="10" ry="14" fill="#edb896" />

          {/* Eyes */}
          <ellipse cx="78" cy="100" rx="10" ry={isListening ? 12 : 8} fill="#fff" />
          <ellipse cx="122" cy="100" rx="10" ry={isListening ? 12 : 8} fill="#fff" />
          <circle cx="80" cy="102" r="5" fill="#2d1f14" />
          <circle cx="124" cy="102" r="5" fill="#2d1f14" />
          <circle cx="82" cy="100" r="1.5" fill="#fff" />
          <circle cx="126" cy="100" r="1.5" fill="#fff" />

          {/* Eyebrows */}
          <path d="M 66 88 Q 78 82 90 88" stroke="#3d2b1f" strokeWidth="3" fill="none" strokeLinecap="round" />
          <path d="M 110 88 Q 122 82 134 88" stroke="#3d2b1f" strokeWidth="3" fill="none" strokeLinecap="round" />

          {/* Nose */}
          <path d="M 100 108 Q 96 120 100 124 Q 104 120 100 108" fill="#e8b48a" />

          {/* Mouth — opens with audio */}
          <ellipse
            cx="100"
            cy="142"
            rx={mouthWidth / 2}
            ry={mouthHeight / 2}
            fill={mouthOpen > 0.15 ? "#c45c5c" : "none"}
            stroke="#b04040"
            strokeWidth="2"
          />
          {mouthOpen <= 0.15 && (
            <path
              d="M 82 142 Q 100 148 118 142"
              stroke="#b04040"
              strokeWidth="2.5"
              fill="none"
              strokeLinecap="round"
            />
          )}

          {/* Blazer / teacher outfit */}
          <path d="M 55 165 L 100 200 L 145 165 L 145 240 L 55 240 Z" fill="#4f46e5" />
          <path d="M 85 165 L 100 195 L 115 165" fill="#3730a3" />
          <ellipse cx="100" cy="178" rx="8" ry="10" fill="#fff" />
          <circle cx="100" cy="190" r="3" fill="#fbbf24" />
        </svg>
      </div>

      <p className="mt-2 text-lg font-semibold text-white">{name}</p>
      <p className="text-sm text-indigo-300">
        {isListening ? "Слушаю…" : isSpeaking ? "Говорю…" : "Ваш учитель"}
      </p>
    </div>
  );
}
