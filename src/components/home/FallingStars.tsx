type ShootingStar = {
  id: string;
  top: string;
  delay: string;
  duration: string;
  direction: "ltr" | "rtl";
};

type SkyStar = {
  id: string;
  top: string;
  left?: string;
  right?: string;
  delay: string;
};

/* Few slow shooting stars that cross the full hero */
const SHOOTING_STARS: ShootingStar[] = [
  { id: "s1", top: "12%", delay: "0s", duration: "42s", direction: "ltr" },
  { id: "s2", top: "26%", delay: "14s", duration: "48s", direction: "rtl" },
  { id: "s3", top: "18%", delay: "28s", duration: "44s", direction: "ltr" },
  { id: "s4", top: "34%", delay: "21s", duration: "50s", direction: "rtl" },
];

/* Subtle fixed stars on the edges only */
const SKY_STARS: SkyStar[] = [
  { id: "k1", top: "12%", left: "4%", delay: "0s" },
  { id: "k2", top: "38%", left: "8%", delay: "1.4s" },
  { id: "k3", top: "62%", left: "3%", delay: "2.8s" },
  { id: "k4", top: "18%", right: "5%", delay: "0.7s" },
  { id: "k5", top: "44%", right: "9%", delay: "2.1s" },
  { id: "k6", top: "72%", right: "4%", delay: "3.2s" },
];

export default function FallingStars() {
  return (
    <div aria-hidden className="falling-stars pointer-events-none absolute inset-0 overflow-hidden">
      <div className="falling-stars-vignette falling-stars-vignette-left" />
      <div className="falling-stars-vignette falling-stars-vignette-right" />

      {SKY_STARS.map((star) => (
        <span
          key={star.id}
          className="sky-star"
          style={{
            top: star.top,
            left: star.left,
            right: star.right,
            animationDelay: star.delay,
          }}
        />
      ))}

      {SHOOTING_STARS.map((star) => (
        <span
          key={star.id}
          className={`shooting-star shooting-star--${star.direction}`}
          style={{
            top: star.top,
            animationDelay: star.delay,
            animationDuration: star.duration,
          }}
        >
          <span className="shooting-star__head" />
          <span className="shooting-star__tail" />
        </span>
      ))}
    </div>
  );
}
