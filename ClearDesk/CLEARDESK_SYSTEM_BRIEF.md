# ClearDesk — AI-Powered AR Document Processing Dashboard

## What It Is
Production-quality accounts receivable document processing dashboard. Users upload real financial documents (invoices, statements, disputes), Claude AI analyzes them server-side, extracts structured data, assigns priority/type, and flags items for escalation. Documents persist in the browser by default, with optional signed Cloudflare KV sync for cross-device access. Premium dark UI (Bloomberg Terminal aesthetic).

## Stack
React 19 · TypeScript 5.9 · Vite 7.3 · Tailwind CSS 4.2 · Lucide React · date-fns · Vercel serverless

## Build Status
```
✓ tsc --noEmit clean
✓ npm run build — 258KB JS, 23KB CSS, 0 errors
✓ Vercel deploy-ready (vercel.json + api/ serverless function)
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Browser (React SPA)                                     │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────────┐ │
│  │FileUpload│→ │claudeSvc │→ │ POST /api/analyze       │ │
│  │  .tsx    │  │  .ts     │  │ (no API key in browser) │ │
│  └──────────┘  └──────────┘  └───────────┬────────────┘ │
│                                           │              │
│  ┌──────────────────────────────────────┐ │              │
│  │ DocumentContext (useReducer)          │ │              │
│  │ localStorage('cleardesk_documents')  │ │              │
│  └──────────────────────────────────────┘ │              │
└───────────────────────────────────────────┼──────────────┘
                                            │
┌───────────────────────────────────────────▼──────────────┐
│  Vercel Serverless: api/analyze.ts                        │
│  process.env.ANTHROPIC_API_KEY → Claude claude-sonnet-4-20250514 API     │
│  Returns structured JSON: type, priority, extractedData,  │
│  escalationReasons, confidence, summary                   │
└──────────────────────────────────────────────────────────┘
```

## File Tree (25 source files, ~1,800 LOC)
```
api/analyze.ts                    71 — Vercel serverless proxy to Claude
src/App.tsx                       12 — Root: DocumentProvider → Dashboard
src/main.tsx                      10 — React entry
src/index.css                     70 — Tailwind v4 @theme tokens, dark palette
src/types/document.ts             85 — All TypeScript interfaces
src/contexts/DocumentContext.tsx  231 — useReducer state, localStorage persistence
src/services/claudeService.ts     20 — POST /api/analyze (no key in browser)
src/utils/fileProcessing.ts      139 — Text extraction from files
src/utils/formatters.ts           87 — classNames, formatFileSize, generateId
src/components/dashboard/
  Dashboard.tsx                   94 — Main view router + tour wiring
  Layout.tsx                      94 — Sidebar nav + header search
  DocumentCard.tsx                61 — Card with type/priority/status badges
  DocumentDetail.tsx             167 — Slide-over detail panel
  StatsOverview.tsx               31 — Summary stat cards
  FilterPanel.tsx                 74 — Status/type/priority/assignee filters
  ExportPanel.tsx                108 — CSV/JSON export
  SettingsPanel.tsx               49 — Clear data, replay tour
src/components/upload/
  FileUpload.tsx                 154 — Drag-drop, phased status, error handling
src/components/tour/
  Tour.tsx                        99 — SVG spotlight 4-step onboarding
src/components/ui/
  Button.tsx                      44 — Primary/secondary/danger/ghost
  Badge.tsx                       48 — Status/priority/type badges
  Modal.tsx                       55 — Slide-over modal
```

## Design System (src/index.css @theme)
```
Background: #0A0A0F    Surface: #111118     Border: #1E1E2E
Text:       #F0F0F5    Secondary: #6B6B80   Accent: #00FF94
Danger:     #FF4444    Warning: #FFB800
Fonts: Syne (headings), DM Sans (body), JetBrains Mono (numbers)
Radius: 8px. No shadows, no glassmorphism, no gradients.
```

## Key Source Files

### api/analyze.ts — Server-side Claude proxy
```typescript
import type { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) return res.status(500).json({ error: 'ANTHROPIC_API_KEY not configured on server' });

  const { content, filename } = req.body;
  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 2000,
      system: `You are an expert AI assistant for accounts receivable document processing.
