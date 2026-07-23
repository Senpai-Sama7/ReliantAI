"use client";

import type { ReactNode } from "react";
import type { SiteContent } from "@/types/SiteContent";
import type { TradeScene } from "@/lib/immersive";
import { TRADE_COPY } from "@/lib/trade-copy";
import ContactBar from "@/components/shared/ContactBar";
import MobileCallBar from "@/components/shared/MobileCallBar";
import CTASection from "@/components/shared/CTASection";
import CraftFAQ from "@/components/shared/CraftFAQ";
import ImmersiveMotionProvider from "@/components/immersive/ImmersiveMotionProvider";
import TradeCinematicHero from "@/components/immersive/TradeCinematicHero";
import TrustInstrumentPanel from "@/components/immersive/TrustInstrumentPanel";
import ServiceProcessReel from "@/components/immersive/ServiceProcessReel";
import ResponseRail from "@/components/immersive/ResponseRail";
import WorkmanshipScrollStory from "@/components/immersive/WorkmanshipScrollStory";
import CoverageRadiusMap from "@/components/immersive/CoverageRadiusMap";
import ReviewConstellation from "@/components/immersive/ReviewConstellation";
import ScrollProgress from "@/components/immersive/ScrollProgress";

type CtaColor = "steel" | "copper" | "gold" | "ochre" | "moss" | "amber" | "orange" | "emerald" | "blue";

interface ImmersiveTemplateProps {
  content: SiteContent;
  scene: TradeScene;
  tradeAttr: string;
  light?: boolean;
  badge?: string;
  contactTagline?: string;
  ctaColor?: CtaColor;
  /** Server Component footer passed as children (never as a function prop). */
  children: ReactNode;
}

/**
 * Shared T2 cinematic composition for all trade templates.
 * Keeps NAP / FAQ / phone rails; swaps editorial core for immersive instruments.
 */
export default function ImmersiveTemplate({
  content,
  scene,
  tradeAttr,
  light = false,
  badge,
  contactTagline,
  ctaColor = "steel",
  children,
}: ImmersiveTemplateProps) {
  const copy = TRADE_COPY[content.site_config.trade] || TRADE_COPY.hvac;
  const shellTone = light
    ? "bg-[var(--trade-surface)] text-[var(--trade-ink)]"
    : "bg-[var(--trade-ink)] text-white";

  return (
    <ImmersiveMotionProvider>
      <div data-trade={tradeAttr} className={`template-shell immersive-shell ${shellTone}`}>
        <ScrollProgress />
        <ContactBar content={content} tagline={contactTagline} light={light} />
        <TradeCinematicHero content={content} scene={scene} light={light} badge={badge} />
        <TrustInstrumentPanel content={content} copy={copy} light={light} />
        <div id="services">
          <ServiceProcessReel content={content} copy={copy} light={light} />
        </div>
        <ResponseRail content={content} copy={copy} light={light} />
        <div id="about">
          <WorkmanshipScrollStory content={content} copy={copy} scene={scene} light={light} />
        </div>
        <CoverageRadiusMap content={content} light={light} />
        <div id="reviews">
          <ReviewConstellation content={content} copy={copy} light={light} />
        </div>
        <CTASection content={content} color={ctaColor} variant="estimate" />
        <div id="faq">
          <CraftFAQ content={content} copy={copy} light={light} />
        </div>
        {children}
        <MobileCallBar content={content} />
      </div>
    </ImmersiveMotionProvider>
  );
}
