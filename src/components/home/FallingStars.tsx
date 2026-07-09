"use client";

import { useEffect, useId, useState } from "react";

type ActiveStar = {
  id: string;
  top: string;
  direction: "ltr" | "rtl";
};

type Props = {
  slideIndex: number;
};

const STAR_TOPS = ["9%", "17%", "24%", "13%", "31%", "20%"];

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

function SkyDot({ gradientId }: { gradientId: string }) {
  return (
    <svg width="8" height="8" viewBox="0 0 8 8" aria-hidden className="sky-star__svg">
      <defs>
        <radialGradient id={gradientId} cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.9" />
          <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle cx="4" cy="4" r="3.5" fill={`url(#${gradientId})`} />
    </svg>
  );
}

const SKY_DOTS = [
  { id: "k1", top: "12%", left: "4%", delay: "0s" },
  { id: "k2", top: "38%", left: "8%", delay: "1.4s" },
  { id: "k3", top: "62%", left: "3%", delay: "2.8s" },
  { id: "k4", top: "18%", right: "5%", delay: "0.7s" },
  { id: "k5", top: "44%", right: "9%", delay: "2.1s" },
  { id: "k6", top: "72%", right: "4%", delay: "3.2s" },
] as const;

export default function FallingStars({ slideIndex }: Props) {
  const baseId = useId();
  const [activeStars, setActiveStars] = useState<ActiveStar[]>([]);

  useEffect(() => {
    const primary: ActiveStar = {
      id: `${slideIndex}-primary-${Date.now()}`,
      top: STAR_TOPS[slideIndex % STAR_TOPS.length],
      direction: slideIndex % 2 === 0 ? "ltr" : "rtl",
    };

    const stars = [primary];

    if (slideIndex % 2 === 0) {
      stars.push({
        id: `${slideIndex}-secondary-${Date.now()}`,
        top: STAR_TOPS[(slideIndex + 3) % STAR_TOPS.length],
        direction: slideIndex % 2 === 0 ? "rtl" : "ltr",
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
          }}
        >
          <SkyDot gradientId={`${baseId}-sky-${i}`} />
        </span>
      ))}

      {activeStars.map((star) => (
        <span
          key={star.id}
          className={`shooting-star shooting-star--${star.direction} shooting-star--once`}
          style={{ top: star.top }}
        >
          <StarHead gradientId={`${baseId}-burst-${star.id}`} />
          <span className="shooting-star__tail" />
        </span>
      ))}
    </div>
  );
}
