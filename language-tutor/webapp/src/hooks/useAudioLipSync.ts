"use client";

import { useEffect, useRef, useState } from "react";

export function useAudioLipSync(isPlaying: boolean, audioElement: HTMLAudioElement | null) {
  const [mouthOpen, setMouthOpen] = useState(0);
  const rafRef = useRef<number>(0);
  const ctxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);

  useEffect(() => {
    if (!isPlaying || !audioElement) {
      setMouthOpen(0);
      return;
    }

    const ctx = new AudioContext();
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 256;
    const source = ctx.createMediaElementSource(audioElement);
    source.connect(analyser);
    analyser.connect(ctx.destination);
    ctxRef.current = ctx;
    analyserRef.current = analyser;

    const data = new Uint8Array(analyser.frequencyBinCount);

    const tick = () => {
      analyser.getByteFrequencyData(data);
      const avg = data.reduce((a, b) => a + b, 0) / data.length;
      const level = Math.min(1, avg / 90);
      setMouthOpen(level);
      rafRef.current = requestAnimationFrame(tick);
    };
    tick();

    return () => {
      cancelAnimationFrame(rafRef.current);
      source.disconnect();
      analyser.disconnect();
      void ctx.close();
      ctxRef.current = null;
      analyserRef.current = null;
      setMouthOpen(0);
    };
  }, [isPlaying, audioElement]);

  return mouthOpen;
}