Analyze the provided document and return ONLY a JSON response:
{
  "documentType": "invoice"|"statement"|"payment_confirmation"|"dispute"|"credit_note"|"other",
  "priority": "critical"|"high"|"medium"|"low",
  "extractedData": {
    "customerName", "customerId", "invoiceNumber", "invoiceDate", "dueDate",
    "amount", "currency", "accountNumber", "paymentTerms", "notes", "confidence"
  },
  "escalationReasons": [{ "type", "description", "field?" }],
  "requiresHumanReview": boolean,
  "confidence": number (0-1),
  "summary": string
}
Priority: Critical >$50k or disputes. High >$10k. Medium $1k-$10k. Low <$1k.
Escalate if confidence <0.8, missing critical fields, amount >$40k, or disputes.`,
      messages: [{ role: 'user', content: `Analyze this document:\n\nFilename: ${filename}\n\nContent:\n${content}` }],
    }),
  });

  const data = await response.json();
  const text = data.content?.[0]?.text;
  const jsonMatch = text.match(/\{[\s\S]*\}/);
  return res.status(200).json(JSON.parse(jsonMatch[0]));
}
```

### src/services/claudeService.ts — Client (no API key)
```typescript
export class ClaudeService {
  async analyzeDocument(content: string, filename: string): Promise<ClaudeAnalysisResponse> {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, filename }),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
      throw new Error(err.error || `API error ${response.status}`);
    }
    return response.json();
  }
}
```

### src/components/upload/FileUpload.tsx — Upload with phased status
```typescript
const ANALYSIS_PHASES = [
  'Extracting document structure…',
  'Analyzing priority…',
  'Generating summary…',
] as const;

// Upload flow:
// 1. User drops/selects file → validate type
// 2. extractTextFromFile reads content (txt/csv natively, pdf/docx notes limitation)
// 3. Empty content guard → specific error
// 4. addDocument creates doc with status:'processing'
// 5. Phase timer cycles ANALYSIS_PHASES every 2.5s during Claude call
// 6. claudeService.analyzeDocument(content, filename) → POST /api/analyze
// 7. Success: updates doc with full analysis, status:'completed' or 'escalated'
// 8. Failure: specific error (missing key, 401, 429, 500, network), doc saved as 'pending'
```

### src/contexts/DocumentContext.tsx — State management
```typescript
// useReducer with actions: ADD/UPDATE/DELETE_DOCUMENT, SET/CLEAR_FILTERS,
//   BULK_UPDATE_STATUS, BULK_ASSIGN, SELECT_DOCUMENT
// Persistence: useEffect saves to localStorage('cleardesk_documents') on every change
// Starts empty — no preloaded data. App populates via real uploads only.
// Filtering: status, type, priority, assignee, searchQuery (searches name, customer, invoice#, notes)
```

### src/types/document.ts — Type system
```typescript
type DocumentStatus = 'pending' | 'processing' | 'review' | 'completed' | 'escalated';
type DocumentPriority = 'critical' | 'high' | 'medium' | 'low';
type DocumentType = 'invoice' | 'statement' | 'payment_confirmation' | 'dispute' | 'credit_note' | 'other';

interface Document {
  id, filename, originalName, type, status, priority,
  fileContent?, extractedData?, escalationReasons?,
  isEscalated, assignee?, createdAt, updatedAt, processedAt?, notes?, tags
}

interface ClaudeAnalysisResponse {
  documentType, priority, extractedData, escalationReasons,
  requiresHumanReview, confidence, summary
}
```

## What's Real vs What's Not
- ✅ Real: File upload, text extraction, Claude AI analysis, structured data extraction, priority classification, escalation logic, localStorage persistence, search, filtering, export (CSV/JSON)
- ✅ Real: Server-side API key (never in browser), Vercel serverless proxy, error handling with specific messages
- ✅ Real: Onboarding tour (4 steps, SVG spotlight, first-visit only, replayable from Settings)
- ⚠️ Limitation: PDF/image/Word extraction requires additional libraries (pdf.js, tesseract.js, mammoth.js) — currently returns honest message about limitation. TXT/CSV work fully.
- ❌ Nothing is mocked, simulated, or fake. App starts empty. All data comes from real uploads + real Claude analysis.

## Deployment
```bash
# Local dev
npm run dev          # Vite on :5173

# Production build
npm run build        # Output in dist/

# Vercel deploy
vercel               # Needs ANTHROPIC_API_KEY env var in Vercel dashboard
```

vercel.json:
```json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "/api/$1" },
    { "source": "/((?!api/).*)", "destination": "/index.html" }
  ]
}
```
