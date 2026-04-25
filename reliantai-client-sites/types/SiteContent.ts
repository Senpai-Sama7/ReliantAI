export interface BusinessInfo {
  business_name: string;
  trade: string;
  city: string;
  state: string;
  phone: string;
  email?: string;
  address: string;
  google_rating: number;
  review_count: number;
  website_url?: string;
  owner_name?: string;
  owner_title?: string;
  years_in_business?: number;
  service_area?: string;
  reviews?: Review[];
}

export interface HeroSection {
  headline: string;
  subheadline: string;
  trust_bar: string[];
  cta_primary: string;
  cta_primary_url: string;
  cta_secondary: string;
  cta_secondary_url: string;
}

export interface ServiceItem {
  icon: string;
  title: string;
  description: string;
  cta_text: string;
}

export interface AboutSection {
  story: string;
  trust_points: string[];
  certifications: string[];
}

export interface Review {
  author: string;
  rating: number;
  text: string;
  time: string;
}

export interface ReviewsSection {
  reviews: Review[];
  aggregate_line: string;
}

export interface FAQItem {
  question: string;
  answer: string;
}

export interface SEOMeta {
  title: string;
  description: string;
  keywords: string[];
}

export interface AEOSignals {
  local_business_type: string;
  primary_category: string;
  secondary_categories: string[];
  area_served: string[];
}

export interface ThemeConfig {
  primary: string;
  accent: string;
  font_display: string;
  font_body: string;
}

export interface SiteContent {
  business: BusinessInfo;
  hero: HeroSection;
  services: ServiceItem[];
  about: AboutSection;
  reviews: ReviewsSection;
  faq: FAQItem[];
  seo: SEOMeta;
  aeo_signals: AEOSignals;
  schema_org: Record<string, unknown>;
  site_config: {
    template_id: string;
    trade: string;
    theme: ThemeConfig;
  };
  status: string;
  slug: string;
  meta_title: string;
  meta_description: string;
  lighthouse_score: number;
}
