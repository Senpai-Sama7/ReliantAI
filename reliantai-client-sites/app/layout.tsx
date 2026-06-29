import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
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
    "AI website generator", "HVAC website", "plumbing website", "electrical website",
    "roofing website", "home service website", "contractor website builder",
    "AI web design", "small business website", "local SEO website",
    "ISR website", "Next.js website generator", "ReliantAI",
  ],
  authors: [{ name: "ReliantAI", url: "https://reliantai.org" }],
  creator: "ReliantAI",
  publisher: "ReliantAI",
  applicationName: "ReliantAI",
  generator: "Next.js",
  referrer: "origin-when-cross-origin",
  category: "technology",
  classification: "AI Website Generator",

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
      "en": "https://reliantai.org",
    },
  },

  openGraph: {
    type: "website",
    locale: "en_US",
    alternateLocale: ["en_US"],
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

  verification: {
    google: "google-site-verification-code",
  },
  other: {
    "geo.region": "US",
    "geo.placename": "United States",
    "geo.position": "39.8283;-98.5795",
    "ICBM": "39.8283, -98.5795",
    "country": "US",
    "format-detection": "telephone=no",
    "msvalidate.01": "bing-verification-code",
    "yandex-verification": "yandex-verification-code",
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
    <html lang="en" dir="ltr" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <head>
        <meta name="geo.region" content="US" />
        <meta name="geo.placename" content="United States" />
        <meta name="geo.position" content="39.8283;-98.5795" />
        <meta name="ICBM" content="39.8283, -98.5795" />
        <meta name="country" content="US" />

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
                  description: "AI-powered website generator for home service businesses. Generate high-converting, SEO-optimized websites for HVAC, plumbing, electrical, roofing, painting, and landscaping.",
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
                    {
                      "@type": "ContactPoint",
                      contactType: "customer service",
                      email: "support@reliantai.org",
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
                  potentialAction: {
                    "@type": "SearchAction",
                    target: "https://reliantai.org/search?q={search_term_string}",
                    "query-input": "required name=search_term_string",
                  },
                },
                {
                  "@type": "WebPage",
                  "@id": "https://reliantai.org/#webpage",
                  url: "https://reliantai.org",
                  name: "ReliantAI — AI-Powered Websites for Home Service Businesses",
                  description: "Generate high-converting, SEO-optimized websites for HVAC, plumbing, electrical, roofing, painting, and landscaping businesses.",
                  isPartOf: { "@id": "https://reliantai.org/#website" },
                  about: { "@id": "https://reliantai.org/#organization" },
                  datePublished: "2024-01-01",
                  dateModified: new Date().toISOString().split("T")[0],
                  inLanguage: "en-US",
                  primaryImageOfPage: {
                    "@type": "ImageObject",
                    url: "https://reliantai.org/og/home.png",
                    width: 1200,
                    height: 630,
                  },
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
