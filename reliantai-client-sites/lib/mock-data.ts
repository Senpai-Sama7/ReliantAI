import type { SiteContent } from "@/types/SiteContent";

const MOCK_BUSINESS = {
  business_name: "Comfort Pro HVAC",
  trade: "hvac",
  city: "Austin",
  state: "TX",
  phone: "(512) 555-0199",
  email: "info@comfortprohvac.com",
  address: "1234 Oak Lane, Austin, TX 78701",
  google_rating: 4.9,
  review_count: 342,
  website_url: "https://comfortprohvac.com",
  owner_name: "Mike Hartwell",
  owner_title: "Founder & Master Technician",
  years_in_business: 15,
  service_area: "Greater Austin Metro Area",
};

const MOCK_REVIEWS = [
  { author: "Sarah M.", rating: 5, text: "They came out same day when our AC died in August. Professional, fast, and fair pricing. Haven't had an issue since.", time: "2 weeks ago" },
  { author: "David R.", rating: 5, text: "Best HVAC company in Austin, period. Mike explained everything clearly and didn't try to upsell us on stuff we didn't need.", time: "1 month ago" },
  { author: "Jennifer K.", rating: 5, text: "Our furnace went out on the coldest night of the year. They were here within 2 hours. Eternally grateful.", time: "3 months ago" },
  { author: "Tom W.", rating: 4, text: "Good service, honest technicians. Only reason for 4 stars is scheduling was a bit tight during peak summer.", time: "2 months ago" },
  { author: "Maria L.", rating: 5, text: "We've used Comfort Pro for 8 years running — annual maintenance and two emergency calls. Always reliable.", time: "4 months ago" },
];

const MOCK_SCHEMA_ORG = {
  "@context": "https://schema.org",
  "@type": "HVACBusiness",
  name: "Comfort Pro HVAC",
  address: { "@type": "PostalAddress", addressLocality: "Austin", addressRegion: "TX" },
};

function makeContent(overrides: Partial<SiteContent> & { site_config: SiteContent["site_config"]; business: SiteContent["business"]; hero: SiteContent["hero"] }): SiteContent {
  return {
    business: overrides.business,
    hero: overrides.hero,
    services: overrides.services ?? [],
    about: overrides.about ?? { story: "", trust_points: [], certifications: [] },
    reviews: overrides.reviews ?? { reviews: [], aggregate_line: "" },
    faq: overrides.faq ?? [],
    seo: overrides.seo ?? { title: "", description: "", keywords: [] },
    aeo_signals: overrides.aeo_signals ?? {
      local_business_type: "",
      primary_category: "",
      secondary_categories: [],
      area_served: [],
    },
    schema_org: overrides.schema_org ?? {},
    site_config: overrides.site_config,
    status: overrides.status ?? "preview_live",
    slug: overrides.slug ?? "mock-preview",
    meta_title: overrides.meta_title ?? "",
    meta_description: overrides.meta_description ?? "",
    lighthouse_score: overrides.lighthouse_score ?? 95,
  };
}

