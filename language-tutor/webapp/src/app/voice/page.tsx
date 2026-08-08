import Script from "next/script";
import VoiceTeacher from "@/components/VoiceTeacher";

export const metadata = {
  title: "Opus Studio — voice lessons",
  description: "3D voice lessons with Opus Neural — Opus 5 Concierge",
};

export default function VoicePage() {
  return (
    <>
      <Script src="https://telegram.org/js/telegram-web-app.js" strategy="beforeInteractive" />
      <VoiceTeacher />
    </>
  );
}
