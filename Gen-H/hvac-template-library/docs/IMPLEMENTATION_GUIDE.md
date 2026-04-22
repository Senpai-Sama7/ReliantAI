# HVAC TEMPLATE LIBRARY - IMPLEMENTATION GUIDE

## 🚀 QUICK START (Day 1)

### Step 1: Clone & Setup (30 mins)
```bash
# Clone repository
git clone https://github.com/yourusername/hvac-template-library.git
cd hvac-template-library

# Install dependencies
npm install

# Setup environment
cp .env.example .env
# Edit .env with your database credentials

# Start services
docker-compose up -d

# Initialize database
docker-compose exec postgres psql -U hvac_user -d hvac_templates \
  -f ./database/schema.sql

# Access CMS
open http://localhost:3000
```

### Step 2: Create First Company (20 mins)
```bash
# Via API
curl -X POST http://localhost:5000/api/companies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Smith HVAC",
    "slug": "smith-hvac",
    "email": "info@smithhvac.com",
    "phone": "+1-555-0123",
    "owner_name": "John Smith",
    "owner_email": "john@smithhvac.com",
    "business_type": "residential"
  }'
```

### Step 3: Deploy Template (15 mins)
```bash
# Execute deployment script
./scripts/deploy.sh \
  template-1-technical-elegance \
  [company-id-from-step-2] \
  smith-hvac.com \
  production

# Watch for completion
# Result: https://smith-hvac.com is LIVE! 🎉
```

---

## 📋 IMPLEMENTATION CHECKLIST

### Week 1: Foundation
- [ ] Clone repository
- [ ] Install all dependencies
- [ ] Configure .env file
- [ ] Start Docker containers
- [ ] Access CMS dashboard
- [ ] Test API endpoints
- [ ] Review database schema

### Week 2: Customization
- [ ] Review template code structure
- [ ] Customize shared components (if needed)
- [ ] Add company logo to assets
- [ ] Prepare team photos
- [ ] Define color schemes
- [ ] Create test customizations

### Week 3: Testing & QA
- [ ] Deploy test site
- [ ] Mobile responsiveness check
- [ ] Form submission testing
- [ ] 3D component testing (if enabled)
- [ ] Performance testing (Lighthouse)
- [ ] Analytics tracking verification
- [ ] Security audit

### Week 4: Launch
- [ ] Setup production domain
- [ ] Configure DNS records
- [ ] Deploy first real customer
- [ ] Monitor analytics
- [ ] Gather customer feedback
- [ ] Plan iterative improvements

---

## 💻 CODE EXAMPLES

### Example 1: Use Pre-built Calculator Component
```typescript
// pages/index.tsx
import { InteractiveCalculator } from '@shared/components/InteractiveCalculator';

export default function Home() {
  return (
    <div>
      <h1>Energy Calculator</h1>
      <InteractiveCalculator
        onCalculate={(cost) => {
          console.log('Estimated cost:', cost);
          // Send to form or analytics
        }}
      />
    </div>
  );
}
```

### Example 2: Create Custom Deployment
```typescript
// api-gateway/routes/deployments.ts
app.post('/api/deployments/custom', async (req, res) => {
  const { template_id, company_id, domain, custom_colors } = req.body;

  // Create deployment
  const deployment = await pool.query(
    'INSERT INTO deployments (template_id, company_id, domain, customizations) VALUES ($1, $2, $3, $4) RETURNING *',
    [template_id, company_id, domain, JSON.stringify(custom_colors)]
  );

  res.json({ success: true, data: deployment.rows[0] });
});
```

### Example 3: Add Analytics Tracking
```typescript
// shared/utils/analytics.ts
export const trackEvent = async (deploymentId: string, eventType: string, data: any) => {
  await fetch(`/api/analytics/${deploymentId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ event_type: eventType, event_data: data })
  });
};

// In component
import { trackEvent } from '@shared/utils/analytics';

export function ContactForm() {
  const handleSubmit = async (data) => {
    await trackEvent(deploymentId, 'contact_form_submit', data);
    // Submit form...
  };
}
```

### Example 4: Customize Colors Per Company
```typescript
// pages/[company]/index.tsx
export async function getServerSideProps(context) {
  const { company } = context.params;

  // Fetch company customizations
  const response = await fetch(
    `http://localhost:5000/api/deployments?company_id=${company}`
  );
  const deployment = await response.json();

  return {
    props: {
      colors: deployment.data[0]?.customizations?.colors,
    },
  };
}

export default function Home({ colors }) {
  return (
    <div style={{ '--primary-color': colors.primary } as any}>
      {/* Your site content */}
    </div>
  );
}
```

### Example 5: Use Before/After Component
```typescript
import { BeforeAfterSlider } from '@shared/components/BeforeAfterSlider';

export function ProjectShowcase() {
  return (
    <BeforeAfterSlider
      beforeImage="/images/project-before.jpg"
      afterImage="/images/project-after.jpg"
      beforeLabel="Before Upgrade"
      afterLabel="After Installation"
    />
  );
}
```

---

## 🔄 WORKFLOW: Template to Live Site

```
1. SELECT TEMPLATE
   ↓
   Choose from 4 frameworks via CMS
   ↓

