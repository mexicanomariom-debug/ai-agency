type ShootingStar = {
  id: string;
  top: string;
  offset: string;
  delay: string;
  duration: string;
  opacity: number;
};

type TwinkleStar = {
  id: string;
  top: string;
  offset: string;
  size: number;
  delay: string;
};

const LEFT_SHOOTING: ShootingStar[] = [
  { id: "ls0", top: "4%", offset: "8%", delay: "0s", duration: "3.2s", opacity: 0.9 },
  { id: "ls1", top: "12%", offset: "18%", delay: "1.4s", duration: "2.8s", opacity: 0.7 },
  { id: "ls2", top: "22%", offset: "6%", delay: "2.8s", duration: "3.6s", opacity: 0.85 },
  { id: "ls3", top: "8%", offset: "24%", delay: "4.2s", duration: "2.5s", opacity: 0.6 },
  { id: "ls4", top: "32%", offset: "14%", delay: "5.6s", duration: "3.1s", opacity: 0.75 },
  { id: "ls5", top: "18%", offset: "28%", delay: "7s", duration: "2.9s", opacity: 0.8 },
  { id: "ls6", top: "2%", offset: "12%", delay: "8.5s", duration: "3.4s", opacity: 0.65 },
  { id: "ls7", top: "28%", offset: "22%", delay: "10s", duration: "2.7s", opacity: 0.7 },
];

const RIGHT_SHOOTING: ShootingStar[] = [
  { id: "rs0", top: "6%", offset: "10%", delay: "0.6s", duration: "3s", opacity: 0.85 },
  { id: "rs1", top: "14%", offset: "20%", delay: "2s", duration: "2.6s", opacity: 0.7 },
  { id: "rs2", top: "24%", offset: "8%", delay: "3.4s", duration: "3.3s", opacity: 0.9 },
  { id: "rs3", top: "10%", offset: "26%", delay: "4.8s", duration: "2.4s", opacity: 0.65 },
  { id: "rs4", top: "30%", offset: "16%", delay: "6.2s", duration: "3.2s", opacity: 0.75 },
  { id: "rs5", top: "20%", offset: "30%", delay: "7.8s", duration: "2.8s", opacity: 0.8 },
  { id: "rs6", top: "4%", offset: "14%", delay: "9.2s", duration: "3.5s", opacity: 0.6 },
  { id: "rs7", top: "26%", offset: "24%", delay: "10.6s", duration: "2.9s", opacity: 0.72 },
];

const LEFT_TWINKLE: TwinkleStar[] = [
  { id: "lt0", top: "15%", offset: "10%", size: 2, delay: "0s" },
  { id: "lt1", top: "35%", offset: "20%", size: 1, delay: "1.2s" },
  { id: "lt2", top: "55%", offset: "8%", size: 2, delay: "2.4s" },
  { id: "lt3", top: "70%", offset: "18%", size: 1, delay: "0.8s" },
  { id: "lt4", top: "45%", offset: "26%", size: 1, delay: "3.1s" },
  { id: "lt5", top: "82%", offset: "12%", size: 2, delay: "1.8s" },
];

const RIGHT_TWINKLE: TwinkleStar[] = [
  { id: "rt0", top: "18%", offset: "12%", size: 2, delay: "0.4s" },
  { id: "rt1", top: "38%", offset: "22%", size: 1, delay: "1.6s" },
  { id: "rt2", top: "58%", offset: "10%", size: 2, delay: "2.8s" },
  { id: "rt3", top: "72%", offset: "20%", size: 1, delay: "1s" },
  { id: "rt4", top: "48%", offset: "28%", size: 1, delay: "3.3s" },
  { id: "rt5", top: "85%", offset: "14%", size: 2, delay: "2s" },
];

function ShootingStarItem({
  star,
  side,
}: {
  star: ShootingStar;
  side: "left" | "right";
}) {
  return (
    <span
      className={`shooting-star shooting-star-${side}`}
      style={{
        top: star.top,
        [side === "left" ? "left" : "right"]: star.offset,
        animationDelay: star.delay,
        animationDuration: star.duration,
        opacity: star.opacity,
      }}
    />
  );
}

function TwinkleStarItem({
  star,
  side,
}: {
  star: TwinkleStar;
  side: "left" | "right";
}) {
  return (
    <span
      className="twinkle-star"
      style={{
        top: star.top,
        [side === "left" ? "left" : "right"]: star.offset,
        width: star.size,
        height: star.size,
        animationDelay: star.delay,
      }}
    />
  );
}

export default function FallingStars() {
  return (
    <div aria-hidden className="falling-stars pointer-events-none absolute inset-0 overflow-hidden">
      <div className="absolute inset-y-0 left-0 w-[32%] bg-gradient-to-r from-black/55 via-black/20 to-transparent" />
      <div className="absolute inset-y-0 right-0 w-[32%] bg-gradient-to-l from-black/55 via-black/20 to-transparent" />

      <div className="absolute inset-y-0 left-0 w-[30%]">
        {LEFT_SHOOTING.map((star) => (
          <ShootingStarItem key={star.id} star={star} side="left" />
        ))}
        {LEFT_TWINKLE.map((star) => (
          <TwinkleStarItem key={star.id} star={star} side="left" />
        ))}
      </div>

      <div className="absolute inset-y-0 right-0 w-[30%]">
        {RIGHT_SHOOTING.map((star) => (
          <ShootingStarItem key={star.id} star={star} side="right" />
        ))}
        {RIGHT_TWINKLE.map((star) => (
          <TwinkleStarItem key={star.id} star={star} side="right" />
        ))}
      </div>
    </div>
  );
}