const MOCK_DATA: Record<string, SiteContent> = {
  "hvac-reliable-blue": makeContent({
    business: { ...MOCK_BUSINESS, business_name: "Comfort Pro HVAC", trade: "hvac", phone: "(512) 555-0199" },
    hero: {
      headline: "Stay Comfortable Austin",
      subheadline: "Same-day HVAC service for homes that need reliable heating and cooling — no runarounds, no surprises.",
      trust_bar: ["Licensed & Insured", "EPA Certified", "Background Checked"],
      cta_primary: "Call Now",
      cta_primary_url: "tel:+15125550199",
      cta_secondary: "View Services",
      cta_secondary_url: "#services",
    },
    services: [
      { icon: "thermometer", title: "AC Repair & Install", description: "Same-day diagnostics and repair. New unit installation with 10-year warranty.", cta_text: "Get AC Help" },
      { icon: "flame", title: "Heating Services", description: "Furnace repair, heat pump service, and full heating system replacement.", cta_text: "Heating Help" },
      { icon: "wind", title: "Ductwork & Indoor Air", description: "Duct sealing, air filtration, and humidity control for healthier air.", cta_text: "Improve Air Quality" },
      { icon: "settings", title: "Maintenance Plans", description: "Annual tune-ups, priority scheduling, and 15% off all repairs.", cta_text: "See Plans" },
    ],
    about: {
      story: "Comfort Pro started in 2009 when founder Mike Hartwell got tired of watching Austin homeowners get hit with surprise charges and delayed service. He built this company on a simple promise: show up when we say we will, fix it right the first time, and charge a fair price. Fifteen years and 5,000+ homes later, that promise still drives everything we do.",
      trust_points: ["15+ years serving Austin homeowners", "4.9-star rating across 342 reviews", "Same-day emergency service available", "EPA-certified and background-checked technicians"],
      certifications: ["EPA 608 Certified", "NATE Certified", "BBB A+ Rating"],
    },
    reviews: {
      reviews: MOCK_REVIEWS,
      aggregate_line: "4.9 average from 342 reviews",
    },
    faq: [
      { question: "How fast can you get here?", answer: "For emergencies, we typically arrive within 2 hours. Standard service calls are scheduled same-day or next business day." },
      { question: "Do you charge for estimates?", answer: "Never. All estimates are free and come with a written quote — no hidden fees, no pressure." },
      { question: "What brands do you service?", answer: "We service all major HVAC brands including Carrier, Trane, Lennox, Rheem, Goodman, and more." },
      { question: "Do you offer financing?", answer: "Yes. We offer 0% APR financing for up to 60 months on qualifying installations." },
    ],
    seo: { title: "Comfort Pro HVAC — Austin's Most Trusted HVAC Company", description: "Same-day HVAC repair and installation in Austin. 4.9-star rated. Licensed, insured, EPA certified. Call (512) 555-0199.", keywords: ["hvac austin", "ac repair austin", "heating repair austin"] },
    aeo_signals: { local_business_type: "HVACContractor", primary_category: "HVAC Repair", secondary_categories: ["AC Installation", "Furnace Repair", "Duct Cleaning"], area_served: ["Austin", "Round Rock", "Cedar Park", "Pflugerville"] },
    schema_org: MOCK_SCHEMA_ORG,
    site_config: { template_id: "hvac-reliable-blue", trade: "hvac", theme: { primary: "#1e40af", accent: "#60a5fa", font_display: "Outfit", font_body: "Inter" } },
    slug: "comfort-pro-hvac-austin",
    meta_title: "Comfort Pro HVAC — Austin's Most Trusted HVAC Company",
    meta_description: "Same-day HVAC repair and installation in Austin. Call (512) 555-0199.",
  }),

  "plumbing-trustworthy-navy": makeContent({
    business: { ...MOCK_BUSINESS, business_name: "PipeShield Plumbing", trade: "plumbing", city: "Denver", state: "CO", phone: "(303) 555-0177" },
    hero: {
      headline: "Denver Trusts PipeShield",
      subheadline: "24/7 emergency plumbing — burst pipes, clogs, leaks. Licensed master plumbers who answer the phone.",
      trust_bar: ["Licensed & Insured", "Master Plumber Certified", "Background Checked"],
      cta_primary: "24/7 Emergency Call",
      cta_primary_url: "tel:+13035550177",
      cta_secondary: "See Our Services",
      cta_secondary_url: "#services",
    },
    services: [
      { icon: "droplet", title: "Emergency Repairs", description: "Burst pipes, sewer backups, gas leaks — we're here 24/7 with no overtime charges.", cta_text: "Call Now" },
      { icon: "wrench", title: "Drain Cleaning", description: "Kitchen, bathroom, and main sewer line clogs cleared fast with camera inspection.", cta_text: "Clear Drains" },
      { icon: "thermometer", title: "Water Heater Service", description: "Tank and tankless replacement, repair, and annual flushing to extend life.", cta_text: "Water Heater Help" },
      { icon: "home", title: "Remodel Plumbing", description: "Kitchen and bath remodels — fixtures, pipe rerouting, code-compliant installation.", cta_text: "Start Remodel" },
    ],
    about: {
      story: "PipeShield was founded by master plumber Carlos Vega in 2004 after a decade of watching Denver homeowners get gouged by dishonest operators. He built this company on transparency — upfront pricing, honest diagnostics, and work that meets code the first time. Twenty years and over 10,000 jobs later, we're still Denver's most-reviewed plumbing company.",
      trust_points: ["20+ years serving Denver", "Master Plumber certified", "4.8-star rating from 1,200+ reviews", "No overtime charges for emergencies"],
      certifications: ["Master Plumber License", "BBB A+ Rating", "EPA Lead-Safe Certified"],
    },
    reviews: {
      reviews: MOCK_REVIEWS.map((r, i) => ({
        ...r,
        author: ["Amanda P.", "Rick D.", "Natalie S.", "James C.", "Susan F."][i],
        text: [
          "Pipe over a weekend and they answered immediately. Fixed in 45 minutes. Amazing.",
          "Most honest plumber I've ever hired. Showed me the camera feed, explained everything, didn't upsell.",
          "Remodeled our master bath — flawless work, on budget, on time. Highly recommend.",
          "Clogged kitchen drain cleared in 30 minutes. Fair price, clean work area. Would call again.",
          "Been using PipeShield for annual maintenance for 6 years. They always show up on time.",
        ][i],
      })),
      aggregate_line: "4.8 average from 1,200 reviews",
    },
    faq: [
      { question: "Do you charge overtime for emergency calls?", answer: "Never. Our 24/7 emergency rate is the same as our standard rate — no surprise upcharges." },
      { question: "How quickly can you respond to a burst pipe?", answer: "Average response time under 60 minutes for emergencies in the Denver metro area." },
      { question: "Can you fix both tank and tankless water heaters?", answer: "Yes. We service and install all water heater types — gas, electric, tank, and tankless." },
    ],
    seo: { title: "PipeShield Plumbing — Denver's Most Trusted Plumber", description: "24/7 emergency plumbing in Denver. No overtime charges. Master Plumber certified. Call (303) 555-0177.", keywords: ["plumber denver", "emergency plumber", "drain cleaning denver"] },
    aeo_signals: { local_business_type: "Plumber", primary_category: "Plumbing", secondary_categories: ["Drain Cleaning", "Water Heater", "Remodel Plumbing"], area_served: ["Denver", "Aurora", "Lakewood", "Littleton"] },
    schema_org: { "@context": "https://schema.org", "@type": "Plumber", name: "PipeShield Plumbing" },
    site_config: { template_id: "plumbing-trustworthy-navy", trade: "plumbing", theme: { primary: "#1e3a5f", accent: "#3b82f6", font_display: "Outfit", font_body: "Inter" } },
    slug: "papeshield-plumbing-denver",
    meta_title: "PipeShield Plumbing — Denver's Most Trusted Plumber",
    meta_description: "24/7 emergency plumbing in Denver. Call (303) 555-0177.",
  }),

  "electrical-sharp-gold": makeContent({
    business: { ...MOCK_BUSINESS, business_name: "VoltPro Electric", trade: "electrical", city: "Phoenix", state: "AZ", phone: "(602) 555-0133" },
    hero: {
      headline: "Phoenix's Brightest Electricians",
      subheadline: "Same-day electrical service — sparking outlets, panel upgrades, EV charger installs. Licensed, insured, and on time.",
      trust_bar: ["Licensed & Insured", "NEC Compliant", "Background Checked"],
      cta_primary: "Call for Service",
      cta_primary_url: "tel:+16025550133",
      cta_secondary: "Our Services",
      cta_secondary_url: "#services",
    },
    services: [
      { icon: "zap", title: "Electrical Repair", description: "Outlet sparking? Flickering lights? We diagnose and fix it safely, same day.", cta_text: "Get Repair" },
      { icon: "shield", title: "Panel Upgrades", description: "200A panel upgrades for modern homes. Code-compliant, permitted, inspected.", cta_text: "Upgrade Panel" },
      { icon: "ev", title: "EV Charger Install", description: "Level 2 charger installation for Tesla, Ford, and all EV makes.", cta_text: "Install Charger" },
      { icon: "lightbulb", title: "Lighting & Fans", description: "Recessed lighting, ceiling fans, and smart lighting setups installed right.", cta_text: "Lighting Help" },
    ],
    about: {
      story: "VoltPro was born in 2012 when master electrician DeShawn Carter saw too many Phoenix homes running on outdated 100A panels with aluminum wiring. He made it his mission to bring every home up to modern safety standards — one clean, code-compliant job at a time. With 8,000+ homes powered and a 4.9-star reputation, VoltPro is Phoenix's most trusted electrical team.",
      trust_points: ["12+ years in Phoenix", "NEC code-compliant on every job", "4.9-star rating from 600+ reviews", "Same-day service available"],
      certifications: ["Master Electrician License", "NEC Certified", "BBB A+ Rating"],
    },
    reviews: {
      reviews: MOCK_REVIEWS.map((r, i) => ({
        ...r,
        author: ["Mark T.", "Lisa H.", "Debbie W.", "Kevin R.", "Yolanda M."][i],
        text: [
          "Replaced our 1970s panel in one day. Clean work, walked us through everything, zero issues at inspection.",
          "Installed our Tesla charger perfectly. Even helped us set up the app scheduling. Top-notch.",
          "Fixed a dangerous wiring situation the previous owner left. So glad we called VoltPro.",
          "Fast, honest, and affordable. They didn't try to sell us anything we didn't need.",
          "Annual electrical inspection is worth every penny. Caught a loose connection before it became a fire hazard.",
        ][i],
      })),
      aggregate_line: "4.9 average from 600 reviews",
    },
    faq: [
      { question: "Is a panel upgrade worth it?", answer: "If your home has a 100A panel or aluminum wiring, yes — modern appliances and EV chargers demand 200A. We provide free assessments." },
      { question: "Can you install EV chargers?", answer: "Absolutely. We install Level 2 chargers for all EV makes — Tesla, Ford, Chevy, and more." },
      { question: "Do you handle permits?", answer: "Yes. We pull all required permits and schedule inspections. You don't have to deal with any paperwork." },
    ],
    seo: { title: "VoltPro Electric — Phoenix's Most Trusted Electrician", description: "Same-day electrical service in Phoenix. Panel upgrades, EV chargers, repairs. Call (602) 555-0133.", keywords: ["electrician phoenix", "panel upgrade", "ev charger install phoenix"] },
    aeo_signals: { local_business_type: "Electrician", primary_category: "Electrical Repair", secondary_categories: ["Panel Upgrade", "EV Charger Install", "Lighting"], area_served: ["Phoenix", "Scottsdale", "Tempe", "Mesa"] },
    schema_org: { "@context": "https://schema.org", "@type": "Electrician", name: "VoltPro Electric" },
    site_config: { template_id: "electrical-sharp-gold", trade: "electrical", theme: { primary: "#78350f", accent: "#d97706", font_display: "Outfit", font_body: "Inter" } },
    slug: "voltpro-electric-phoenix",
    meta_title: "VoltPro Electric — Phoenix's Most Trusted Electrician",
    meta_description: "Same-day electrical service in Phoenix. Call (602) 555-0133.",
  }),

  "roofing-bold-copper": makeContent({
    business: { ...MOCK_BUSINESS, business_name: "Summit Roofing Co", trade: "roofing", city: "Nashville", state: "TN", phone: "(615) 555-0144" },
    hero: {
      headline: "Protecting Nashville Roofs",
      subheadline: "Storm damage? Free inspection within 24 hours. GAF-certified roofers with 30 years of experience standing behind every nail.",
      trust_bar: ["Licensed & Insured", "GAF Certified", "Worker's Comp Covered"],
      cta_primary: "Free Inspection",
      cta_primary_url: "tel:+16155550144",
      cta_secondary: "See Our Work",
      cta_secondary_url: "#services",
    },
    services: [
      { icon: "cloud-rain", title: "Storm Damage Repair", description: "Wind, hail, and storm damage — inspected free, repaired fast, insurance claim assistance.", cta_text: "Free Inspection" },
      { icon: "home", title: "Full Roof Replacement", description: "Asphalt, metal, and architectural shingle installations with manufacturer warranty.", cta_text: "Get Quote" },
      { icon: "search", title: "Roof Inspections", description: "Detailed 21-point inspection with photo report — free for Nashville homeowners.", cta_text: "Book Inspection" },
      { icon: "shield", title: "Maintenance Plans", description: "Annual inspections, gutter cleaning, and preventative maintenance to extend roof life.", cta_text: "See Plans" },
    ],
    about: {
      story: "Summit Roofing started in 1994 when third-generation roofer Jake Dalton moved to Nashville and saw homeowners getting fleeced by storm-chasing contractors. He built this company on a simple principle: inspect for free, quote honestly, and warranty everything. Thirty years later, we've protected over 2,500 Nashville homes and earned more 5-star reviews than any roofer in the state.",
      trust_points: ["30+ years protecting Nashville homes", "GAF Master Elite Certification (top 2% nationally)", "4.8-star rating from 890+ reviews", "Free 21-point inspections"],
      certifications: ["GAF Master Elite", "BBB A+ Rating", "Worker's Comp Certified"],
    },
    reviews: {
      reviews: MOCK_REVIEWS.map((r, i) => ({
        ...r,
        author: ["Patty N.", "Robert G.", "Clara J.", "Mike S.", "Angela B."][i],
        text: [
          "After the April storms, Summit was the only roofer who actually showed up for the free inspection. Found 3 spots the insurance adjuster missed.",
          "Complete roof replacement done in 2 days. Clean crew, great communication, warranty that actually means something.",
          "The 21-point inspection caught damage we didn't even know about. Saved us from a future leak for sure.",
          "Honest quote, no pressure. They even helped us navigate the insurance claim. Stand-up company.",
          "Annual maintenance plan is worth every penny. They caught a small issue before it became a big one.",
        ][i],
      })),
      aggregate_line: "4.8 average from 890 reviews",
    },
    faq: [
      { question: "How do I know if I need a new roof?", answer: "Our free 21-point inspection gives you a clear answer with photos — no pressure, no sales pitch. Just facts." },
      { question: "Do you help with insurance claims?", answer: "Yes. We document all damage with photos, meet adjusters on-site, and handle the paperwork. Most claims are approved the first time." },
      { question: "What's the warranty?", answer: "GAF Master Elite installs come with a 25-year manufacturer warranty plus our 10-year workmanship guarantee." },
    ],
    seo: { title: "Summit Roofing Co — Nashville's Most Trusted Roofer", description: "Free roof inspections in Nashville. GAF-certified, 30+ years experience. Call (615) 555-0144.", keywords: ["roofer nashville", "roof repair nashville", "storm damage roof"] },
    aeo_signals: { local_business_type: "RoofingContractor", primary_category: "Roofing", secondary_categories: ["Storm Damage", "Roof Replacement", "Gutters"], area_served: ["Nashville", "Franklin", "Brentwood", "Murfreesboro"] },
    schema_org: { "@context": "https://schema.org", "@type": "RoofingContractor", name: "Summit Roofing Co" },
    site_config: { template_id: "roofing-bold-copper", trade: "roofing", theme: { primary: "#7c2d12", accent: "#ea580c", font_display: "Outfit", font_body: "Inter" } },
    slug: "summit-roofing-nashville",
    meta_title: "Summit Roofing Co — Nashville's Most Trusted Roofer",
    meta_description: "Free roof inspections in Nashville. Call (615) 555-0144.",
  }),

  "painting-clean-minimal": makeContent({
    business: { ...MOCK_BUSINESS, business_name: "HueCraft Painting", trade: "painting", city: "Portland", state: "OR", phone: "(503) 555-0166" },
    hero: {
      headline: "Portland's Paint Perfectionists",
      subheadline: "Interior and exterior painting with a free color consultation. Clean lines, lasting finishes, zero mess.",
      trust_bar: ["Licensed & Insured", "Lead-Safe Certified", "Satisfaction Guaranteed"],
      cta_primary: "Free Consultation",
      cta_primary_url: "tel:+15035550166",
      cta_secondary: "See Our Work",
      cta_secondary_url: "#services",
    },
    services: [
      { icon: "palette", title: "Interior Painting", description: "Walls, trim, cabinets — flawless coverage with premium paints and meticulous prep.", cta_text: "Interior Quote" },
      { icon: "sun", title: "Exterior Painting", description: "Weather-resistant coatings that protect your home and boost curb appeal.", cta_text: "Exterior Quote" },
      { icon: "frame", title: "Cabinet Refinishing", description: "Transform kitchen cabinets without replacement — savings of 50%+ compared to new cabinets.", cta_text: "Refinish Cabinets" },
      { icon: "ruler", title: "Color Consultation", description: "Free professional color consultation with every project. See your space before we paint.", cta_text: "Book Consult" },
    ],
    about: {
      story: "HueCraft was founded by painter and color consultant Yuki Tanaka in 2012, built on the belief that a great paint job starts long before the first brush stroke. Our prep-first approach means we sand, prime, and patch everything before a single drop of color goes on the wall. The result? Finishes that last 8-10 years and zero call-backs in 12 years of business.",
      trust_points: ["12+ years transforming Portland homes", "Lead-Safe Certified for pre-1978 homes", "4.9-star rating from 480+ reviews", "Free color consultation with every project"],
      certifications: ["Lead-Safe Certified", "Sherwin-Williams Certified Applicator", "BBB A+ Rating"],
    },
    reviews: {
      reviews: MOCK_REVIEWS.map((r, i) => ({
        ...r,
        author: ["Emma C.", "Jordan P.", "Rachel M.", "Todd L.", "Priya S."][i],
        text: [
          "The color consultation alone was worth it. Yuki helped us see the actual swatches in our lighting. Game-changer.",
          "Kitchen cabinets went from dated oak to modern navy — without replacing them. Saved us $8,000.",
          "Cleanest painters I've ever hired. Zero paint on the floors, zero drips on trim. Impressive.",
          "Exterior painting was done in 3 days. Looked great immediately and still looks fresh 2 years later.",
          "They patched holes we didn't even think were fixable. The walls look better than new.",
        ][i],
      })),
      aggregate_line: "4.9 average from 480 reviews",
    },
    faq: [
      { question: "How much does interior painting cost?", answer: "It depends on square footage, trim, ceiling height, and paint quality. We provide a free in-home estimate — no guessing." },
      { question: "Do you help choose colors?", answer: "Every project includes a free professional color consultation. We bring samples and test them in your actual lighting." },
      { question: "How long does a typical job take?", answer: "Most interiors take 3-5 days. Exteriors take 5-7 days depending on weather and surface condition." },
    ],
    seo: { title: "HueCraft Painting — Portland's Painter With a Free Color Consultation", description: "Interior & exterior painting in Portland. Free color consultation. Lead-Safe Certified. Call (503) 555-0166.", keywords: ["painter portland", "interior painting oregon", "cabinet refinishing portland"] },
    aeo_signals: { local_business_type: "Painter", primary_category: "Painting", secondary_categories: ["Interior Painting", "Exterior Painting", "Cabinet Refinishing"], area_served: ["Portland", "Beaverton", "Lake Oswego", "Tigard"] },
    schema_org: { "@context": "https://schema.org", "@type": "Painter", name: "HueCraft Painting" },
    site_config: { template_id: "painting-clean-minimal", trade: "painting", theme: { primary: "#6b21a8", accent: "#a855f7", font_display: "Outfit", font_body: "Inter" } },
    slug: "huecraft-painting-portland",
    meta_title: "HueCraft Painting — Portland's Painter With a Free Color Consultation",
    meta_description: "Interior & exterior painting in Portland. Call (503) 555-0166.",
  }),

  "landscaping-earthy-green": makeContent({
    business: { ...MOCK_BUSINESS, business_name: "GreenScape Landscaping", trade: "landscaping", city: "Charlotte", state: "NC", phone: "(704) 555-0188" },
    hero: {
      headline: "Charlotte's Finest Yards Start Here",
      subheadline: "Landscape design, lawn care, and outdoor living spaces — premium craftsmanship for homes that deserve to stand out.",
      trust_bar: ["Licensed & Insured", "Green Industry Certified", "Satisfaction Guaranteed"],
      cta_primary: "Free Estimate",
      cta_primary_url: "tel:+17045550188",
      cta_secondary: "Our Services",
      cta_secondary_url: "#services",
    },
    services: [
      { icon: "tree-pine", title: "Landscape Design", description: "Custom designs that blend native plants, hardscaping, and outdoor living spaces.", cta_text: "Design Yours" },
      { icon: "leaf", title: "Lawn Care & Maintenance", description: "Weekly mowing, seasonal cleanups, fertilization, and weed control packages.", cta_text: "Get Lawn Plan" },
      { icon: "fence", title: "Hardscaping", description: "Patios, walkways, retaining walls, and fire pits built to last.", cta_text: "Hardscape Quote" },
      { icon: "sprinkler", title: "Irrigation Systems", description: "Smart irrigation installs and repairs — efficient, code-compliant, saving water.", cta_text: "Irrigation Help" },
    ],
    about: {
      story: "GreenScape was founded by landscape architect Ben Morales in 2006 after years of watching Charlotte homeowners pour money into generic yard work that never delivered lasting results. He combined his design training with horticultural expertise to create outdoor spaces that actually thrive in the Carolina climate. Eighteen years later, we maintain over 4,000 properties and have designed hundreds of outdoor living spaces.",
      trust_points: ["18+ years beautifying Charlotte", "Green Industry Certified team", "4.8-star rating from 550+ reviews", "Free estimates on every project"],
      certifications: ["Green Industry Certified", "NC Landscape Contractor License", "BBB A+ Rating"],
    },
    reviews: {
      reviews: MOCK_REVIEWS.map((r, i) => ({
        ...r,
        author: ["Christine V.", "Derek A.", "Monica B.", "Brian H.", "Theresa K."][i],
        text: [
          "Ben designed our backyard oasis — fire pit, patio, and native plantings. It looks like a magazine cover every season.",
          "Weekly lawn care is always on time, always clean. Our lawn has never looked this good.",
          "Retaining wall and walkway were done in under a week. Solid craftsmanship, fair price.",
          "Switched from another lawn company — night and day difference. GreenScape actually cares about the details.",
          "Irrigation repair saved our garden during the summer drought. Fast, knowledgeable, honest pricing.",
        ][i],
      })),
      aggregate_line: "4.8 average from 550 reviews",
    },
    faq: [
      { question: "How much does landscape design cost?", answer: "Basic design starts with a free on-site consultation. Full design plans vary by scope — we'll give you a clear quote before any work starts." },
      { question: "Do you offer lawn maintenance contracts?", answer: "Yes. Weekly, bi-weekly, and seasonal packages. All include mowing, edging, blowing, and seasonal fertilization." },
      { question: "What's included in a free estimate?", answer: "An on-site visit, measurements, photos, and a detailed written proposal — no obligation, no pressure." },
    ],
    seo: { title: "GreenScape Landscaping — Charlotte's Premier Outdoor Living Company", description: "Landscape design, lawn care, and hardscaping in Charlotte. Free estimates. Call (704) 555-0188.", keywords: ["landscaping charlotte", "lawn care charlotte", "hardscaping design nc"] },
    aeo_signals: { local_business_type: "Landscaper", primary_category: "Landscaping", secondary_categories: ["Lawn Care", "Hardscaping", "Irrigation"], area_served: ["Charlotte", "Matthews", "Huntersville", "Fort Mill"] },
    schema_org: { "@context": "https://schema.org", "@type": "Landscaper", name: "GreenScape Landscaping" },
    site_config: { template_id: "landscaping-earthy-green", trade: "landscaping", theme: { primary: "#14532d", accent: "#22c55e", font_display: "Outfit", font_body: "Inter" } },
    slug: "greenscape-landscaping-charlotte",
    meta_title: "GreenScape Landscaping — Charlotte's Premier Outdoor Living Company",
    meta_description: "Landscape design and lawn care in Charlotte. Call (704) 555-0188.",
  }),
};

export default MOCK_DATA;