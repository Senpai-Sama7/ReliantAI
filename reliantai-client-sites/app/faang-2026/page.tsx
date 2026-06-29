import GlassNav from "@/components/faang-2026/GlassNav";
import HeroSection from "@/components/faang-2026/HeroSection";
import BentoGrid from "@/components/faang-2026/BentoGrid";
import ArchivalIndex from "@/components/faang-2026/ArchivalIndex";
import MotionNarrative from "@/components/faang-2026/MotionNarrative";
import MetricsStrip from "@/components/faang-2026/MetricsStrip";
import Footer from "@/components/faang-2026/Footer";

export default function Faang2026Page() {
  return (
    <>
      <div className="faang-aurora" aria-hidden="true" />
      <GlassNav />
      <main className="relative z-10">
        <HeroSection />
        <BentoGrid />
        <ArchivalIndex />
        <MotionNarrative />
        <MetricsStrip />
      </main>
      <Footer />
    </>
  );
}
