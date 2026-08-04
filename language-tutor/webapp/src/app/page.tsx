import { Features, Footer, Header, Hero } from "@/components/Landing";

export default function HomePage() {
  return (
    <>
      <Header />
      <main>
        <Hero />
        <Features />
      </main>
      <Footer />
    </>
  );
}
