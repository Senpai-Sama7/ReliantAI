import React, { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';


const sections = [
  {
    title: 'Getting Started',
    content: `ClearDesk processes your accounts receivable documents using AI. Upload any invoice, statement, collections notice, or email — the system extracts structured data, scores priority, and generates a plain-English summary your team can act on immediately.

**First steps:**
1. Click **Upload** in the sidebar or the **Upload** button on the dashboard
2. Drag and drop files or click to browse — PDF, images, Word, Excel, email (.eml), and text files are all supported
3. ClearDesk sends the document to Claude AI for analysis
4. The processed document appears as a card on your dashboard with priority, status, and extracted data

**Sample documents:** When the upload panel is open, click "Use sample documents" to try pre-loaded invoices without uploading your own files.`
  },
  {
    title: 'Document Processing',
    content: `**Supported formats:** PDF, PNG, JPG, WEBP, DOCX, XLSX, CSV, EML, TXT, JSON, Markdown

**What the AI extracts:**
- Document type (invoice, statement, payment confirmation, dispute, credit note)
- Customer name, ID, and account number
- Invoice number, date, and due date
- Amount and currency
- Payment terms
- Confidence score (0–100%)

**What the AI generates:**
- Priority classification (Critical, High, Medium, Low) based on your configured thresholds
- A 3-sentence summary in English and Spanish
- Action deadline — the single most important date from the document
- Escalation flags with specific reasons and triggering fields
- Whether the document requires human review`
  },
  {
    title: 'Priority & Escalation',
    content: `**Priority levels** are determined by dollar amount thresholds you configure in Settings:
- **Critical:** Above your critical threshold (default $50,000) or any dispute
- **High:** Above your high threshold (default $10,000)
- **Medium:** Between medium and high thresholds (default $1,000–$10,000)
- **Low:** Below your medium threshold

**Escalation rules** (configurable in Settings):
- Dispute documents always escalated
- AI confidence below 80% triggers review
- Amounts exceeding critical threshold flagged
- Due dates within 7 days flagged (optional)

Each escalation includes a severity level:
- **Blocking** — cannot proceed without human decision
- **Warning** — should review but can proceed
- **Informational** — FYI only`
  },
  {
    title: 'Dashboard & Filtering',
    content: `**Stats overview** at the top shows total documents, escalated count, and priority breakdown at a glance.

**Filters** let you narrow the view by:
- Status: Pending, Processing, In Review, Completed, Escalated
- Priority: Critical, High, Medium, Low
- Document type: Invoice, Statement, Payment, Dispute, Credit Note
- Assignee: Any team member you've added

**Search** in the top bar searches across document names, customer names, and extracted data.

**Document detail** — click any card to open the full detail panel with all extracted data, escalation reasons, status controls, assignee dropdown, and the EN/ES summary toggle.`
  },
  {
    title: 'AI Chat Assistant',
    content: `The green chat button in the bottom-right corner opens ClearDesk's AI assistant, powered by Claude Haiku for fast responses.

**What it can do:**
- Answer questions about your document queue ("What needs attention today?")
- Summarize escalated or overdue items
- Identify which customers have the largest outstanding balances
- Draft collections follow-up emails and notices
- Provide operational recommendations

**Smart context:** The assistant only receives documents relevant to your question — not your entire queue. If you ask about escalated items, it only sees escalated documents. If you mention a customer name, it only sees that customer's documents. This keeps responses fast and focused.

**Suggested prompts** appear when you first open the chat:
- "What needs attention today?"
- "Summarize all escalated items"
- "Who is most overdue?"
- "Draft a collections follow-up for the largest outstanding invoice"

Chat history is saved per browser session. Click the trash icon to clear it.`
  },
  {
    title: 'Multilingual Summaries',
    content: `Every processed document generates two summaries simultaneously:
- **English (EN)** — default display language
- **Spanish (ES)** — professional Latin American Spanish

Open any document's detail panel and use the **EN / ES** toggle next to the summary to switch languages. Names, amounts, dates, and invoice numbers are preserved exactly — only the surrounding language is translated.

This is designed for multilingual operations teams. Your US team sees English summaries. Your Latin American team sees Spanish. Same dashboard, same data, no extra steps.`
  },
  {
    title: 'Export',
    content: `Click **Export** in the filter bar to generate a summary report of your current document view.

The export includes:
- Date and document count
- Each document's key fields: type, priority, customer, amount, due date, status, and summary
- Escalation flags where applicable

Export respects your current filters — if you're viewing only escalated documents, the export contains only escalated documents.`
  },
  {
    title: 'Cross-Device Sync',
    content: `ClearDesk can sync your documents across devices using Cloudflare KV with a signed browser session and short-lived share codes.

**How it works:**
1. Go to **Settings → Cross-Device Sync**
2. Generate a share code for the current browser
3. On another device, paste the share code into the import field before it expires
4. The new browser receives its own sync session and loads your documents

Documents sync automatically in the background whenever they change. If cloud sync is not configured by the server admin, the app works normally with local storage only.`
  },
  {
    title: 'Settings',
    content: `**Appearance** — Switch between Dark, Light, and System theme.

**Priority Thresholds** — Set the dollar amounts that determine Critical, High, Medium, and Low priority. These are sent to the AI with every document analysis.

**Escalation Rules** — Toggle which conditions trigger automatic escalation: disputes, low confidence, high value, approaching deadlines.

**Team Members** — Add names that populate the assignee dropdown on document cards. Assign documents to team members for accountability.

**Data Management** — View how many documents are stored and clear all data if needed.`
  },
  {
    title: 'Keyboard Shortcuts',
    content: `- **Enter** — Send message in AI chat
- **Shift + Enter** — New line in AI chat
- **Escape** — Close modals and detail panels`
  },
];

function Accordion({ title, content, defaultOpen = false }: { title: string; content: string; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <button onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-3.5 text-left hover:bg-surface/50 transition-colors">
        <span className="text-sm font-medium text-text-primary">{title}</span>
        {open ? <ChevronDown className="w-4 h-4 text-text-secondary" /> : <ChevronRight className="w-4 h-4 text-text-secondary" />}
      </button>
      {open && (
        <div className="px-5 pb-4 text-sm text-text-secondary leading-relaxed space-y-2 border-t border-border pt-3">
          {content.split('\n\n').map((block, i) => {
            if (block.startsWith('- ')) {
              return <ul key={i} className="space-y-1 ml-1">{block.split('\n').map((line, j) => (
                <li key={j} className="flex gap-2"><span className="text-accent mt-0.5">•</span><span>{renderInline(line.replace(/^- /, ''))}</span></li>
              ))}</ul>;
            }
            if (/^\d+\. /.test(block)) {
              return <ol key={i} className="space-y-1 ml-1">{block.split('\n').map((line, j) => (
                <li key={j} className="flex gap-2"><span className="text-accent font-mono text-xs mt-0.5">{j + 1}.</span><span>{renderInline(line.replace(/^\d+\.\s*/, ''))}</span></li>
              ))}</ol>;
            }
            return <p key={i}>{renderInline(block)}</p>;
          })}
        </div>
      )}
    </div>
  );
}

function renderInline(text: string): React.ReactNode[] {
  return text.split(/(\*\*.+?\*\*)/g).filter(Boolean).map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index} className="text-text-primary">{part.slice(2, -2)}</strong>;
    }
    return <React.Fragment key={index}>{part}</React.Fragment>;
  });
}

export function HelpPanel() {
  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <h1 className="font-heading text-2xl font-bold text-text-primary">Help & User Guide</h1>
        <p className="text-sm text-text-secondary mt-1">Everything you need to know about using ClearDesk</p>
      </div>
      <div className="space-y-2">
        {sections.map((s, i) => (
          <Accordion key={s.title} title={s.title} content={s.content} defaultOpen={i === 0} />
        ))}
      </div>
      <div className="text-center py-4">
        <p className="text-xs text-text-secondary">ClearDesk v1.0 — Built by <a href="https://douglasmitchell.info" target="_blank" rel="noopener" className="text-accent hover:underline">Douglas Mitchell</a></p>
      </div>
    </div>
  );
}
