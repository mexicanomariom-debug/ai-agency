import { Features, Footer, Header, Hero, Journey, ProductShowcase } from "@/components/Landing";
import LandingChildDemo from "@/components/LandingChildDemo";

export default function HomePage() {
  return (
    <div className="opus-marketing">
      <Header />
      <main>
        <Hero />
        <LandingChildDemo />
        <ProductShowcase />
        <Journey />
        <Features />
      </main>
      <Footer />
    </div>
  );
}
