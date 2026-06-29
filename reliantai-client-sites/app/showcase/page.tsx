import type { Metadata } from "next";
import ShowcaseClient from "./showcase-client";

export const metadata: Metadata = {
  title: "Showcase — AI-Generated Websites for Every Trade",
  description:
    "Browse AI-generated websites for HVAC, plumbing, electrical, roofing, painting, and landscaping businesses. Each template is SEO-optimized, mobile-ready, and designed to convert. See your free preview instantly.",
  keywords: [
    "AI website generator showcase", "HVAC website template", "plumbing website design",
    "electrical contractor website", "roofing website builder", "painting company website",
    "landscaping website template", "home service website examples",
    "AI web design examples", "contractor website templates", "local business SEO",
  ],
  alternates: {
    canonical: "https://reliantai.org/showcase",
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    siteName: "ReliantAI",
    title: "Showcase — AI-Generated Websites for Every Trade",
    description:
      "Browse AI-generated websites for HVAC, plumbing, electrical, roofing, painting, and landscaping. Free preview instantly.",
    url: "https://reliantai.org/showcase",
    images: [
      {
        url: "https://reliantai.org/og/showcase.png",
        width: 1200,
        height: 630,
        alt: "ReliantAI Showcase — AI-Generated Websites for Home Service Businesses",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Showcase — AI-Generated Websites for Every Trade",
    description:
      "Browse AI-generated websites for HVAC, plumbing, electrical, roofing, painting, and landscaping.",
    images: ["https://reliantai.org/og/showcase.png"],
  },
};

export default ShowcaseClient;