2. REGISTER COMPANY
   ↓
   Input company details (name, location, services)
   ↓

3. APPLY CUSTOMIZATIONS
   ↓
   Upload logo, configure colors, add content
   ↓

4. PREVIEW
   ↓
   Review customized site at staging URL
   ↓

5. DEPLOY
   ↓
   Run deployment script
   ↓

6. GO LIVE
   ↓
   Site is live at custom domain
   ↓

7. MONITOR
   ↓
   Track analytics and performance
```

---

## 🎯 COMMON CUSTOMIZATIONS

### Change Primary Color
```bash
./scripts/customize.sh deploy-id company-id

# Modify customizations
{
  "primary_color": "#your-color"
}
```

### Add Custom Hero Image
```typescript
// Update deployment with custom content
{
  "custom_content": {
    "hero_image": "https://your-cdn.com/image.jpg",
    "hero_headline": "Welcome to Your Company"
  }
}
```

### Enable/Disable Features
```typescript
{
  "features_enabled": {
    "3d_viewer": true,
    "calculator": true,
    "before_after_slider": true,
    "testimonials": true
  }
}
```

### Add Team Members
```typescript
{
  "custom_content": {
    "team_members": [
      {
        "name": "John Doe",
        "role": "Lead Technician",
        "image": "https://..."
      }
    ]
  }
}
```

---

## 📊 MONITORING & ANALYTICS

### View Real-time Analytics
```bash
curl http://localhost:5000/api/deployments/[id]/analytics

# Response:
{
  "success": true,
  "data": [
    {
      "event_type": "page_view",
      "count": 1234,
      "unique_users": 456
    },
    {
      "event_type": "contact_form_submit",
      "count": 78,
      "unique_users": 75
    }
  ]
}
```

### Performance Metrics
```bash
# Run Lighthouse check
npx lighthouse https://site-url.com --output json

# Check response time
time curl https://site-url.com

# Monitor uptime
./scripts/monitor.sh admin@example.com
```

---

## 🚨 TROUBLESHOOTING

### Database Connection Failed
```bash
# Check PostgreSQL
docker-compose logs postgres

# Restart
docker-compose restart postgres

# Verify connection
docker-compose exec postgres psql -U hvac_user -d hvac_templates -c "SELECT 1;"
```

### API Not Responding
```bash
# Check API logs
docker-compose logs api

# Verify running
docker-compose ps

# Restart
docker-compose restart api
```

### Deployment Failed
```bash
# Check deployment logs
cat deployment.log

# Verify domain DNS
nslookup yourdomain.com

# Retry
./scripts/deploy.sh template-id company-id domain production
```

### Component Not Rendering
```bash
# Check browser console for errors
# Verify component import path
// Should be: import { Button } from '@shared/components/Button'

# Clear cache
rm -rf .next/
npm run build
```

---

## 📞 GETTING HELP

### Documentation Files
- `SETUP_GUIDE.md` - Complete setup instructions
- `API_DOCS.md` - API reference
- `TEMPLATES.md` - Template information
- `CUSTOMIZATION.md` - How to customize
- `DEPLOYMENT.md` - Deployment guide

### Online Resources
- API Docs: http://localhost:5000/api/docs
- CMS Dashboard: http://localhost:3000
- GitHub Repo: https://github.com/yourusername/hvac-template-library

### Common Issues & Solutions

**Q: How do I change colors?**
A: Use the customize API endpoint or CMS dashboard

**Q: Can I use my own domain?**
A: Yes, configure DNS and update deployment

**Q: How many deployments can it handle?**
A: 10,000+ with proper scaling

**Q: Can I modify templates?**
A: Yes, all code is yours to customize

**Q: What about SSL certificates?**
A: Automatic with Vercel/Netlify

---

## 🎓 NEXT STEPS

1. **Today**: Setup and get first template running
2. **This Week**: Deploy test customer site
3. **Next Week**: Optimize based on feedback
4. **Next Month**: Launch multiple customer sites
5. **Quarter**: Scale operations and add new templates

---

## 💰 ROI METRICS TO TRACK

- **Time per deployment**: Target < 30 minutes
- **Customer acquisition cost**: Reduced by 70%
- **Site performance**: 90+ Lighthouse score
- **Customer satisfaction**: Track NPS
- **Revenue per template**: Calculate LTV

---

## ✅ LAUNCH CHECKLIST

Before going fully live:

- [ ] All 4 templates tested
- [ ] Database backed up
- [ ] Security audit completed
- [ ] Analytics tracking verified
- [ ] Support documentation ready
- [ ] Customer onboarding process created
- [ ] Payment/billing system integrated
- [ ] SSL certificates configured
- [ ] CDN configured
- [ ] Monitoring alerts setup

---

You're ready to deploy! 🚀

Start with: `docker-compose up -d`

Questions? Check the documentation or review the code comments.

**Total setup time: < 2 hours**
**Time to first deployment: < 4 hours**
