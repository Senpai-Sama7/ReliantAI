# ClearDesk - Agent Guide

**Last updated:** 2026-03-05

## Project Overview

ClearDesk is an AI-powered Accounts Receivable (AR) document processing system. It handles the "messy middle" that RPA bots fail on - misformatted invoices, missing fields, and ambiguous collections disputes.

**Key Capabilities:**
- Processes 7 document formats: PDF, Image, Word, Excel, CSV, Email, Text
- Bilingual output (English + Spanish) automatic
- Claude AI-powered document analysis
- Real-time AR queue chat assistant
- Priority scoring: CRITICAL / HIGH / MEDIUM / LOW

## Hostile Audit Rules

- Keep cross-device sync behind signed browser sessions and short-lived share codes; do not reintroduce raw UUID-based KV access.
- Keep document preview rendering text-safe or explicitly sanitized before any HTML insertion.
- Treat browser storage as non-secret storage only; do not persist auth tokens or equivalent capability secrets there.
- Append hostile-audit proof, commands, and blockers to the root `PROGRESS_TRACKER.md` before closing security work.
 
**Architecture Pattern:**
```
┌─────────────────────────────────────────────────────────┐
│  Vercel Edge Functions                                    │
│  ├── Document analysis (Claude Sonnet 4)                 │
│  ├── Entity extraction                                   │
│  └── Priority classification                             │
├─────────────────────────────────────────────────────────┤
│  Chat Assistant                                           │
│  └── Claude Haiku 4.5 (fast responses)                   │
├─────────────────────────────────────────────────────────┤
│  Storage Strategy                                         │
│  ├── Production: Vercel Blob                             │
│  └── Development: JSON files (silent fallback)           │
└─────────────────────────────────────────────────────────┘
```

---

## Build / Run / Test Commands

### Development
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint

# Type check
npx tsc --noEmit
```

### Vercel Deployment
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

### API Testing
```bash
# Health check
curl https://clear-desk-ten.vercel.app/api/health

# Document analysis (POST with FormData)
curl -X POST https://clear-desk-ten.vercel.app/api/analyze \
  -F "file=@invoice.pdf"

# Chat query
curl -X POST https://clear-desk-ten.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me overdue invoices"}'
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React 19 + TypeScript | UI components |
| **Build Tool** | Vite 5 | Fast dev server, optimized builds |
| **Styling** | Tailwind CSS | Utility-first CSS |
| **AI Analysis** | Claude Sonnet 4 | Document processing |
| **Chat** | Claude Haiku 4.5 | Fast chat responses |
| **Storage** | Vercel Blob / JSON | Document & data storage |
| **Sync** | Cloudflare KV | Cross-device state |
| **Icons** | Lucide React | Icon library |
| **Linting** | ESLint + TypeScript | Code quality |

---

## Project Structure

```
ClearDesk/
├── src/
│   ├── components/             # React components
│   │   ├── DocumentUpload.tsx
│   │   ├── AnalysisResults.tsx
│   │   └── ChatInterface.tsx
│   ├── hooks/                  # Custom React hooks
│   │   └── useDocumentAnalysis.ts
│   ├── utils/                  # Utility functions
│   │   ├── claude-client.ts   # Claude API wrapper
│   │   └── storage.ts         # Vercel Blob / JSON fallback
│   ├── types/                  # TypeScript types
│   └── App.tsx                 # Main application
├── api/                        # Vercel Edge Functions
│   ├── analyze.ts             # Document analysis endpoint
│   ├── chat.ts                # Chat endpoint
│   └── health.ts              # Health check
├── public/                     # Static assets
├── index.html                  # Entry HTML
├── vite.config.ts             # Vite configuration
├── vercel.json                # Vercel routing config
├── tailwind.config.js         # Tailwind configuration
└── tsconfig.json              # TypeScript config
```

---

## Critical Code Patterns

### Claude API Client
```typescript
// Claude Sonnet 4 for document analysis
const analysis = await claude.messages.create({
  model: "claude-3-sonnet-20240229",
  max_tokens: 4096,
  messages: [{
    role: "user",
    content: [
      { type: "text", text: "Analyze this AR document..." },
      { type: "image", source: { type: "base64", media_type: "application/pdf", data: pdfBase64 } }
    ]
  }]
});

// Claude Haiku 4.5 for chat (faster, cheaper)
const chat = await claude.messages.create({
  model: "claude-3-haiku-20240307",
  max_tokens: 1024,
  messages: [{ role: "user", content: userQuery }]
});
```

