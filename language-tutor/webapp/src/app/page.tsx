import { Features, Footer, Header, Hero, Journey, ProductShowcase } from "@/components/Landing";

export default function HomePage() {
  return (
    <div className="opus-marketing">
      <Header />
      <main>
        <Hero />
        <ProductShowcase />
        <Journey />
        <Features />
      </main>
      <Footer />
    </div>
  );
}
