"use client";

import { useEffect, useState } from "react";

interface VirtualTeacherAvatarProps {
  name: string;
  mouthOpen: number;
  isSpeaking: boolean;
  isListening: boolean;
}

/** Viseme-like mouth path from 0 (closed smile) to 1 (wide open). */
function mouthPath(open: number): string {
  const t = Math.max(0, Math.min(1, open));
  if (t < 0.08) {
    return "M 84 148 Q 100 154 116 148";
  }
  const top = 146 - t * 4;
  const bottom = 148 + t * 22;
  const left = 100 - (12 + t * 16);
  const right = 100 + (12 + t * 16);
  const mid = 100;
  return `M ${left} ${top}
    Q ${mid} ${top - 2} ${right} ${top}
    Q ${right + 2} ${(top + bottom) / 2} ${right} ${bottom}
    Q ${mid} ${bottom + 4} ${left} ${bottom}
    Q ${left - 2} ${(top + bottom) / 2} ${left} ${top} Z`;
}

export default function VirtualTeacherAvatar({
  name,
  mouthOpen,
  isSpeaking,
  isListening,
}: VirtualTeacherAvatarProps) {
  const [blink, setBlink] = useState(false);
  const open = Math.max(0, Math.min(1, mouthOpen));
  const teethVisible = open > 0.22;
  const browLift = isListening ? -3 : isSpeaking ? -1 : 0;

  useEffect(() => {
    let timeout: ReturnType<typeof setTimeout>;
    const schedule = () => {
      timeout = setTimeout(() => {
        setBlink(true);
        setTimeout(() => setBlink(false), 120);
        schedule();
      }, 2800 + Math.random() * 3200);
    };
    schedule();
    return () => clearTimeout(timeout);
  }, []);

  return (
    <div className="flex flex-col items-center">
      <div
        className={`avatar-stage relative ${isSpeaking ? "avatar-speaking" : ""} ${
          isListening ? "avatar-listening" : "avatar-idle"
        }`}
      >
        <div className="avatar-halo" aria-hidden />
        <svg
          viewBox="0 0 240 300"
          className="avatar-svg relative h-64 w-52 drop-shadow-2xl"
          aria-label={`Учитель ${name}`}
        >
          <defs>
            <linearGradient id="skin" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#e8b896" />
              <stop offset="45%" stopColor="#d4a07a" />
              <stop offset="100%" stopColor="#c48962" />
            </linearGradient>
            <linearGradient id="skinShade" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#00000000" />
              <stop offset="100%" stopColor="#00000033" />
            </linearGradient>
            <linearGradient id="hair" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#1a1410" />
              <stop offset="100%" stopColor="#0a0806" />
            </linearGradient>
            <linearGradient id="beard" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#1c1612" />
              <stop offset="100%" stopColor="#0d0a08" />
            </linearGradient>
            <linearGradient id="hoodie" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#2a2a2e" />
              <stop offset="100%" stopColor="#121214" />
            </linearGradient>
            <linearGradient id="gold" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#c9a227" />
              <stop offset="50%" stopColor="#f0d56a" />
              <stop offset="100%" stopColor="#a8841a" />
            </linearGradient>
            <radialGradient id="cheek" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#d4785a55" />
              <stop offset="100%" stopColor="#d4785a00" />
            </radialGradient>
            <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="1.2" />
            </filter>
          </defs>

          {/* Shoulders / athletic hoodie */}
          <path
            d="M 48 210 C 40 230 36 260 34 300 L 206 300 C 204 260 200 230 192 210
               C 170 222 150 228 120 230 C 90 228 70 222 48 210 Z"
            fill="url(#hoodie)"
          />
          <path
            d="M 95 218 L 120 248 L 145 218"
            fill="none"
            stroke="url(#gold)"
            strokeWidth="2.5"
            strokeLinecap="round"
          />
          <path d="M 100 222 L 120 242 L 140 222" fill="#1a1a1c" opacity="0.85" />

          {/* Neck */}
          <path d="M 100 178 L 90 210 L 150 210 L 140 178 Z" fill="url(#skin)" />
          <path d="M 100 178 L 90 210 L 150 210 L 140 178 Z" fill="url(#skinShade)" />

          {/* Ears */}
          <ellipse cx="62" cy="128" rx="11" ry="16" fill="#c99574" />
          <ellipse cx="178" cy="128" rx="11" ry="16" fill="#c99574" />
          <ellipse cx="62" cy="128" rx="6" ry="10" fill="#b87d5c" opacity="0.7" />
          <ellipse cx="178" cy="128" rx="6" ry="10" fill="#b87d5c" opacity="0.7" />

          {/* Head */}
          <ellipse cx="120" cy="118" rx="58" ry="68" fill="url(#skin)" />
          <ellipse cx="120" cy="118" rx="58" ry="68" fill="url(#skinShade)" />

          {/* Hair — short fade, textured top */}
          <ellipse cx="120" cy="72" rx="56" ry="42" fill="url(#hair)" />
          <path
            d="M 66 95 C 62 70 78 48 120 46 C 162 48 178 70 174 95
               C 168 78 150 68 120 66 C 90 68 72 78 66 95 Z"
            fill="#0f0c0a"
          />
          {/* Fade sides */}
          <path d="M 64 100 C 58 118 60 140 68 155 L 72 140 C 68 120 68 108 64 100 Z" fill="#1a1410" />
          <path d="M 176 100 C 182 118 180 140 172 155 L 168 140 C 172 120 172 108 176 100 Z" fill="#1a1410" />
          {/* Hair texture strokes */}
          <path d="M 95 52 Q 100 62 98 72" stroke="#2a221c" strokeWidth="2" fill="none" opacity="0.5" />
          <path d="M 120 48 Q 118 60 122 74" stroke="#2a221c" strokeWidth="2" fill="none" opacity="0.45" />
          <path d="M 145 54 Q 142 64 146 76" stroke="#2a221c" strokeWidth="2" fill="none" opacity="0.5" />

          {/* Beard / stubble silhouette */}
          <path
            d="M 72 130 C 70 160 85 188 120 196 C 155 188 170 160 168 130
               C 158 148 140 162 120 164 C 100 162 82 148 72 130 Z"
            fill="url(#beard)"
            opacity="0.92"
          />
          <path
            d="M 88 138 C 92 158 104 170 120 172 C 136 170 148 158 152 138"
            fill="none"
            stroke="#2c241e"
            strokeWidth="8"
            opacity="0.35"
            filter="url(#soft)"
          />

          {/* Cheek warmth */}
          <ellipse cx="82" cy="138" rx="14" ry="10" fill="url(#cheek)" />
          <ellipse cx="158" cy="138" rx="14" ry="10" fill="url(#cheek)" />

          {/* Brows — thick, intense */}
          <path
            d={`M 78 ${96 + browLift} Q 92 ${88 + browLift} 106 ${94 + browLift}`}
            stroke="#1a1410"
            strokeWidth="4.5"
            fill="none"
            strokeLinecap="round"
          />
          <path
            d={`M 134 ${94 + browLift} Q 148 ${88 + browLift} 162 ${96 + browLift}`}
            stroke="#1a1410"
            strokeWidth="4.5"
            fill="none"
            strokeLinecap="round"
          />

          {/* Eyes */}
          <g className={blink ? "avatar-eyes-closed" : ""}>
            <ellipse cx="94" cy="112" rx="11" ry={isListening ? 9 : 7.5} fill="#f7f2ea" />
            <ellipse cx="146" cy="112" rx="11" ry={isListening ? 9 : 7.5} fill="#f7f2ea" />
            <ellipse cx="95" cy="113" rx="5.5" ry="5.5" fill="#2c1a10" />
            <ellipse cx="147" cy="113" rx="5.5" ry="5.5" fill="#2c1a10" />
            <circle cx="97" cy="111" r="1.8" fill="#fff" />
            <circle cx="149" cy="111" r="1.8" fill="#fff" />
          </g>
          {blink && (
            <>
              <path d="M 84 112 Q 94 116 104 112" stroke="#1a1410" strokeWidth="2.5" fill="none" />
              <path d="M 136 112 Q 146 116 156 112" stroke="#1a1410" strokeWidth="2.5" fill="none" />
            </>
          )}

          {/* Nose */}
          <path
            d="M 120 118 L 114 138 Q 120 142 126 138 Z"
            fill="#c48962"
            opacity="0.85"
          />
          <path d="M 116 138 Q 120 141 124 138" stroke="#a86f4e" strokeWidth="1.5" fill="none" />

          {/* Mustache */}
          <path
            d="M 100 142 Q 120 148 140 142"
            stroke="#15110e"
            strokeWidth="5"
            fill="none"
            strokeLinecap="round"
            opacity="0.9"
          />

          {/* Mouth + lip sync */}
          <path
            d={mouthPath(open)}
            fill={open > 0.08 ? "#5c1f24" : "none"}
            stroke="#6b3030"
            strokeWidth={open > 0.08 ? 1.5 : 2.8}
            strokeLinecap="round"
            className="avatar-mouth"
          />
          {teethVisible && (
            <rect
              x={100 - (8 + open * 10)}
              y={146 - open * 2}
              width={16 + open * 20}
              height={3 + open * 4}
              rx="1.5"
              fill="#f3ebe3"
              opacity="0.95"
            />
          )}
          {open > 0.45 && (
            <ellipse
              cx="120"
              cy={158 + open * 6}
              rx={4 + open * 4}
              ry={2 + open * 3}
              fill="#3a1216"
            />
          )}

          {/* Gold chain hint */}
          <path
            d="M 105 208 Q 120 218 135 208"
            stroke="url(#gold)"
            strokeWidth="2"
            fill="none"
            opacity="0.85"
          />
          <circle cx="120" cy="214" r="3" fill="url(#gold)" />
        </svg>
      </div>

      <p className="mt-3 text-xl font-semibold tracking-wide text-white">{name}</p>
      <p className="text-sm text-amber-400/90">
        {isListening ? "Слушаю…" : isSpeaking ? "Говорю…" : "Ваш учитель · чемпионский вайб"}
      </p>
    </div>
  );
}