### Storage Strategy Pattern
```typescript
// Vercel Blob in production, JSON files in dev
export async function storeDocument(file: File, analysis: Analysis) {
  if (process.env.VERCEL_ENV === 'production') {
    // Use Vercel Blob
    const blob = await put(`docs/${file.name}`, file, {
      access: 'public',
    });
    return blob.url;
  } else {
    // Dev fallback: localStorage or JSON file
    const data = await file.text();
    localStorage.setItem(`doc_${Date.now()}`, data);
    return `local://${file.name}`;
  }
}
```

### Priority Scoring Logic
```typescript
type Priority = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

function calculatePriority(
  amount: number,
  daysOverdue: number,
  escalationFlags: string[]
): Priority {
  if (amount > 50000 || daysOverdue > 90) return 'CRITICAL';
  if (amount > 10000 || daysOverdue > 30) return 'HIGH';
  if (daysOverdue > 0) return 'MEDIUM';
  return 'LOW';
}
```

---

## Non-Obvious Gotchas

### 1. vercel.json is a Safety Shim
The `vercel.json` file is a **critical safety configuration**. DO NOT REMOVE IT.

It handles:
- Route fallbacks
- Security headers
- API routing

### 2. Production vs Development Storage
| Environment | Storage | Behavior |
|-------------|---------|----------|
| Production | Vercel Blob | Real blob storage |
| Development | JSON files | Silent fallback |

The app automatically detects environment and switches. No code changes needed.

### 3. Two Claude Models Used
- **Claude Sonnet 4** (`claude-3-sonnet-20240229`): Document analysis (detailed, slower)
- **Claude Haiku 4.5** (`claude-3-haiku-20240307`): Chat responses (fast, cheaper)

Don't confuse them - they have different APIs and pricing.

### 4. Edge Functions Location
API routes go in `api/` directory at project root:
```
api/
├── analyze.ts    →  /api/analyze
├── chat.ts       →  /api/chat
└── health.ts     →  /api/health
```

NOT in `src/api/` - that's for frontend API utilities.

### 5. Cloudflare KV for Cross-Device Sync
User preferences and queue state sync via Cloudflare KV:
- Requires `KV_NAMESPACE_ID` env var
- Falls back to localStorage if KV unavailable
- Eventually consistent (not real-time)

### 6. Document Size Limits
Vercel Edge Functions have limits:
- Request body: 4.5 MB
- Function duration: 60 seconds (Hobby), 300s (Pro)
- Large PDFs may need preprocessing

### 7. Tailwind Configuration
Custom theme extends defaults:
```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        'ar-critical': '#DC2626',
        'ar-high': '#F59E0B',
        'ar-medium': '#3B82F6',
        'ar-low': '#10B981',
      }
    }
  }
}
```

### 8. No Database Required
ClearDesk is stateless:
- Documents stored in Vercel Blob (or localStorage)
- Analysis results cached in Blob
- No PostgreSQL, no Redis needed

---

## Configuration

### Environment Variables
```bash
# Required for Claude
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Cloudflare KV (for cross-device sync)
CLOUDFLARE_ACCOUNT_ID=your-account-id
CLOUDFLARE_API_TOKEN=your-api-token
KV_NAMESPACE_ID=your-namespace-id

# Optional: Vercel Blob (auto-configured in production)
BLOB_READ_WRITE_TOKEN=vercel_blob_token
```

### Vercel Configuration
```json
// vercel.json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "/api/$1" },
    { "source": "/(.*)", "destination": "/index.html" }
  ],
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        { "key": "Access-Control-Allow-Origin", "value": "*" }
      ]
    }
  ]
}
```

---

## Testing Strategy

### Unit Tests
```bash
# Run with Vitest (if configured)
npm test
```

### API Testing
```bash
# Test document analysis
curl -X POST http://localhost:3000/api/analyze \
  -F "file=@test-invoice.pdf" \
  -F "language=es"  # Spanish output

# Test chat
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Total amount overdue?", "context": [...]}'
```

### E2E Testing
Use Playwright or Cypress for full flow testing.

---

## Deployment Checklist

- [ ] Set `ANTHROPIC_API_KEY` in Vercel env
- [ ] Configure `BLOB_READ_WRITE_TOKEN` for production
- [ ] Set up Cloudflare KV (optional, for sync)
- [ ] Verify `vercel.json` is present
- [ ] Run `npm run build` locally to check for errors
- [ ] Deploy with `vercel --prod`

---

## Reference

See root `AGENTS.md` for:
- Core commandments (integration build rules)
- Mode-specific guidelines
- Universal patterns across all ReliantAI projects
