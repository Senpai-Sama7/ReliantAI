/**
 * SEO/AEO utilities for ReliantAI client sites.
 * Generates JSON-LD structured data, meta tags, and AEO signals.
 */

import { serializeJsonLd } from "./serialize-json-ld";

// ─── Types ────────────────────────────────────────────────────────

export interface LocalBusinessSchema {
  "@context": "https://schema.org";
  "@type": string;
  name: string;
  description?: string;
  url?: string;
  telephone?: string;
  email?: string;
  address: {
    "@type": "PostalAddress";
    streetAddress?: string;
    addressLocality: string;
    addressRegion: string;
    postalCode?: string;
    addressCountry: string;
  };
  geo?: {
    "@type": "GeoCoordinates";
    latitude: number;
    longitude: number;
  };
  openingHours?: string[];
  priceRange?: string;
  aggregateRating?: {
    "@type": "AggregateRating";
    ratingValue: number;
    reviewCount: number;
  };
  review?: Array<{
    "@type": "Review";
    author: { "@type": "Person"; name: string };
    reviewRating: { "@type": "Rating"; ratingValue: number };
    reviewBody: string;
    datePublished?: string;
  }>;
  areaServed?: Array<{ "@type": "City"; name: string }>;
  serviceType?: string[];
  knowsAbout?: string[];
  sameAs?: string[];
  image?: string;
  logo?: string;
}

export interface FAQPageSchema {
  "@context": "https://schema.org";
  "@type": "FAQPage";
  mainEntity: Array<{
    "@type": "Question";
    name: string;
    acceptedAnswer: {
      "@type": "Answer";
      text: string;
    };
  }>;
}

export interface ProductSchema {
  "@context": "https://schema.org";
  "@type": "Product";
  name: string;
  description?: string;
  image?: string;
  url?: string;
  brand?: { "@type": "Brand"; name: string };
  offers?: {
    "@type": "Offer";
    price?: string;
    priceCurrency?: string;
    availability?: string;
    url?: string;
  };
  aggregateRating?: {
    "@type": "AggregateRating";
    ratingValue: number;
    reviewCount: number;
  };
}

export interface WebSiteSchema {
  "@context": "https://schema.org";
  "@type": "WebSite";
  name: string;
  url: string;
  description?: string;
  publisher: {
    "@type": "Organization";
    name: string;
    url: string;
    logo?: string;
  };
  potentialAction?: {
    "@type": "SearchAction";
    target: string;
    "query-input": string;
  };
}

export interface OrganizationSchema {
  "@context": "https://schema.org";
  "@type": "Organization";
  name: string;
  url: string;
  logo?: string;
  description?: string;
  sameAs?: string[];
  contactPoint?: {
    "@type": "ContactPoint";
    telephone: string;
    contactType: string;
    areaServed?: string;
  }[];
}

export interface BreadcrumbListSchema {
  "@context": "https://schema.org";
  "@type": "BreadcrumbList";
  itemListElement: Array<{
    "@type": "ListItem";
    position: number;
    name: string;
    item: string;
  }>;
}

// ─── Generators ───────────────────────────────────────────────────

export function generateLocalBusiness(data: {
  name: string;
  description?: string;
  url?: string;
  telephone?: string;
  email?: string;
  street?: string;
  city: string;
  state: string;
  zip?: string;
  country?: string;
  lat?: number;
  lng?: number;
  hours?: string[];
  priceRange?: string;
  rating?: number;
  reviewCount?: number;
  reviews?: Array<{ author: string; rating: number; text: string; date?: string }>;
  areaServed?: string[];
  serviceType?: string[];
  knowsAbout?: string[];
  sameAs?: string[];
  image?: string;
  logo?: string;
  businessType?: string;
}): string {
  const schema: LocalBusinessSchema = {
    "@context": "https://schema.org",
    "@type": data.businessType || "LocalBusiness",
    name: data.name,
    description: data.description,
    url: data.url,
    telephone: data.telephone,
    email: data.email,
    address: {
      "@type": "PostalAddress",
      streetAddress: data.street,
      addressLocality: data.city,
      addressRegion: data.state,
      postalCode: data.zip,
      addressCountry: data.country || "US",
    },
  };

  if (data.lat && data.lng) {
    schema.geo = { "@type": "GeoCoordinates", latitude: data.lat, longitude: data.lng };
  }
  if (data.hours?.length) schema.openingHours = data.hours;
  if (data.priceRange) schema.priceRange = data.priceRange;
  if (data.rating !== undefined && data.reviewCount !== undefined) {
    schema.aggregateRating = { "@type": "AggregateRating", ratingValue: data.rating, reviewCount: data.reviewCount };
  }
  if (data.reviews?.length) {
    schema.review = data.reviews.map((r) => ({
      "@type": "Review",
      author: { "@type": "Person", name: r.author },
      reviewRating: { "@type": "Rating", ratingValue: r.rating },
      reviewBody: r.text,
      datePublished: r.date,
    }));
  }
  if (data.areaServed?.length) {
    schema.areaServed = data.areaServed.map((a) => ({ "@type": "City", name: a }));
  }
  if (data.serviceType?.length) schema.serviceType = data.serviceType;
  if (data.knowsAbout?.length) schema.knowsAbout = data.knowsAbout;
  if (data.sameAs?.length) schema.sameAs = data.sameAs;
  if (data.image) schema.image = data.image;
  if (data.logo) schema.logo = data.logo;

  return serializeJsonLd(schema);
}

