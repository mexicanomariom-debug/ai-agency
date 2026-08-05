import Script from "next/script";
import TwaApp from "@/components/TwaApp";

export default function AppPage() {
  return (
    <>
      <Script src="https://telegram.org/js/telegram-web-app.js" strategy="beforeInteractive" />
      <TwaApp />
    </>
  );
}
