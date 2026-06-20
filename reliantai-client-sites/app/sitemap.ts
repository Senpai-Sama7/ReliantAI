import type { MetadataRoute } from "next";

const BASE_URL = "https://reliantai.org";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();

  // Static pages
  const staticPages: MetadataRoute.Sitemap = [
    {
      url: BASE_URL,
      lastModified: now,
      changeFrequency: "weekly",
      priority: 1.0,
    },
    {
      url: `${BASE_URL}/showcase`,
      lastModified: now,
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${BASE_URL}/preview`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.7,
    },
  ];

  // Template showcase pages (for SEO — each template as a landing page)
  const templatePages: MetadataRoute.Sitemap = [
    {
      url: `${BASE_URL}/templates/hvac`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${BASE_URL}/templates/plumbing`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${BASE_URL}/templates/electrical`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${BASE_URL}/templates/roofing`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${BASE_URL}/templates/landscaping`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${BASE_URL}/templates/painting`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.8,
    },
  ];

  return [...staticPages, ...templatePages];
}
