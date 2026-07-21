import type { Metadata, Viewport } from "next";
import { DM_Sans, Instrument_Serif } from "next/font/google";
import "./globals.css";

const dmSans = DM_Sans({
  variable: "--font-dm-sans",
  subsets: ["latin"],
  display: "swap",
});

const instrumentSerif = Instrument_Serif({
  variable: "--font-instrument-serif",
  subsets: ["latin"],
  weight: "400",
  display: "swap",
});

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#09090b" },
  ],
};

export const metadata: Metadata = {
  title: {
    default: "ReliantAI — AI-Powered Websites for Home Service Businesses",
    template: "%s | ReliantAI",
  },
  description:
    "ReliantAI generates high-converting, SEO-optimized websites for HVAC, plumbing, electrical, roofing, and home service businesses. Get a professional website in minutes, not weeks. Free preview.",
  keywords: [
    "AI website generator",
    "HVAC website",
    "plumbing website",
    "electrical website",
    "roofing website",
    "home service website",
    "contractor website builder",
    "local SEO website",
    "ReliantAI",
  ],
  authors: [{ name: "ReliantAI", url: "https://reliantai.org" }],
  creator: "ReliantAI",
  publisher: "ReliantAI",
  applicationName: "ReliantAI",
  referrer: "origin-when-cross-origin",
  category: "technology",

  robots: {
    index: true,
    follow: true,
    "max-image-preview": "large",
    "max-snippet": -1,
    "max-video-preview": -1,
    googleBot: {
      index: true,
      follow: true,
      "max-image-preview": "large",
      "max-snippet": -1,
      "max-video-preview": -1,
    },
  },

  alternates: {
    canonical: "https://reliantai.org",
    languages: {
      "en-US": "https://reliantai.org",
      en: "https://reliantai.org",
    },
  },

  openGraph: {
    type: "website",
    locale: "en_US",
    siteName: "ReliantAI",
    title: "ReliantAI — AI-Powered Websites for Home Service Businesses",
    description:
      "Generate high-converting, SEO-optimized websites for HVAC, plumbing, electrical, and home service businesses. Free preview. No credit card.",
    url: "https://reliantai.org",
    images: [
      {
        url: "https://reliantai.org/og-image.png",
        width: 1200,
        height: 630,
        alt: "ReliantAI — AI-Powered Websites for Home Service Businesses",
        type: "image/png",
      },
    ],
  },

  twitter: {
    card: "summary_large_image",
    site: "@reliantai",
    creator: "@reliantai",
    title: "ReliantAI — AI-Powered Websites for Home Service Businesses",
    description:
      "Generate high-converting, SEO-optimized websites for HVAC, plumbing, electrical, and home service businesses. Free preview.",
    images: [
      {
        url: "https://reliantai.org/og-image.png",
        alt: "ReliantAI — AI-Powered Websites for Home Service Businesses",
      },
    ],
  },

  other: {
    "format-detection": "telephone=no",
  },

  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/icon-192.png", type: "image/png", sizes: "192x192" },
      { url: "/icon-512.png", type: "image/png", sizes: "512x512" },
    ],
    apple: [{ url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" }],
  },

  manifest: "/site.webmanifest",

  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "ReliantAI",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      dir="ltr"
      className={`${dmSans.variable} ${instrumentSerif.variable} h-full antialiased`}
    >
      <head>
        <meta name="application-name" content="ReliantAI" />
        <meta name="apple-mobile-web-app-title" content="ReliantAI" />
        <meta name="theme-color" content="#09090b" media="(prefers-color-scheme: dark)" />
        <meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)" />
        <meta name="format-detection" content="telephone=no" />
        <meta name="mobile-web-app-capable" content="yes" />

        <link rel="alternate" hrefLang="en-US" href="https://reliantai.org" />
        <link rel="alternate" hrefLang="en" href="https://reliantai.org" />
        <link rel="alternate" hrefLang="x-default" href="https://reliantai.org" />

        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@graph": [
                {
                  "@type": "Organization",
                  "@id": "https://reliantai.org/#organization",
                  name: "ReliantAI",
                  url: "https://reliantai.org",
                  logo: {
                    "@type": "ImageObject",
                    url: "https://reliantai.org/logo.png",
                    width: 512,
                    height: 512,
                  },
                  description:
                    "AI-powered website generator for home service businesses. Generate high-converting, SEO-optimized websites for HVAC, plumbing, electrical, roofing, painting, and landscaping.",
                  foundingDate: "2024",
                  sameAs: [
                    "https://twitter.com/reliantai",
                    "https://linkedin.com/company/reliantai",
                    "https://github.com/reliantai",
                  ],
                  contactPoint: [
                    {
                      "@type": "ContactPoint",
                      contactType: "sales",
                      email: "hello@reliantai.org",
                      areaServed: "US",
                    },
                  ],
                },
                {
                  "@type": "WebSite",
                  "@id": "https://reliantai.org/#website",
                  name: "ReliantAI",
                  url: "https://reliantai.org",
                  description: "AI-powered website generator for home service businesses",
                  publisher: { "@id": "https://reliantai.org/#organization" },
                },
              ],
            }).replace(/</g, "\\u003c"),
          }}
        />
      </head>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
