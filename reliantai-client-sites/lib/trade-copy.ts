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
    services_title: "Heating & Cooling Work We Handle",
    services_subtitle: "Licensed HVAC service across",
    about_title: "Built for the Climate You Live In",
    about_trust_title: "What Local Homeowners Check First",
    reviews_title: "Recent Jobs From Nearby Homes",
    faq_title: "Heating & Cooling Questions",
    urgency_message: "AC down mid-day? Same-day diagnostic windows when crews are free.",
    estimate_heading: "Get a Written Estimate Before Any Work Starts",
    estimate_subtext: "covers your ZIP with clear pricing — no pressure, no upsell script.",
    trust_badges: ["Licensed & Insured", "EPA 608 Certified", "Background Checked Techs"],
    stats: [
      { label: "Years in Business", value_key: "years_in_business", suffix: "+", fallback: "15" },
      { label: "Google Reviews", value_key: "review_count", suffix: "", fallback: "120" },
      { label: "Google Rating", value_key: "google_rating", suffix: "★", fallback: "4.9" },
      { label: "Same-Day Service", value_key: "_always", suffix: "", fallback: "When available" },
    ],
  },
  plumbing: {
    services_title: "Plumbing Repairs & Installs",
    services_subtitle: "Licensed plumbing crews covering",
    about_title: "Master-Plumber Standards, Local Response",
    about_trust_title: "Proof Before You Book",
    reviews_title: "What Neighbors Reported After the Call",
    faq_title: "Plumbing Questions Homeowners Ask",
    urgency_message: "Active leak? Emergency line staffed nights and weekends.",
    estimate_heading: "Request a Flat-Rate Plumbing Quote",
    estimate_subtext: "confirms availability for your street before dispatch.",
    trust_badges: ["Licensed & Insured", "Master Plumber On Staff", "Background Checked"],
    stats: [
      { label: "Years in Business", value_key: "years_in_business", suffix: "+", fallback: "20" },
      { label: "Google Reviews", value_key: "review_count", suffix: "", fallback: "200" },
      { label: "Google Rating", value_key: "google_rating", suffix: "★", fallback: "4.8" },
      { label: "24/7 Emergency", value_key: "_always", suffix: "", fallback: "Staffed" },
    ],
  },
  electrical: {
    services_title: "Residential Electrical Services",
    services_subtitle: "Code-compliant electrical work in",
    about_title: "Panel Upgrades Done to NEC Spec",
    about_trust_title: "Safety Checks We Document",
    reviews_title: "Homeowner Notes After Service Visits",
    faq_title: "Electrical Safety & Service FAQs",
    urgency_message: "Burning smell or sparking outlet? Call for same-day triage.",
    estimate_heading: "Schedule a Licensed Electrician Visit",
    estimate_subtext: "quotes panel and circuit work before tools come out.",
    trust_badges: ["Licensed & Insured", "NEC Compliant", "Background Checked"],
    stats: [
      { label: "Years in Business", value_key: "years_in_business", suffix: "+", fallback: "12" },
      { label: "Google Reviews", value_key: "review_count", suffix: "", fallback: "150" },
      { label: "Google Rating", value_key: "google_rating", suffix: "★", fallback: "4.9" },
      { label: "Same-Day Available", value_key: "_always", suffix: "", fallback: "Weekdays" },
    ],
  },
  roofing: {
    services_title: "Roof Repair & Replacement",
    services_subtitle: "Storm-ready roofing crews based in",
    about_title: "Roofs Spec'd for Local Weather Loads",
    about_trust_title: "What We Document on Every Bid",
    reviews_title: "Post-Storm and Replacement Reviews",
    faq_title: "Roofing Questions Answered",
    urgency_message: "Active leak after a storm? Inspection slots within 24 hours.",
    estimate_heading: "Book a Free Roof Inspection",
    estimate_subtext: "photographs damage and prices materials before you commit.",
    trust_badges: ["Licensed & Insured", "Manufacturer-Certified", "Workers' Comp Covered"],
    stats: [
      { label: "Years in Business", value_key: "years_in_business", suffix: "+", fallback: "30" },
      { label: "Google Reviews", value_key: "review_count", suffix: "", fallback: "90" },
      { label: "Google Rating", value_key: "google_rating", suffix: "★", fallback: "4.8" },
      { label: "Free Inspections", value_key: "_always", suffix: "", fallback: "Yes" },
    ],
  },
  painting: {
    services_title: "Interior & Exterior Painting",
    services_subtitle: "Prep-first painting crews serving",
    about_title: "Surface Prep Is Half the Job",
    about_trust_title: "What Homeowners Verify Before We Start",
    reviews_title: "Before-and-After Notes From Clients",
    faq_title: "Painting FAQs",
    urgency_message: "Need a room finished before guests arrive? Ask about weekend slots.",
    estimate_heading: "Get a Color Consult & Written Bid",
    estimate_subtext: "measures rooms on-site and locks materials before painting day.",
    trust_badges: ["Licensed & Insured", "Lead-Safe Certified", "Written Satisfaction Terms"],
    stats: [
      { label: "Years in Business", value_key: "years_in_business", suffix: "+", fallback: "12" },
      { label: "Google Reviews", value_key: "review_count", suffix: "", fallback: "110" },
      { label: "Google Rating", value_key: "google_rating", suffix: "★", fallback: "4.9" },
      { label: "Free Consultation", value_key: "_always", suffix: "", fallback: "Yes" },
    ],
  },
  landscaping: {
    services_title: "Lawn, Hardscape & Seasonal Care",
    services_subtitle: "Crews maintaining properties around",
    about_title: "Yards Planned for How You Actually Use Them",
    about_trust_title: "Local Details We Build Into Every Plan",
    reviews_title: "Notes From Neighbors After Install Day",
    faq_title: "Yard & Landscape FAQs",
    urgency_message: "Spring backlog fills fast — reserve an estimate for your block.",
    estimate_heading: "Request a Landscape Site Walk",
    estimate_subtext: "maps drainage and plant choices before quoting materials.",
    trust_badges: ["Licensed & Insured", "Industry Certified Crews", "Seasonal Maintenance Plans"],
    stats: [
      { label: "Years in Business", value_key: "years_in_business", suffix: "+", fallback: "18" },
      { label: "Google Reviews", value_key: "review_count", suffix: "", fallback: "80" },
      { label: "Google Rating", value_key: "google_rating", suffix: "★", fallback: "4.8" },
      { label: "Free Estimates", value_key: "_always", suffix: "", fallback: "Yes" },
    ],
  },
};
