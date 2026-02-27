# Reliant AI — SEO & AI Search Action Plan

> Tasks to complete after deploying the site. Work through these in order.

---

## 1. Google Business Profile (HIGH PRIORITY)

- Go to https://business.google.com
- Create a profile for "Reliant AI"
- Set category: **Web Designer**
- Add address: Houston, TX 77002
- Add phone: (832) 947-7028
- Add website: https://reliantai.org
- Upload photos of your work (screenshots of client sites)
- Once created, add the profile URL to the `sameAs` array in `index.html` JSON-LD schema

---

## 2. Google Search Console

- Go to https://search.google.com/search-console
- Add property: `https://reliantai.org`
- Verify via DNS or HTML file upload
- Submit sitemap: `https://reliantai.org/sitemap.xml`
- Click "Request Indexing" on the main URL
- Monitor for crawl errors weekly

---

## 3. Analytics Setup

Replace placeholder IDs in `index.html`:

- **Google Analytics 4**: Create at https://analytics.google.com → replace `G-XXXXXXXXXX`
- **Meta Pixel**: Create at https://business.facebook.com/events_manager → replace `XXXXXXXXXXXXXXX`
- **Microsoft Clarity**: Create at https://clarity.microsoft.com → replace `XXXXXXXXXX`

---

## 4. Directory Listings (AI Search Visibility)

AI models (ChatGPT, Perplexity, Google AI Overview) heavily weight these directories when recommending agencies. Create profiles on:

| Directory | URL | Priority |
|-----------|-----|----------|
| Clutch.co | https://clutch.co/developers/apply | HIGH |
| DesignRush | https://www.designrush.com/agency/submit | HIGH |
| UpCity | https://upcity.com/for-providers | HIGH |
| GoodFirms | https://www.goodfirms.co/add-your-company | MEDIUM |
| Expertise.com | https://www.expertise.com (auto-indexed) | MEDIUM |
| Houston Chamber | https://www.houston.org/membership | MEDIUM |
| BBB | https://www.bbb.org/get-accredited | MEDIUM |
| Yelp | https://biz.yelp.com/signup | LOW |

---

## 5. Content Marketing (Long-term SEO)

Publish blog posts targeting these long-tail keywords:

1. "Best website design for metal fabrication companies in Houston"
2. "How much does a website cost for an oilfield services company?"
3. "HIPAA-compliant website design for Houston medical practices"
4. "Why HVAC companies in Houston need a custom website"
5. "React vs WordPress: Which is better for small business websites?"

Each post should be 1,500+ words, include internal links to your services section, and have a CTA to the contact form.

> Note: This requires adding a blog/content section to the site or using an external platform (Medium, LinkedIn articles) that links back.

---

## 6. Backlink Strategy

Reach out for backlinks from:

- **Houston Chamber of Commerce** — member directory link
- **BBB** — accredited business listing
- **Local news** — pitch a story about a Houston tech entrepreneur
- **Client websites** — ask clients to add "Website by Reliant AI" in their footer
- **Industry blogs** — guest posts on metal fabrication, oilfield, or HVAC industry sites

---

## 7. Social Profiles

Create and link these (add URLs to `sameAs` in `index.html`):

- LinkedIn company page
- Twitter/X profile
- Instagram (portfolio showcase)
- YouTube (if you create video content)

---

## 8. Scheduling Link (Optional)

If you set up Calendly or Cal.com:

1. Create a free account
2. Set up a "30-Minute Consultation" event
3. Share the URL with me and I'll embed it in the "Book a Call" section

---

## 9. Ongoing Monitoring

- **Weekly**: Check Google Search Console for errors and impressions
- **Monthly**: Review Analytics for traffic sources and conversion rates
- **Quarterly**: Update testimonials and case study stats in the code
- **Annually**: Refresh schema.org dates, review pricing, update copyright year

---

## Code Changes Still Needed

These require specific values from you:

| Item | What I need | Where it goes |
|------|-------------|---------------|
| GA4 ID | `G-XXXXXXXXXX` | `index.html` (2 places) |
| Meta Pixel ID | 15-digit number | `index.html` |
| Clarity ID | 10-char string | `index.html` |
| Google Business URL | Profile URL | `index.html` sameAs array |
| Calendly URL | Scheduling link | Contact section embed |
