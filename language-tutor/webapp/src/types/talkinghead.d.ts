declare module "@met4citizen/talkinghead/modules/talkinghead.mjs" {
  export class TalkingHead {
    constructor(node: HTMLElement, opt?: Record<string, unknown>);
    lipsync: Record<string, unknown>;
    audioCtx: AudioContext;
    opt: Record<string, unknown>;
    showAvatar(avatar: Record<string, unknown>, onprogress?: (ev: ProgressEvent) => void): Promise<void>;
    setView(view: string, opt?: Record<string, number>): void;
    setMood(mood: string): void;
    speakAudio(audio: Record<string, unknown>, opt?: Record<string, unknown>): void;
    stopSpeaking(): void;
    start(): void;
    stop(): void;
    playGesture(name: string, dur?: number): void;
  }
}

declare module "@met4citizen/talkinghead/modules/lipsync-en.mjs" {
  export class LipsyncEn {
    preProcessText(s: string): string;
    wordsToVisemes(word: string): { visemes: string[]; times: number[]; durations: number[] };
  }
}

declare module "@met4citizen/talkinghead/modules/lipsync-de.mjs" {
  export class LipsyncDe {
    preProcessText(s: string): string;
    wordsToVisemes(word: string): { visemes: string[]; times: number[]; durations: number[] };
  }
}
