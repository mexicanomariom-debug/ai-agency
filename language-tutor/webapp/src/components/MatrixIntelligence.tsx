"use client";

import { useEffect, useRef } from "react";

type Status = "idle" | "recording" | "processing" | "speaking";

const MATRIX_CHARS = "ｱｲｳｴｵｶｷｸｹｺ0123456789ABCDEFｻｼｽｾｿﾀﾁﾂﾃﾄ";

type Props = {
  status: Status;
};

export default function MatrixIntelligence({ status }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const statusRef = useRef(status);
  statusRef.current = status;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let raf = 0;
    let w = 0;
    let h = 0;
    const fontSize = 14;
    let columns = 0;
    const drops: number[] = [];
    let pulse = 0;

    const resize = () => {
      const parent = canvas.parentElement;
      if (!parent) return;
      w = parent.clientWidth;
      h = parent.clientHeight;
      canvas.width = w;
      canvas.height = h;
      columns = Math.floor(w / fontSize);
      drops.length = columns;
      for (let i = 0; i < columns; i++) {
        drops[i] = Math.random() * -h;
      }
    };

    const drawCore = (time: number) => {
      const cx = w / 2;
      const cy = h * 0.42;
      const st = statusRef.current;
      const speed = st === "speaking" ? 0.012 : st === "recording" ? 0.009 : 0.005;
      pulse = (pulse + speed) % (Math.PI * 2);
      const baseR = Math.min(w, h) * 0.11;
      const breathe = 1 + Math.sin(pulse) * (st === "idle" ? 0.04 : 0.12);

      for (let ring = 3; ring >= 0; ring--) {
        const r = baseR * breathe + ring * 22;
        const alpha =
          st === "processing"
            ? 0.08 + ring * 0.04
            : st === "speaking"
              ? 0.15 + ring * 0.06
              : 0.06 + ring * 0.05;
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(0, 255, 136, ${alpha})`;
        ctx.lineWidth = st === "recording" ? 2 : 1;
        ctx.stroke();
      }

      const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, baseR * 1.2);
      grad.addColorStop(0, "rgba(0, 255, 180, 0.35)");
      grad.addColorStop(0.45, "rgba(0, 200, 120, 0.12)");
      grad.addColorStop(1, "rgba(0, 0, 0, 0)");
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(cx, cy, baseR * 1.3 * breathe, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle =
        st === "speaking" ? "rgba(0, 255, 200, 0.95)" : "rgba(0, 255, 136, 0.85)";
      ctx.font = `600 ${Math.max(11, fontSize - 1)}px "Share Tech Mono", monospace`;
      ctx.textAlign = "center";
      ctx.fillText("OPUS", cx, cy - 6);
      ctx.font = `400 ${fontSize - 2}px "Share Tech Mono", monospace`;
      ctx.fillStyle = "rgba(0, 255, 136, 0.7)";
      ctx.fillText("NEURAL CORE", cx, cy + 12);

      if (st === "processing") {
        const scanY = cy + Math.sin(time * 0.004) * (baseR * 0.8);
        ctx.strokeStyle = "rgba(0, 255, 200, 0.35)";
        ctx.beginPath();
        ctx.moveTo(cx - baseR * 1.4, scanY);
        ctx.lineTo(cx + baseR * 1.4, scanY);
        ctx.stroke();
      }
    };

    const draw = (time: number) => {
      ctx.fillStyle = "rgba(0, 4, 0, 0.12)";
      ctx.fillRect(0, 0, w, h);

      ctx.font = `${fontSize}px "Share Tech Mono", monospace`;
      const st = statusRef.current;
      const trailBright = st === "speaking" ? 0.9 : st === "recording" ? 0.75 : 0.55;

      for (let i = 0; i < columns; i++) {
        const x = i * fontSize;
        const y = drops[i] * fontSize;
        const ch = MATRIX_CHARS[Math.floor(Math.random() * MATRIX_CHARS.length)];
        ctx.fillStyle = `rgba(0, 255, 120, ${0.03 + (i % 5) * 0.01})`;
        ctx.fillText(ch, x, y);
        if (y > 0 && Math.random() > 0.975) {
          ctx.fillStyle = `rgba(180, 255, 220, ${trailBright})`;
          ctx.fillText(ch, x, y);
        }
        drops[i] += st === "speaking" ? 1.8 : st === "recording" ? 1.4 : 0.85;
        if (drops[i] * fontSize > h && Math.random() > 0.975) {
          drops[i] = 0;
        }
      }

      drawCore(time);
      raf = requestAnimationFrame(draw);
    };

    resize();
    window.addEventListener("resize", resize);
    raf = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="matrix-canvas"
      aria-hidden
    />
  );
}
