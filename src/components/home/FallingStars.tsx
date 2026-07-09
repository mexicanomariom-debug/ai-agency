type FallingStar = {
  id: string;
  left: string;
  delay: string;
  duration: string;
  drift: string;
  size: number;
  opacity: number;
};

type Meteor = {
  id: string;
  top: string;
  offset: string;
  delay: string;
  duration: string;
};

type SkyStar = {
  id: string;
  top: string;
  offset: string;
  size: number;
  delay: string;
  opacity: number;
};

function makeFallingStars(prefix: string, offsets: string[]): FallingStar[] {
  return offsets.map((left, i) => ({
    id: `${prefix}-f${i}`,
    left,
    delay: `${(i * 1.7) % 9}s`,
    duration: `${7 + (i % 5) * 1.4}s`,
    drift: `${(i % 2 === 0 ? 1 : -1) * (6 + (i % 4) * 3)}px`,
    size: i % 4 === 0 ? 2 : 1,
    opacity: 0.35 + (i % 3) * 0.2,
  }));
}

function makeSkyStars(prefix: string, positions: [string, string, number, number][]): SkyStar[] {
  return positions.map(([top, offset, size, opacity], i) => ({
    id: `${prefix}-s${i}`,
    top,
    offset,
    size,
    delay: `${(i * 0.9) % 5}s`,
    opacity,
  }));
}

const LEFT_FALLING = makeFallingStars("l", [
  "6%", "14%", "22%", "10%", "28%", "18%", "4%", "24%", "12%", "20%",
]);

const RIGHT_FALLING = makeFallingStars("r", [
  "8%", "16%", "24%", "12%", "30%", "20%", "6%", "26%", "14%", "22%",
]);

const LEFT_SKY = makeSkyStars("l", [
  ["8%", "12%", 2, 0.7],
  ["18%", "24%", 1, 0.45],
  ["28%", "8%", 1, 0.5],
  ["42%", "18%", 2, 0.65],
  ["55%", "26%", 1, 0.4],
  ["68%", "10%", 1, 0.55],
  ["78%", "20%", 2, 0.6],
  ["88%", "14%", 1, 0.35],
  ["32%", "28%", 1, 0.5],
  ["62%", "22%", 1, 0.45],
  ["48%", "6%", 2, 0.55],
  ["92%", "26%", 1, 0.4],
]);

const RIGHT_SKY = makeSkyStars("r", [
  ["10%", "14%", 2, 0.65],
  ["20%", "26%", 1, 0.5],
  ["30%", "10%", 1, 0.45],
  ["44%", "20%", 2, 0.7],
  ["58%", "28%", 1, 0.4],
  ["70%", "12%", 1, 0.55],
  ["80%", "22%", 2, 0.6],
  ["90%", "16%", 1, 0.35],
  ["36%", "30%", 1, 0.5],
  ["64%", "8%", 1, 0.45],
  ["50%", "24%", 2, 0.55],
  ["94%", "10%", 1, 0.4],
]);

const LEFT_METEORS: Meteor[] = [
  { id: "lm0", top: "0", offset: "10%", delay: "0s", duration: "14s" },
  { id: "lm1", top: "0", offset: "22%", delay: "3s", duration: "18s" },
  { id: "lm2", top: "0", offset: "6%", delay: "7s", duration: "16s" },
  { id: "lm3", top: "0", offset: "18%", delay: "11s", duration: "20s" },
];

const RIGHT_METEORS: Meteor[] = [
  { id: "rm0", top: "0", offset: "12%", delay: "1s", duration: "15s" },
  { id: "rm1", top: "0", offset: "24%", delay: "5s", duration: "17s" },
  { id: "rm2", top: "0", offset: "8%", delay: "9s", duration: "19s" },
  { id: "rm3", top: "0", offset: "20%", delay: "13s", duration: "16s" },
];

export default function FallingStars() {
  return (
    <div aria-hidden className="falling-stars pointer-events-none absolute inset-0 overflow-hidden">
      <div className="falling-stars-vignette falling-stars-vignette-left" />
      <div className="falling-stars-vignette falling-stars-vignette-right" />

      <div className="falling-stars-side falling-stars-side-left">
        {LEFT_SKY.map((star) => (
          <span
            key={star.id}
            className="sky-star"
            style={{
              top: star.top,
              left: star.offset,
              width: star.size,
              height: star.size,
              opacity: star.opacity,
              animationDelay: star.delay,
            }}
          />
        ))}
        {LEFT_FALLING.map((star) => (
          <span
            key={star.id}
            className="falling-star-particle"
            style={{
              left: star.left,
              width: star.size,
              height: star.size,
              animationDelay: star.delay,
              animationDuration: star.duration,
              ["--drift" as string]: star.drift,
              ["--particle-opacity" as string]: String(star.opacity),
            }}
          />
        ))}
        {LEFT_METEORS.map((meteor) => (
          <span
            key={meteor.id}
            className="meteor meteor-left"
            style={{
              top: meteor.top,
              left: meteor.offset,
              animationDelay: meteor.delay,
              animationDuration: meteor.duration,
            }}
          >
            <span className="meteor-head" />
            <span className="meteor-tail" />
          </span>
        ))}
      </div>

      <div className="falling-stars-side falling-stars-side-right">
        {RIGHT_SKY.map((star) => (
          <span
            key={star.id}
            className="sky-star"
            style={{
              top: star.top,
              right: star.offset,
              width: star.size,
              height: star.size,
              opacity: star.opacity,
              animationDelay: star.delay,
            }}
          />
        ))}
        {RIGHT_FALLING.map((star) => (
          <span
            key={star.id}
            className="falling-star-particle"
            style={{
              right: star.left,
              width: star.size,
              height: star.size,
              animationDelay: star.delay,
              animationDuration: star.duration,
              ["--drift" as string]: star.drift,
              ["--particle-opacity" as string]: String(star.opacity),
            }}
          />
        ))}
        {RIGHT_METEORS.map((meteor) => (
          <span
            key={meteor.id}
            className="meteor meteor-right"
            style={{
              top: meteor.top,
              right: meteor.offset,
              animationDelay: meteor.delay,
              animationDuration: meteor.duration,
            }}
          >
            <span className="meteor-head" />
            <span className="meteor-tail" />
          </span>
        ))}
      </div>
    </div>
  );
}
