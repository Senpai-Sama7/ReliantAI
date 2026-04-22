# GEN-H Studio

Premium HVAC growth systems with integrated admin portal. A dark editorial website with sophisticated scroll-driven animations and full backend control capabilities.

## Features

### Customer-Facing Website
- **Hero Section** - Full-viewport with Ken Burns background, parallax scrolling
- **Narrative Text** - Scroll-triggered text reveal with animated gold star
- **Card Stack** - Pinned scroll-driven card gallery (Attract → Qualify → Convert)
- **Breath Section** - Cinematic image banner with scale-up animation
- **ZigZag Grid** - Alternating image/text layout (Clarify → Capture → Run → Optimize)
- **Footer** - Dark footer with magnetic button effect

### Admin Portal
- **Secure Login** - Username/password form with backend-issued session cookie
- **Dashboard Metrics** - Total dispatches, pending, completed, emergency percentages
- **Dispatch List** - Real-time view of all service requests
- **Auto-Refresh** - Dashboard updates every 30 seconds
- **Status Tracking** - View customer info, issues, urgency levels

## Design System

- **Background**: #0B0C0E (near-black)
- **Accent**: #D7A04D (warm gold) - CTAs and labels only
- **Text Primary**: #F4F6F8 (off-white)
- **Text Secondary**: #A6ACB2 (cool gray)
- **Typography**: Montserrat 700-900 (display, ALL CAPS) + Inter 400-500 (body)

## Tech Stack

- React 19 + TypeScript
- React Router 6 (navigation)
- Vite (build tool)
- Tailwind CSS 3
- GSAP (ScrollTrigger) for animations
- Lenis for smooth scrolling

## Quick Start

```bash
npm install
npm run dev
```

## Configuration

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8000` |
| `VITE_ENABLE_ADMIN` | Enable admin features | `true` |

## Deployment

### Vercel (Recommended)

1. Push your code to GitHub
2. Import repository on [Vercel](https://vercel.com)
3. Add environment variables in Vercel dashboard
4. Deploy!

**Build Settings:**
- Framework: Vite
- Build Command: `npm run build`
- Output Directory: `dist`

### Connecting to Backend

1. Deploy the backend API (see main system repo)
2. Set `VITE_API_BASE_URL` to your API URL
3. Ensure backend CORS allows your frontend domain
4. Use your `DISPATCH_API_KEY` to log into admin portal

## Admin Portal Usage

### Accessing Admin Dashboard

1. Navigate to `/admin/login`
2. Enter your admin username and password
3. View and manage dispatches in real-time

### Features

- **Metrics Cards**: Overview of dispatch statistics
- **Dispatch Table**: Sortable list with customer info, status, urgency
- **Auto-Refresh**: Data refreshes every 30 seconds
- **Logout**: Securely clear session

## API Integration

The frontend connects to the main HVAC dispatch system:

```typescript
// API Service endpoints
GET  /health           - Health check
GET  /dispatches       - List recent dispatches
GET  /run/{id}         - Get dispatch status
POST /dispatch         - Create new dispatch
POST /login            - Admin login (form data)
GET  /logout           - Admin logout
```

## Project Structure

```
src/
├── components/
│   └── ProtectedRoute.tsx    # Auth guard component
├── config/
│   ├── env.ts                # Environment variables
│   └── site.ts               # Site configuration
├── contexts/
│   └── AuthContext.tsx       # Authentication state
├── sections/
│   ├── admin/
│   │   ├── AdminLogin.tsx    # Admin login page
│   │   └── AdminDashboard.tsx # Admin dashboard
│   ├── Hero.tsx
│   ├── NarrativeText.tsx
│   ├── CardStack.tsx
│   ├── BreathSection.tsx
│   ├── ZigZagGrid.tsx
│   └── Footer.tsx
├── services/
│   └── api.ts                # API client
└── App.tsx                   # Main router
```

## Required Images

Place images in `public/`:

| File | Description |
|------|-------------|
| `hero-bg.jpg` | Modern minimalist interior |
| `breath-bg.jpg` | HVAC control room |
| `card-1.jpg` | Premium website on laptop |
| `card-2.jpg` | Lead qualification form |
| `card-3.jpg` | Admin portal dashboard |
| `grid-1.jpg` | Team collaboration |
| `grid-2.jpg` | Professional reviewing docs |
| `grid-3.jpg` | HVAC technician with tablet |
| `grid-4.jpg` | Executive reviewing analytics |

## Security

- Admin authentication is session-cookie based; the frontend does not persist bearer tokens or API keys in `localStorage`
- Protected routes require an authenticated backend session
- CORS credentials are enabled for session cookies
- Security headers are sent on requests

## License

© 2025 GEN-H Studio. All rights reserved.
