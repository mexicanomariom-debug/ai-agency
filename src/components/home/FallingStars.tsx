"use client";

import { useEffect, useId, useState } from "react";

type ActiveStar = {
  id: string;
  top: string;
  direction: "ltr" | "rtl";
  duration: number;
};

type Props = {
  slideIndex: number;
};

const STAR_TOPS = ["9%", "17%", "24%", "13%", "31%", "20%"];
const STAR_DURATIONS = [2.35, 2.7, 3.05, 3.35, 3.6] as const;

function StarHead({ gradientId }: { gradientId: string }) {
  return (
    <svg
      className="shooting-star__head"
      width="12"
      height="12"
      viewBox="0 0 12 12"
      aria-hidden
    >
      <defs>
        <radialGradient id={gradientId} cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="1" />
          <stop offset="30%" stopColor="#f8fafc" stopOpacity="0.95" />
          <stop offset="55%" stopColor="#e0e7ff" stopOpacity="0.35" />
          <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle cx="6" cy="6" r="5" fill={`url(#${gradientId})`} />
    </svg>
  );
}

function SkyDot({
  gradientId,
  size,
}: {
  gradientId: string;
  size: 1 | 2;
}) {
  const dim = size === 1 ? 4 : 5;
  const r = size === 1 ? 1.4 : 1.8;
  const c = dim / 2;

  return (
    <svg
      width={dim}
      height={dim}
      viewBox={`0 0 ${dim} ${dim}`}
      aria-hidden
      className="sky-star__svg"
    >
      <defs>
        <radialGradient id={gradientId} cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.95" />
          <stop offset="65%" stopColor="#ffffff" stopOpacity="0.15" />
          <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle cx={c} cy={c} r={r} fill={`url(#${gradientId})`} />
    </svg>
  );
}

const SKY_DOTS = [
  { id: "k1", top: "8%", left: "3%", delay: "0s", duration: "3.1s", size: 1 as const },
  { id: "k2", top: "16%", left: "7%", delay: "0.4s", duration: "4.6s", size: 2 as const },
  { id: "k3", top: "24%", left: "2%", delay: "1.1s", duration: "2.8s", size: 1 as const },
  { id: "k4", top: "34%", left: "9%", delay: "0.7s", duration: "5.2s", size: 1 as const },
  { id: "k5", top: "44%", left: "4%", delay: "1.8s", duration: "3.7s", size: 2 as const },
  { id: "k6", top: "54%", left: "11%", delay: "0.2s", duration: "4.1s", size: 1 as const },
  { id: "k7", top: "64%", left: "5%", delay: "2.3s", duration: "3.4s", size: 1 as const },
  { id: "k8", top: "74%", left: "8%", delay: "1.5s", duration: "5.8s", size: 1 as const },
  { id: "k9", top: "84%", left: "3%", delay: "0.9s", duration: "2.5s", size: 2 as const },
  { id: "k10", top: "28%", left: "13%", delay: "2.8s", duration: "4.4s", size: 1 as const },
  { id: "k11", top: "10%", right: "4%", delay: "0.3s", duration: "3.9s", size: 1 as const },
  { id: "k12", top: "18%", right: "8%", delay: "1.2s", duration: "2.7s", size: 2 as const },
  { id: "k13", top: "26%", right: "2%", delay: "0.6s", duration: "5.1s", size: 1 as const },
  { id: "k14", top: "36%", right: "10%", delay: "1.9s", duration: "3.3s", size: 1 as const },
  { id: "k15", top: "46%", right: "5%", delay: "0.1s", duration: "4.7s", size: 1 as const },
  { id: "k16", top: "56%", right: "12%", delay: "2.1s", duration: "3.6s", size: 2 as const },
  { id: "k17", top: "66%", right: "6%", delay: "1.4s", duration: "5.5s", size: 1 as const },
  { id: "k18", top: "76%", right: "9%", delay: "0.8s", duration: "2.9s", size: 1 as const },
  { id: "k19", top: "86%", right: "3%", delay: "2.5s", duration: "4.2s", size: 1 as const },
  { id: "k20", top: "32%", right: "14%", delay: "1.7s", duration: "3.8s", size: 1 as const },
] as const;

export default function FallingStars({ slideIndex }: Props) {
  const baseId = useId();
  const [activeStars, setActiveStars] = useState<ActiveStar[]>([]);

  useEffect(() => {
    const primary: ActiveStar = {
      id: `${slideIndex}-primary-${Date.now()}`,
      top: STAR_TOPS[slideIndex % STAR_TOPS.length],
      direction: slideIndex % 2 === 0 ? "ltr" : "rtl",
      duration: STAR_DURATIONS[slideIndex % STAR_DURATIONS.length],
    };

    const stars = [primary];

    if (slideIndex % 2 === 0) {
      stars.push({
        id: `${slideIndex}-secondary-${Date.now()}`,
        top: STAR_TOPS[(slideIndex + 3) % STAR_TOPS.length],
        direction: "rtl",
        duration: STAR_DURATIONS[(slideIndex + 2) % STAR_DURATIONS.length],
      });
    }

    setActiveStars(stars);
  }, [slideIndex]);

  return (
    <div aria-hidden className="falling-stars pointer-events-none absolute inset-0 overflow-hidden">
      <div className="falling-stars-vignette falling-stars-vignette-left" />
      <div className="falling-stars-vignette falling-stars-vignette-right" />

      {SKY_DOTS.map((dot, i) => (
        <span
          key={dot.id}
          className="sky-star"
          style={{
            top: dot.top,
            left: "left" in dot ? dot.left : undefined,
            right: "right" in dot ? dot.right : undefined,
            animationDelay: dot.delay,
            animationDuration: dot.duration,
          }}
        >
          <SkyDot gradientId={`${baseId}-sky-${i}`} size={dot.size} />
        </span>
      ))}

      {activeStars.map((star) => (
        <span
          key={star.id}
          className={`shooting-star shooting-star--${star.direction} shooting-star--once`}
          style={{ top: star.top, animationDuration: `${star.duration}s` }}
        >
          <StarHead gradientId={`${baseId}-burst-${star.id}`} />
          <span className="shooting-star__tail" />
        </span>
      ))}
    </div>
  );
}
