import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { getSiteContent, getTemplate } from "@/lib/api";
import { serializeJsonLd } from "@/lib/serialize-json-ld";
import { generateFAQPage, generateBreadcrumbList } from "@/lib/seo";
import PreviewBanner from "@/components/PreviewBanner";

export const revalidate = 3600;

export async function generateStaticParams() {
  return [];
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const content = await getSiteContent(slug);
  if (!content) return {};

  const title = content.seo?.title || content.meta_title || `${content.business.business_name} - ${content.business.trade.toUpperCase()} in ${content.business.city}, ${content.business.state}`;
  const description = content.seo?.description || content.meta_description || `Professional ${content.business.trade} services in ${content.business.city}, ${content.business.state}. ${content.business.google_rating}★ rated. Call ${content.business.phone}.`;

  return {
    title,
    description,
    keywords: content.seo?.keywords || [
      content.business.trade,
      `${content.business.trade} ${content.business.city}`,
      `${content.business.trade} services`,
      `best ${content.business.trade} in ${content.business.city}`,
      `${content.business.state} ${content.business.trade}`,
    ],
    authors: [{ name: content.business.business_name }],
    creator: content.business.business_name,
    publisher: content.business.business_name,
    alternates: {
      canonical: `https://reliantai.org/${slug}`,
    },
    openGraph: {
      type: "website",
      locale: "en_US",
      siteName: content.business.business_name,
      title,
      description,
      url: `https://reliantai.org/${slug}`,
      images: [
        {
          url: `https://reliantai.org/og/${slug}.png`,
          width: 1200,
          height: 630,
          alt: title,
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [`https://reliantai.org/og/${slug}.png`],
    },
    other: {
      "geo.region": `US-${content.business.state}`,
      "geo.placename": `${content.business.city}, ${content.business.state}`,
      "ICBM": "0, 0",
    },
  };
}

export default async function ClientSitePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const content = await getSiteContent(slug);
  if (!content) return notFound();

  const isPreview = content.status === "preview_live";
  const Template = await getTemplate(content.site_config.template_id);
  if (!Template) return notFound();

  // ── Build comprehensive JSON-LD ──
  const businessName = content.business.business_name;
  const city = content.business.city;
  const state = content.business.state;
  const trade = content.business.trade;
  const phone = content.business.phone;
  const address = content.business.address || "";
  const rating = content.business.google_rating;
  const reviewCount = content.business.review_count;
  const reviews = content.business.reviews || [];
  const faq = content.faq || [];
  const services = content.services || [];
  const aeo = content.aeo_signals;
  const areaServed = aeo?.area_served?.map((a) => ({ "@type": "City", name: a as string })) || [{ "@type": "City", name: city }];

  // LocalBusiness JSON-LD
  const localBusinessSchema = {
    "@context": "https://schema.org",
    "@type": aeo?.local_business_type || "LocalBusiness",
    name: businessName,
    description: content.seo?.description || content.meta_description || `Professional ${trade} services in ${city}, ${state}`,
    url: `https://reliantai.org/${slug}`,
    telephone: phone,
    email: content.business.email || undefined,
    address: {
      "@type": "PostalAddress",
      streetAddress: address,
      addressLocality: city,
      addressRegion: state,
      addressCountry: "US",
    },
    aggregateRating: rating ? {
      "@type": "AggregateRating",
      ratingValue: rating,
      reviewCount: reviewCount,
      bestRating: 5,
      worstRating: 1,
    } : undefined,
    review: reviews.slice(0, 5).map((r) => ({
      "@type": "Review",
      author: { "@type": "Person", name: r.author },
      reviewRating: { "@type": "Rating", ratingValue: r.rating, bestRating: 5 },
      reviewBody: r.text,
    })),
    areaServed,
    serviceType: aeo?.secondary_categories || [trade],
    knowsAbout: aeo?.primary_category ? [aeo.primary_category, trade] : [trade],
  };

  // FAQPage JSON-LD
  const faqJsonLd = faq.length > 0 ? generateFAQPage(faq) : null;

  // Service/Product JSON-LD for each service
  const serviceSchemas = services.map((s) => ({
    "@context": "https://schema.org",
    "@type": "Service",
    name: s.title,
    description: s.description,
    provider: {
      "@type": "LocalBusiness",
      name: businessName,
      address: {
        "@type": "PostalAddress",
        addressLocality: city,
        addressRegion: state,
      },
    },
    areaServed,
  }));

  // BreadcrumbList JSON-LD
  const breadcrumbListContent = generateBreadcrumbList([
    { name: "Home", url: "https://reliantai.org" },
    { name: businessName, url: `https://reliantai.org/${slug}` },
  ]);

  return (
    <>
      {/* LocalBusiness */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: serializeJsonLd(localBusinessSchema) }}
      />
      {/* FAQPage */}
      {faqJsonLd && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: faqJsonLd }}
        />
      )}
      {/* Services */}
      {serviceSchemas.map((s, i) => (
        <script
          key={`service-${i}`}
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: serializeJsonLd(s) }}
        />
      ))}
      {/* BreadcrumbList */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: breadcrumbListContent }}
      />
      {/* Legacy schema_org from API */}
      {content.schema_org && Object.keys(content.schema_org).length > 0 && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: serializeJsonLd(content.schema_org) }}
        />
      )}

      <Template content={content} />
      {isPreview && (
        <PreviewBanner
          slug={slug}
          lighthouseScore={content.lighthouse_score}
          city={city}
        />
      )}
    </>
  );
}
