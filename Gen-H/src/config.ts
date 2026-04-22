// GEN-H Studio - Site Configuration
// Content centralized per design spec

export interface SiteConfig {
  language: string;
  siteName: string;
  siteDescription: string;
}

export const siteConfig: SiteConfig = {
  language: "en",
  siteName: "GEN-H Studio",
  siteDescription: "Premium HVAC growth systems. Websites that attract. Briefs that qualify. A portal that converts.",
};

// Hero Section Configuration
export interface HeroConfig {
  backgroundImage: string;
  backgroundAlt: string;
  title: string;
  subtitle: string;
  ctaPrimary: string;
  ctaSecondary: string;
}

export const heroConfig: HeroConfig = {
  backgroundImage: "/hero-bg.jpg",
  backgroundAlt: "Modern minimalist interior representing premium HVAC solutions",
  title: "PREMIUM HVAC GROWTH SYSTEMS",
  subtitle: "Websites that attract. Briefs that qualify. A portal that converts.",
  ctaPrimary: "Start the Strategy Brief",
  ctaSecondary: "Book a Discovery Call",
};

// Narrative Text Section Configuration
export interface NarrativeTextConfig {
  line1: string;
  line2: string;
  line3: string;
}

export const narrativeTextConfig: NarrativeTextConfig = {
  line1: "We build premium digital experiences for HVAC companies ready to scale.",
  line2: "Clear positioning, smart lead capture, and a control room for your pipeline.",
  line3: "From first impression to final signature—every touchpoint engineered for growth.",
};

// Card Stack Section Configuration
export interface CardStackItem {
  id: number;
  image: string;
  title: string;
  description: string;
  rotation: number;
}

export interface CardStackConfig {
  sectionTitle: string;
  sectionSubtitle: string;
  cards: CardStackItem[];
}

export const cardStackConfig: CardStackConfig = {
  sectionTitle: "What We Build",
  sectionSubtitle: "Three Pillars of Growth",
  cards: [
    {
      id: 1,
      image: "/card-1.jpg",
      title: "ATTRACT",
      description: "Premium positioning, fast load times, and local SEO that puts you in front of high-intent buyers.",
      rotation: -2,
    },
    {
      id: 2,
      image: "/card-2.jpg",
      title: "QUALIFY",
      description: "A smart brief captures budget, timeline, and scope—so your team talks to real opportunities.",
      rotation: 1,
    },
    {
      id: 3,
      image: "/card-3.jpg",
      title: "CONVERT",
      description: "A private admin portal routes leads, tracks follow-ups, and shows what's actually working.",
      rotation: -1,
    },
  ],
};

// Breath Section Configuration
export interface BreathSectionConfig {
  backgroundImage: string;
  backgroundAlt: string;
  title: string;
  subtitle: string;
  description: string;
  metrics: {
    fitScore: string;
    urgency: string;
    clarity: string;
  };
}

export const breathSectionConfig: BreathSectionConfig = {
  backgroundImage: "/breath-bg.jpg",
  backgroundAlt: "HVAC control room with digital dashboards",
  title: "YOUR DASHBOARD, NOT A BLACK BOX",
  subtitle: "Complete Pipeline Visibility",
  description: "See every lead, every stage, and every next step. Assign tasks, add notes, and know what's booked—without digging through inboxes.",
  metrics: {
    fitScore: "74%",
    urgency: "68%",
    clarity: "82%",
  },
};

// ZigZag Grid Section Configuration
export interface ZigZagGridItem {
  id: string;
  title: string;
  subtitle: string;
  description: string;
  image: string;
  imageAlt: string;
  reverse: boolean;
}

export interface ZigZagGridConfig {
  sectionLabel: string;
  sectionTitle: string;
  items: ZigZagGridItem[];
}

export const zigZagGridConfig: ZigZagGridConfig = {
  sectionLabel: "How It Works",
  sectionTitle: "From Clarity to Conversion",
  items: [
    {
      id: "clarify",
      title: "Make the value obvious in seconds",
      subtitle: "01 / Clarify",
      description: "We build a clear story: what you do, who it's for, and why it's worth more—so premium buyers understand instantly. No confusion. No friction. Just clarity that converts.",
      image: "/grid-1.jpg",
      imageAlt: "Team collaborating to clarify brand positioning",
      reverse: false,
    },
    {
      id: "capture",
      title: "Collect intent, not just contact info",
      subtitle: "02 / Capture",
      description: "A structured brief asks the right questions—budget, timing, scope—so your team starts with context. Separate price shoppers from real buyers before the first call.",
      image: "/grid-2.jpg",
      imageAlt: "Professional reviewing lead qualification data",
      reverse: true,
    },
    {
      id: "run",
      title: "Review, assign, and close in one place",
      subtitle: "03 / Run",
      description: "Leads flow into a private portal where you can qualify, track, and follow up without losing momentum. Your dashboard, not a black box.",
      image: "/grid-3.jpg",
      imageAlt: "HVAC technician using digital portal",
      reverse: false,
    },
    {
      id: "optimize",
      title: "Scale with confidence",
      subtitle: "04 / Optimize",
      description: "Data-driven insights show what's working. Refine your approach, expand to new markets, and build a growth engine that keeps delivering.",
      image: "/grid-4.jpg",
      imageAlt: "Executive reviewing analytics dashboard",
      reverse: true,
    },
  ],
};

// Footer Section Configuration
export interface FooterContactItem {
  type: "email" | "phone";
  label: string;
  value: string;
  href: string;
}

export interface FooterSocialItem {
  platform: string;
  href: string;
}

export interface FooterConfig {
  heading: string;
  description: string;
  ctaText: string;
  contact: FooterContactItem[];
  locationLabel: string;
  address: string[];
  socialLabel: string;
  socials: FooterSocialItem[];
  logoText: string;
  copyright: string;
  links: { label: string; href: string }[];
}

export const footerConfig: FooterConfig = {
  heading: "READY TO TURN TRAFFIC INTO PIPELINE?",
  description: "Tell us what you're building. We'll reply within one business day with next steps and a clear path forward.",
  ctaText: "Start the Strategy Brief",
  contact: [
    {
      type: "email",
      label: "advisors@genh.studio",
      value: "advisors@genh.studio",
      href: "mailto:advisors@genh.studio",
    },
    {
      type: "phone",
      label: "(555) 014-8891",
      value: "(555) 014-8891",
      href: "tel:+15550148891",
    },
  ],
  locationLabel: "Location",
  address: ["Austin, TX", "Remote Worldwide"],
  socialLabel: "Follow",
  socials: [
    {
      platform: "instagram",
      href: "https://instagram.com/genhstudio",
    },
    {
      platform: "facebook",
      href: "https://facebook.com/genhstudio",
    },
  ],
  logoText: "GEN-H",
  copyright: "© 2025 GEN-H Studio. All rights reserved.",
  links: [
    { label: "Privacy Policy", href: "#" },
    { label: "Terms of Service", href: "#" },
  ],
};
