"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Smooth jaw openness 0..1 from live audio (speech-band weighted).
 */
export function useAudioLipSync(isPlaying: boolean, audioElement: HTMLAudioElement | null) {
  const [mouthOpen, setMouthOpen] = useState(0);
  const rafRef = useRef<number>(0);
  const smoothRef = useRef(0);

  useEffect(() => {
    if (!isPlaying || !audioElement) {
      smoothRef.current = 0;
      setMouthOpen(0);
      return;
    }

    let cancelled = false;
    const ctx = new AudioContext();
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 512;
    analyser.smoothingTimeConstant = 0.55;
    const source = ctx.createMediaElementSource(audioElement);
    source.connect(analyser);
    analyser.connect(ctx.destination);

    const freq = new Uint8Array(analyser.frequencyBinCount);
    const sampleRate = ctx.sampleRate;
    const binHz = sampleRate / analyser.fftSize;

    // Speech energy ~300Hz–3kHz
    const lo = Math.floor(300 / binHz);
    const hi = Math.min(freq.length - 1, Math.ceil(3000 / binHz));

    const tick = () => {
      if (cancelled) return;
      analyser.getByteFrequencyData(freq);
      let sum = 0;
      let n = 0;
      for (let i = lo; i <= hi; i++) {
        sum += freq[i];
        n++;
      }
      const avg = n ? sum / n : 0;
      // Nonlinear map — quiet speech still moves lips a bit
      const raw = Math.min(1, Math.pow(avg / 70, 1.15));
      // Attack fast / release slower for natural jaw
      const prev = smoothRef.current;
      const next = raw > prev ? prev * 0.35 + raw * 0.65 : prev * 0.78 + raw * 0.22;
      smoothRef.current = next;
      setMouthOpen(next);
      rafRef.current = requestAnimationFrame(tick);
    };

    void ctx.resume().then(() => {
      if (!cancelled) tick();
    });

    return () => {
      cancelled = true;
      cancelAnimationFrame(rafRef.current);
      try {
        source.disconnect();
        analyser.disconnect();
      } catch {
        /* already closed */
      }
      void ctx.close();
      smoothRef.current = 0;
      setMouthOpen(0);
    };
  }, [isPlaying, audioElement]);

  return mouthOpen;
}
