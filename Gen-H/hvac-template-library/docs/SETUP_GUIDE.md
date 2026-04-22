# HVAC Template Library - Setup Guide

## Quick Start (5 minutes)

### Prerequisites
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+
- Git

### 1. Clone Repository
\`\`\`bash
git clone https://github.com/yourusername/hvac-template-library.git
cd hvac-template-library
\`\`\`

### 2. Setup Environment
\`\`\`bash
cp .env.example .env
# Edit .env with your credentials
export DB_PASSWORD=your_secure_password
export JWT_SECRET=your_jwt_secret
\`\`\`

### 3. Start Services
\`\`\`bash
docker-compose up -d
\`\`\`

### 4. Initialize Database
\`\`\`bash
docker-compose exec postgres psql -U hvac_user -d hvac_templates -f /database/schema.sql
\`\`\`

### 5. Access Services
- **CMS Dashboard**: http://localhost:3000
- **API**: http://localhost:5000
- **Database**: localhost:5432

---

## User Roles

### 1. Admin
- Manage all templates
- View all deployments
- Access analytics
- Manage users

### 2. Template Developer
- Create/edit templates
- Test templates locally
- Submit for review
- Version control

### 3. Company Manager
- View own deployments
- Customize templates
- Request changes
- View analytics

---

## Workflow: Template to Deployment

### Step 1: Select Template
\`\`\`bash
curl http://localhost:5000/api/templates
\`\`\`

### Step 2: Create Company
\`\`\`bash
curl -X POST http://localhost:5000/api/companies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "HVAC Corp",
    "slug": "hvac-corp",
    "email": "info@hvacsorp.com",
    "phone": "+1-555-0100",
    "owner_name": "John Doe",
    "owner_email": "john@hvacsorp.com",
    "business_type": "residential"
  }'
\`\`\`

### Step 3: Create Deployment
\`\`\`bash
curl -X POST http://localhost:5000/api/deployments \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "template-1-technical-elegance",
    "company_id": "company-id",
    "domain": "hvac-corp.com",
    "customizations": {
      "primary_color": "#0f172a",
      "secondary_color": "#b87333"
    }
  }'
\`\`\`

### Step 4: Deploy
\`\`\`bash
./scripts/deploy.sh template-1-technical-elegance company-id hvac-corp.com production
\`\`\`

---

## Directory Structure Explained

\`\`\`
templates/              # 4 pre-built template frameworks
├── template-1/        # Technical Elegance (3D, calculator, case studies)
├── template-2/        # Trust & Reliability (team focus, testimonials)
├── template-3/        # Performance Showcase (data-driven, ROI)
└── template-4/        # Modern Minimalist (clean, typography-forward)

cms/                   # Management dashboard (Next.js)
├── pages/
│   ├── index.tsx      # Dashboard home
│   ├── templates/     # Template management
│   ├── companies/     # Company management
│   └── deployments/   # Deployment management
└── components/        # Reusable UI components

api-gateway/           # Central API (Express)
├── routes/
│   ├── templates.ts   # Template CRUD
│   ├── companies.ts   # Company CRUD
│   ├── deployments.ts # Deployment management
│   └── analytics.ts   # Analytics & metrics
└── models/            # Database models

shared/                # Reusable across templates
├── components/
│   ├── Button.tsx
│   ├── ServiceCard.tsx
│   ├── BeforeAfterSlider.tsx
│   ├── InteractiveCalculator.tsx
│   ├── Testimonials.tsx
│   └── 3DViewer.tsx
└── utils/
    ├── colorPalettes.ts
    ├── animations.ts
    └── helpers.ts

database/              # Schema & migrations
└── schema.sql
\`\`\`

---

## Configuration Files

### Template Config (templates/{id}/config.json)
\`\`\`json
{
  "name": "Technical Elegance",
  "colors": {
    "primary": "#0f172a",
    "secondary": "#b87333",
    "accent": "#ff6b00"
  },
  "sections": [
    {"name": "Hero", "component": "Hero3DViewer"},
    {"name": "Services", "component": "SplitLayout"}
  ]
}
\`\`\`

### Deployment Config (customizations)
\`\`\`json
{
  "customizations": {
    "primary_color": "#custom",
    "secondary_color": "#custom",
    "logo_url": "https://..."
  },
  "custom_content": {
    "hero_headline": "Your Company",
    "about_text": "About your company"
  }
}
\`\`\`

---

## API Documentation

### Templates

#### Get All Templates
\`\`\`
GET /api/templates?framework=technical-elegance&status=active
Response: { success: true, data: [...] }
\`\`\`

#### Get Single Template
\`\`\`
GET /api/templates/{id}
Response: { success: true, data: {...} }
\`\`\`

#### Create Template
\`\`\`
POST /api/templates
Body: { name, framework, colors, features, ... }
Response: { success: true, data: {...} }
\`\`\`

### Deployments

#### Create Deployment
\`\`\`
POST /api/deployments
Body: { template_id, company_id, domain, customizations }
Response: { success: true, data: {...} }
\`\`\`

#### Update Customizations
\`\`\`
PATCH /api/deployments/{id}/customize
Body: { customizations, custom_content }
Response: { success: true, data: {...} }
\`\`\`

#### Deploy to Production
\`\`\`
POST /api/deployments/{id}/deploy
Response: { success: true, data: {...} }
\`\`\`

#### Get Analytics
\`\`\`
GET /api/deployments/{id}/analytics
Response: { success: true, data: [{event_type, count, unique_users}, ...] }
\`\`\`

---

## Customization Examples

### Change Colors
\`\`\`bash
./scripts/customize.sh deployment-id company-id
\`\`\`

### Update Content
\`\`\`typescript
// Edit custom_content in deployment
{
  "custom_content": {
    "hero_headline": "Welcome to HVAC Corp",
    "services": [...],
    "team_members": [...]
  }
}
\`\`\`

### Enable/Disable Features
\`\`\`typescript
// Modify customizations
{
  "features_enabled": {
    "3d_viewer": true,
    "calculator": true,
    "before_after": false
  }
}
\`\`\`

---

## Deployment Platforms

### Vercel (Recommended)
- Zero-config deployment
- Automatic scaling
- Built-in analytics
- Free SSL certificates

### Netlify
- Git-based deployments
- Edge functions
- Built-in forms
- Free SSL certificates

### Self-Hosted (AWS/GCP/Azure)
- Full control
- Custom domain
- Load balancing
- Custom integrations

---

## Monitoring & Maintenance

### Performance Monitoring
\`\`\`bash
./scripts/monitor.sh alerts@example.com
\`\`\`

### Health Checks
- Response time < 2s
- Lighthouse score > 85
- Uptime > 99.9%
- No 5xx errors

### Regular Tasks
- Backup database (daily)
- Monitor SSL certificates (weekly)
- Review analytics (weekly)
- Update dependencies (monthly)

---

## Troubleshooting

### Port Already in Use
\`\`\`bash
lsof -i :3000
kill -9 <PID>
\`\`\`

### Database Connection Error
\`\`\`bash
docker-compose logs postgres
docker-compose restart postgres
\`\`\`

### Deployment Failed
\`\`\`bash
# Check logs
docker-compose logs api
# Re-run deployment
./scripts/deploy.sh template-id company-id domain
\`\`\`

---

## Support & Resources

- **Documentation**: /docs
- **API Reference**: http://localhost:5000/api/docs
- **GitHub Issues**: https://github.com/yourusername/hvac-template-library/issues
- **Community**: Discord channel
