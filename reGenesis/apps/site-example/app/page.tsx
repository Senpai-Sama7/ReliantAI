"use client";

import { useEffect, useMemo, useState } from "react";
import { SkipLink, Button, Section, Nav } from "@cyberarchitect/ui";
import { initLenis, syncWithScrollTrigger } from "@cyberarchitect/scroll";

const defaultBrief = {
  name: "Sunrise Coffee Co.",
  summary: "Neighborhood coffee shop focused on warm vibes and weekend events.",
  audience: "Local coffee lovers, remote workers, and weekend brunch visitors.",
  tone: "Friendly and welcoming with a hint of playful energy.",
  palette: "Sunrise (amber + soft teal)",
};

export default function Page(){
  const [brief, setBrief] = useState(defaultBrief);
  const [backupUrl, setBackupUrl] = useState("https://example.com");
  const [status, setStatus] = useState<string | null>(null);
  const [backupStatus, setBackupStatus] = useState<string | null>(null);

  useEffect(() => {
    const lenis = initLenis({ smooth: true, duration: 1.2 });
    syncWithScrollTrigger(lenis);
  }, []);

  const briefPreview = useMemo(() => {
    return `We heard you: a ${brief.tone.toLowerCase()} brand voice for ${brief.name}, serving ${brief.audience}. We'll ship a site with a ${brief.palette} palette plus homepage, menu/services, reviews, and contact CTA.`;
  }, [brief]);

  function handleBriefSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus("Thanks! We saved your Brand Brief. Click \"Generate my site\" to see a live preview in minutes.");
  }

  function handleBackupSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBackupStatus("Backup scheduled. We'll capture a pixel-perfect offline copy and email your download link.");
  }

  return (
    <>
      <SkipLink />
      <header className="site-header" aria-label="Site header">
        <Nav
          items={[
            { href: "#hero", label: "Overview" },
            { href: "#how-it-works", label: "How it works" },
            { href: "#brand-brief", label: "Brand Brief" },
            { href: "#backup", label: "Backup" },
            { href: "#hosting", label: "Hosting" },
          ]}
        />
        <div className="header-actions">
          <Button onClick={() => window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" })}>
            Talk to us
          </Button>
        </div>
      </header>
      <main id="main">
        <Section id="hero" aria-labelledby="h1" className="hero">
          <p className="eyebrow">AI website studio • Backups included</p>
          <h1 id="h1">Launch-ready sites for non-technical teams</h1>
          <p className="lede">
            Describe your business in plain language, pick a color vibe, and we generate, host, and back up your site.
            No setup, no code, no waiting.
          </p>
          <div className="cta-row">
            <Button onClick={() => document.getElementById("brand-brief")?.scrollIntoView({ behavior: "smooth" })}>
              Start with a Brand Brief
            </Button>
            <Button className="ghost" onClick={() => document.getElementById("backup")?.scrollIntoView({ behavior: "smooth" })}>
              Backup my existing site
            </Button>
          </div>
          <div className="pill-row">
            <span className="pill">Includes 7-day free trial</span>
            <span className="pill">One-click hosting & domain setup</span>
            <span className="pill">Pixel-perfect offline backups</span>
          </div>
        </Section>

        <Section id="how-it-works" aria-labelledby="how-heading" className="grid two-cols">
          <div>
            <h2 id="how-heading">How reGenesis works for you</h2>
            <ol className="steps">
              <li><strong>Share your Brand Brief.</strong> Plain-language prompts capture your vibe, colors, and goals.</li>
              <li><strong>See a live preview.</strong> We generate a responsive, SEO-ready site with modern design defaults.</li>
              <li><strong>Deploy instantly.</strong> We can host it for you, connect your domain, and keep weekly backups.</li>
            </ol>
            <p className="muted">Prefer white-glove? We'll do it for you—just drop a few sentences and our team handles the rest.</p>
          </div>
          <div className="card">
            <p className="eyebrow">New site or refresh</p>
            <h3>Fast launch package</h3>
            <ul className="checklist">
              <li>AI-written copy + curated images</li>
              <li>Mobile-first, accessibility-checked layout</li>
              <li>SEO scan with title/meta suggestions</li>
              <li>One-click publish to managed hosting</li>
            </ul>
            <Button onClick={() => document.getElementById("brand-brief")?.scrollIntoView({ behavior: "smooth" })}>
              Build my site
            </Button>
          </div>
        </Section>

        <Section id="brand-brief" aria-labelledby="brief-heading" className="card">
          <p className="eyebrow">Create without code</p>
          <h2 id="brief-heading">Brand Brief (plain language)</h2>
          <p className="muted">Drop a few sentences and we turn it into a ready-to-publish site. We save this as a template for future updates.</p>
          <form className="form" onSubmit={handleBriefSubmit}>
            <label>
              Business or project name
              <input
                value={brief.name}
                onChange={e => setBrief({ ...brief, name: e.target.value })}
                placeholder="Your brand name"
                required
              />
            </label>
            <label>
              Elevator pitch
              <textarea
                value={brief.summary}
                onChange={e => setBrief({ ...brief, summary: e.target.value })}
                rows={3}
                placeholder="What you do, who you serve, and what makes you special"
                required
              />
            </label>
            <label>
              Audience & goals
              <textarea
                value={brief.audience}
                onChange={e => setBrief({ ...brief, audience: e.target.value })}
                rows={2}
                placeholder="Target customers and the action you want them to take"
              />
            </label>
            <div className="grid two-cols">
              <label>
                Brand voice
                <input
                  value={brief.tone}
                  onChange={e => setBrief({ ...brief, tone: e.target.value })}
                  placeholder="Friendly, bold, minimalist, playful, etc."
                />
              </label>
              <label>
                Color direction
                <input
                  value={brief.palette}
                  onChange={e => setBrief({ ...brief, palette: e.target.value })}
                  placeholder="e.g., Midnight blue + coral accent"
                />
              </label>
            </div>
            <p className="preview" aria-live="polite">{briefPreview}</p>
            <div className="cta-row">
              <Button type="submit">Generate my site</Button>
              <Button
                className="ghost"
                type="button"
                onClick={() => setBrief(defaultBrief)}
              >
                Reset example
              </Button>
            </div>
          </form>
          {status && <div className="notice success" role="status">{status}</div>}
        </Section>

        <Section id="backup" aria-labelledby="backup-heading" className="card">
          <p className="eyebrow">Pixel-perfect capture</p>
          <h2 id="backup-heading">Backup my existing site</h2>
          <p className="muted">We archive every page, asset, and style so you always have an offline copy—great for compliance, migrations, or peace of mind.</p>
          <form className="form inline" onSubmit={handleBackupSubmit}>
            <label className="inline-label">
              Site URL
              <input
                value={backupUrl}
                onChange={e => setBackupUrl(e.target.value)}
                type="url"
                placeholder="https://yourdomain.com"
                required
              />
            </label>
            <label className="inline-label">
              Frequency
              <select>
                <option>One-time snapshot</option>
                <option>Weekly refresh</option>
                <option>Monthly refresh</option>
              </select>
            </label>
            <Button type="submit">Schedule backup</Button>
          </form>
          {backupStatus && <div className="notice" role="status">{backupStatus}</div>}
          <ul className="checklist compact">
            <li>Offline HTML + assets, plus manifest for integrity</li>
            <li>Ideal for migrations or investor due diligence</li>
            <li>Option to sync updates to your hosted version</li>
          </ul>
        </Section>

        <Section id="hosting" aria-labelledby="hosting-heading" className="grid two-cols">
          <div className="card">
            <p className="eyebrow">One-click live</p>
            <h3 id="hosting-heading">Hosting & domains handled</h3>
            <p className="muted">We deploy to managed hosting, wire up SSL, and point your custom domain. Choose monthly hosting or bundle a year free with launch.</p>
            <ul className="checklist compact">
              <li>Global CDN + uptime monitoring</li>
              <li>Automatic backups stored alongside your project</li>
              <li>DNS + domain concierge for non-technical teams</li>
            </ul>
            <Button onClick={() => document.getElementById("cta")?.scrollIntoView({ behavior: "smooth" })}>
              Bundle hosting with my build
            </Button>
          </div>
          <div className="card">
            <p className="eyebrow">Stay fresh</p>
            <h3>Continuous AI enhancements</h3>
            <p className="muted">We keep your site aligned to current design, accessibility, and SEO guidelines. Copy refreshes and meta checks are built in.</p>
            <ul className="checklist compact">
              <li>Model updates keep layouts modern</li>
              <li>Accessibility spot checks baked into previews</li>
              <li>SEO recommendations after each publish</li>
            </ul>
            <Button onClick={() => document.getElementById("how-it-works")?.scrollIntoView({ behavior: "smooth" })}>
              See how it works
            </Button>
          </div>
        </Section>

        <Section id="cta" aria-labelledby="cta-heading" className="card final">
          <h2 id="cta-heading">Ready to ship?</h2>
          <p className="lede">Tell us who you are and we'll handle the rest—generation, hosting, domain, and backups.</p>
          <div className="cta-row">
            <Button onClick={() => document.getElementById("brand-brief")?.scrollIntoView({ behavior: "smooth" })}>
              Start free trial
            </Button>
            <Button className="ghost" onClick={() => document.getElementById("backup")?.scrollIntoView({ behavior: "smooth" })}>
              Just need a backup
            </Button>
          </div>
          <p className="muted">Prefer a conversation? Email hello@regensis.ai with your Brand Brief and we'll set everything up.</p>
        </Section>

        <script
          dangerouslySetInnerHTML={{
            __html: `
        (function(){
          if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
          const io = new IntersectionObserver((entries) => {
            for (const e of entries) if (e.isIntersecting) e.target.classList.add('in-view');
          }, { threshold: 0.2 });
          document.querySelectorAll('.fade-in').forEach(el => io.observe(el));
        })();
      `,
          }}
        />
      </main>
    </>
  );
}
