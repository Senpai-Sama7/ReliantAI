export interface TradeCopy {
  services_title: string;
  services_subtitle: string;
  about_title: string;
  about_trust_title: string;
  reviews_title: string;
  faq_title: string;
  urgency_message: string;
  estimate_heading: string;
  estimate_subtext: string;
  trust_badges: string[];
  stats: { label: string; value_key: string; suffix: string; fallback: string }[];
}

export const TRADE_COPY: Record<string, TradeCopy> = {
  hvac: {
    services_title: "Heating & Cooling Solutions",
    services_subtitle: "Professional HVAC services in",
    about_title: "Your Comfort Is Our Mission",
    about_trust_title: "Why Homeowners Choose Us",
    reviews_title: "Stay Comfortable — Hear From Our Customers",
    faq_title: "Heating & Cooling Questions",
    urgency_message: "AC broken? We can be there today. Call now.",
    estimate_heading: "Ready for a Free Estimate?",
    estimate_subtext: "serves your area with no obligation, no pressure.",
    trust_badges: ["Licensed & Insured", "EPA Certified", "Background Checked"],
    stats: [
      { label: "Years in Business", value_key: "years_in_business", suffix: "+", fallback: "15" },
      { label: "Homes Serviced", value_key: "_derived", suffix: "+", fallback: "5,000" },
      { label: "Google Rating", value_key: "google_rating", suffix: "★", fallback: "4.9" },
      { label: "Same-Day Service", value_key: "_always", suffix: "", fallback: "Available" },
    ],
  },
  plumbing: {
    services_title: "Plumbing Services You Can Trust",
    services_subtitle: "Professional plumbing services in",
    about_title: "Built on Trust, Backed by Skill",
    about_trust_title: "Why Our Customers Trust Us",
    reviews_title: "Trusted by Homeowners",
    faq_title: "Common Plumbing Questions",
    urgency_message: "Burst pipe? 24/7 emergency response. Call now.",
    estimate_heading: "Need a Plumber? Get a Free Estimate",
    estimate_subtext: "is standing by — no obligation, fast response.",
    trust_badges: ["Licensed & Insured", "Master Plumber Certified", "Background Checked"],
    stats: [
      { label: "Years in Business", value_key: "years_in_business", suffix: "+", fallback: "20" },
      { label: "Pipes Fixed", value_key: "_derived", suffix: "+", fallback: "10,000" },
      { label: "Google Rating", value_key: "google_rating", suffix: "★", fallback: "4.8" },
      { label: "24/7 Emergency", value_key: "_always", suffix: "", fallback: "Available" },
    ],
  },
  electrical: {
    services_title: "Electrical Services",
    services_subtitle: "Professional electrical services in",
    about_title: "Powering Homes Safely",
    about_trust_title: "Why Homeowners Trust Our Electricians",
    reviews_title: "What Our Customers Say About Our Work",
    faq_title: "Electrical Safety & Service FAQs",
    urgency_message: "Sparking outlet? Same-day service available. Call now.",
    estimate_heading: "Need Electrical Work? Get a Free Quote",
    estimate_subtext: "provides fast, safe electrical service with free estimates.",
    trust_badges: ["Licensed & Insured", "NEC Compliant", "Background Checked"],
    stats: [
      { label: "Years in Business", value_key: "years_in_business", suffix: "+", fallback: "12" },
      { label: "Homes Powered", value_key: "_derived", suffix: "+", fallback: "8,000" },
      { label: "Google Rating", value_key: "google_rating", suffix: "★", fallback: "4.9" },
      { label: "Same-Day Available", value_key: "_always", suffix: "", fallback: "Available" },
    ],
  },
  roofing: {
    services_title: "Roofing & Protection Services",
    services_subtitle: "Professional roofing services in",
    about_title: "Protecting Homes, One Roof at a Time",
    about_trust_title: "Why Homeowners Trust Our Roofers",
    reviews_title: "Roofing Reviews From Homeowners",
    faq_title: "Roofing Questions Answered",
    urgency_message: "Storm damage? Free inspection within 24 hours.",
    estimate_heading: "Get a Free Roof Inspection",
    estimate_subtext: "offers free, no-obligation roof inspections.",
    trust_badges: ["Licensed & Insured", "GAF Certified", "Worker's Comp Covered"],
    stats: [
      { label: "Years in Business", value_key: "years_in_business", suffix: "+", fallback: "30" },
      { label: "Roofs Protected", value_key: "_derived", suffix: "+", fallback: "2,500" },
      { label: "Google Rating", value_key: "google_rating", suffix: "★", fallback: "4.8" },
      { label: "Free Inspections", value_key: "_always", suffix: "", fallback: "Available" },
    ],
  },
  painting: {
    services_title: "Our Painting Services",
    services_subtitle: "Professional painting services in",
    about_title: "Transforming Spaces, One Brushstroke at a Time",
    about_trust_title: "Why Homeowners Trust Our Painters",
    reviews_title: "See Our Transformations",
    faq_title: "Painting FAQs",
    urgency_message: "Ready to transform your space? Free color consultation.",
    estimate_heading: "Get a Free Color Consultation",
    estimate_subtext: "offers free consultations — see the possibilities.",
    trust_badges: ["Licensed & Insured", "Lead-Safe Certified", "Satisfaction Guaranteed"],
    stats: [
      { label: "Years in Business", value_key: "years_in_business", suffix: "+", fallback: "12" },
      { label: "Homes Transformed", value_key: "_derived", suffix: "+", fallback: "3,000" },
      { label: "Google Rating", value_key: "google_rating", suffix: "★", fallback: "4.9" },
      { label: "Free Consultation", value_key: "_always", suffix: "", fallback: "Available" },
    ],
  },
  landscaping: {
    services_title: "Yard & Landscape Services",
    services_subtitle: "Professional landscaping services in",
    about_title: "Growing Beautiful Spaces",
    about_trust_title: "Why Homeowners Trust Our Team",
    reviews_title: "What Our Clients Say About Their Yards",
    faq_title: "Yard & Landscape FAQs",
    urgency_message: "Want a yard you love? Get a free estimate today.",
    estimate_heading: "Get a Free Landscape Estimate",
    estimate_subtext: "designs beautiful outdoor spaces — free estimates.",
    trust_badges: ["Licensed & Insured", "Green Industry Certified", "Satisfaction Guaranteed"],
    stats: [
      { label: "Years in Business", value_key: "years_in_business", suffix: "+", fallback: "18" },
      { label: "Yards Maintained", value_key: "_derived", suffix: "+", fallback: "4,000" },
      { label: "Google Rating", value_key: "google_rating", suffix: "★", fallback: "4.8" },
      { label: "Free Estimates", value_key: "_always", suffix: "", fallback: "Available" },
    ],
  },
};
