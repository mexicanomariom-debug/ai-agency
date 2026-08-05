import Script from "next/script";
import VoiceTeacher from "@/components/VoiceTeacher";

export const metadata = {
  title: "Учитель — голосовое общение",
  description: "AI-учитель с голосовым общением",
};

export default function VoicePage() {
  return (
    <>
      <Script src="https://telegram.org/js/telegram-web-app.js" strategy="beforeInteractive" />
      <VoiceTeacher />
    </>
  );
}