export function generateFAQPage(faqs: Array<{ question: string; answer: string }>): string {
  const schema: FAQPageSchema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faqs.map((faq) => ({
      "@type": "Question",
      name: faq.question,
      acceptedAnswer: { "@type": "Answer", text: faq.answer },
    })),
  };
  return serializeJsonLd(schema);
}

export function generateProduct(data: {
  name: string;
  description?: string;
  image?: string;
  url?: string;
  brand?: string;
  price?: string;
  currency?: string;
  availability?: string;
  rating?: number;
  reviewCount?: number;
}): string {
  const schema: ProductSchema = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: data.name,
    description: data.description,
    image: data.image,
    url: data.url,
  };
  if (data.brand) schema.brand = { "@type": "Brand", name: data.brand };
  if (data.price) {
    schema.offers = {
      "@type": "Offer",
      price: data.price,
      priceCurrency: data.currency || "USD",
      availability: data.availability || "https://schema.org/InStock",
      url: data.url,
    };
  }
  if (data.rating !== undefined && data.reviewCount !== undefined) {
    schema.aggregateRating = { "@type": "AggregateRating", ratingValue: data.rating, reviewCount: data.reviewCount };
  }
  return serializeJsonLd(schema);
}

export function generateWebSite(data: {
  name: string;
  url: string;
  description?: string;
  orgName: string;
  orgUrl: string;
  orgLogo?: string;
  searchUrl?: string;
}): string {
  const schema: WebSiteSchema = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: data.name,
    url: data.url,
    description: data.description,
    publisher: {
      "@type": "Organization",
      name: data.orgName,
      url: data.orgUrl,
      logo: data.orgLogo,
    },
  };
  if (data.searchUrl) {
    schema.potentialAction = {
      "@type": "SearchAction",
      target: data.searchUrl,
      "query-input": "required name=search_term_string",
    };
  }
  return serializeJsonLd(schema);
}

export function generateOrganization(data: {
  name: string;
  url: string;
  logo?: string;
  description?: string;
  sameAs?: string[];
  phone?: string;
  email?: string;
}): string {
  const schema: OrganizationSchema = {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: data.name,
    url: data.url,
    logo: data.logo,
    description: data.description,
    sameAs: data.sameAs,
  };
  if (data.phone || data.email) {
    schema.contactPoint = [];
    if (data.phone) {
      schema.contactPoint.push({
        "@type": "ContactPoint",
        telephone: data.phone,
        contactType: "customer service",
        areaServed: "US",
      });
    }
    if (data.email) {
      schema.contactPoint.push({
        "@type": "ContactPoint",
        telephone: data.email,
        contactType: "sales",
        areaServed: "US",
      });
    }
  }
  return serializeJsonLd(schema);
}

export function generateBreadcrumbList(items: Array<{ name: string; url: string }>): string {
  const schema: BreadcrumbListSchema = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, i) => ({
      "@type": "ListItem",
      position: i + 1,
      name: item.name,
      item: item.url,
    })),
  };
  return serializeJsonLd(schema);
}

// ─── Meta Tag Generators ──────────────────────────────────────────

export function generateGeoMeta(data: {
  region: string;
  placename: string;
  position: string;
  icbm: string;
}): string {
  return [
    `<meta name="geo.region" content="${data.region}" />`,
    `<meta name="geo.placename" content="${data.placename}" />`,
    `<meta name="geo.position" content="${data.position}" />`,
    `<meta name="ICBM" content="${data.icbm}" />`,
  ].join("\n");
}

export function generateOpenGraph(data: {
  title: string;
  description: string;
  url: string;
  type?: string;
  image?: string;
  siteName?: string;
  locale?: string;
}): string {
  const lines = [
    `<meta property="og:title" content="${data.title}" />`,
    `<meta property="og:description" content="${data.description}" />`,
    `<meta property="og:url" content="${data.url}" />`,
    `<meta property="og:type" content={data.type || "website"} />`,
  ];
  if (data.image) lines.push(`<meta property="og:image" content="${data.image}" />`);
  if (data.siteName) lines.push(`<meta property="og:site_name" content="${data.siteName}" />`);
  if (data.locale) lines.push(`<meta property="og:locale" content="${data.locale}" />`);
  return lines.join("\n");
}

export function generateTwitterCard(data: {
  title: string;
  description: string;
  image?: string;
  card?: string;
  site?: string;
}): string {
  const lines = [
    `<meta name="twitter:card" content="${data.card || "summary_large_image"}" />`,
    `<meta name="twitter:title" content="${data.title}" />`,
    `<meta name="twitter:description" content="${data.description}" />`,
  ];
  if (data.image) lines.push(`<meta name="twitter:image" content="${data.image}" />`);
  if (data.site) lines.push(`<meta name="twitter:site" content="${data.site}" />`);
  return lines.join("\n");
}

export function generateAEOGeoTags(data: {
  country: string;
  region: string;
  city: string;
  zip?: string;
  lat: number;
  lng: number;
}): string {
  return [
    `<meta name="country" content="${data.country}" />`,
    `<meta name="region" content="${data.region}" />`,
    `<meta name="city" content="${data.city}" />`,
    data.zip ? `<meta name="zip" content="${data.zip}" />` : "",
    `<meta name="latitude" content="${data.lat}" />`,
    `<meta name="longitude" content="${data.lng}" />`,
  ].filter(Boolean).join("\n");
}
