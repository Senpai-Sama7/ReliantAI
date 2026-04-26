import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { getSiteContent, getTemplate } from "@/lib/api";
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
  return {
    title: content.seo.title,
    description: content.seo.description,
    other: {
      "script:ld+json": JSON.stringify(content.schema_org),
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

  return (
    <>
      <Template content={content} />
      {isPreview && (
        <PreviewBanner
          slug={slug}
          lighthouseScore={content.lighthouse_score}
          city={content.business.city}
        />
      )}
    </>
  );
}
