import Hero from "@/components/Hero";
import NeedsSection from "@/components/NeedsSection";

export default function Home() {
  return (
    <main className="min-h-screen overflow-x-hidden bg-white text-gray-900">
      <Hero />
      <NeedsSection />
    </main>
  );
}
