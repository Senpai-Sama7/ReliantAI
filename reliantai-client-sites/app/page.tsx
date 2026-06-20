import type { Metadata } from "next";
import { redirect } from "next/navigation";

export const metadata: Metadata = {
  title: "ReliantAI — AI-Powered Websites for Home Service Businesses",
  description:
    "Generate high-converting, SEO-optimized websites for HVAC, plumbing, electrical, roofing, painting, and landscaping businesses. Free preview in minutes, not weeks. No credit card required.",
  keywords: [
    "AI website generator", "HVAC website", "plumbing website", "electrical website",
    "roofing website", "painting website", "landscaping website",
    "home service website builder", "contractor website", "AI web design",
    "small business website", "local SEO website", "ISR website",
    "Next.js website generator", "ReliantAI",
  ],
  alternates: {
    canonical: "https://reliantai.org",
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    siteName: "ReliantAI",
    title: "ReliantAI — AI-Powered Websites for Home Service Businesses",
    description:
      "Generate high-converting, SEO-optimized websites for HVAC, plumbing, electrical, roofing, painting, and landscaping businesses. Free preview in minutes.",
    url: "https://reliantai.org",
    images: [
      {
        url: "https://reliantai.org/og/home.png",
        width: 1200,
        height: 630,
        alt: "ReliantAI — AI-Powered Websites for Home Service Businesses",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "ReliantAI — AI-Powered Websites for Home Service Businesses",
    description:
      "Generate high-converting, SEO-optimized websites for HVAC, plumbing, electrical, roofing, painting, and landscaping businesses.",
    images: ["https://reliantai.org/og/home.png"],
  },
};

export default function Home() {
  redirect("/showcase");
}
