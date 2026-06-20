import type { MetadataRoute } from "next";

const BASE_URL = "https://reliantai.org";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: [
          "/api/",
          "/_next/",
          "/private/",
          "/admin/",
        ],
      },
      // ── AI Crawlers (AEO) ──
      {
        userAgent: "GPTBot",
        allow: "/",
        disallow: ["/api/", "/_next/", "/private/", "/admin/"],
      },
      {
        userAgent: "ChatGPT-User",
        allow: "/",
        disallow: ["/api/", "/_next/", "/private/", "/admin/"],
      },
      {
        userAgent: "Google-Extended",
        allow: "/",
        disallow: ["/api/", "/_next/", "/private/", "/admin/"],
      },
      {
        userAgent: "PerplexityBot",
        allow: "/",
        disallow: ["/api/", "/_next/", "/private/", "/admin/"],
      },
      {
        userAgent: "ClaudeBot",
        allow: "/",
        disallow: ["/api/", "/_next/", "/private/", "/admin/"],
      },
      {
        userAgent: "CCBot",
        allow: "/",
        disallow: ["/api/", "/_next/", "/private/", "/admin/"],
      },
      {
        userAgent: "OAI-SearchBot",
        allow: "/",
        disallow: ["/api/", "/_next/", "/private/", "/admin/"],
      },
      {
        userAgent: "Applebot",
        allow: "/",
        disallow: ["/api/", "/_next/", "/private/", "/admin/"],
      },
      // ── Search Engines ──
      {
        userAgent: "Googlebot",
        allow: "/",
        disallow: ["/api/", "/_next/", "/private/", "/admin/"],
      },
      {
        userAgent: "Bingbot",
        allow: "/",
        disallow: ["/api/", "/_next/", "/private/", "/admin/"],
      },
    ],
    sitemap: `${BASE_URL}/sitemap.xml`,
    host: BASE_URL,
  };
}
