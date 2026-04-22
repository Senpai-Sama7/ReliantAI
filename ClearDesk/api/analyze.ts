import type { VercelRequest, VercelResponse } from '@vercel/node';

const CLAUDE_API_URL = 'https://api.anthropic.com/v1/messages';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) return res.status(500).json({ error: 'ANTHROPIC_API_KEY not configured on server' });

  try {
    if (!req.body || typeof req.body !== 'object') return res.status(400).json({ error: 'Invalid request body' });
    const { content, filename, settings } = req.body;
    if (!content || !filename) return res.status(400).json({ error: 'content and filename required' });

    // Guard against oversized documents — truncate at 50k chars
    const MAX_CHARS = 50000;
    const truncated = content.length > MAX_CHARS;
    const safeContent = truncated ? content.slice(0, MAX_CHARS) : content;

    const t = settings?.thresholds || { critical: 50000, high: 10000, medium: 1000 };
    const r = settings?.escalationRules || { disputes: true, lowConfidence: true, exceedsCritical: true, dueSoon: false };

    const escalationLines = [
      r.disputes && '- Dispute documents ALWAYS require requiresHumanReview: true regardless of amount.',
      r.lowConfidence && '- Escalate if confidence < 0.8 or missing critical fields.',
      r.exceedsCritical && `- Escalate if amount exceeds $${t.critical.toLocaleString()}.`,
      r.dueSoon && '- Escalate if due date is within 7 days from today.',
    ].filter(Boolean).join('\n');

    const response = await fetch(CLAUDE_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-beta': 'prompt-caching-2024-07-31',
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 4096,
        system: [{ type: 'text', text: `You are an expert AI assistant for accounts receivable document processing.
Analyze the provided document and return ONLY a JSON response:
{
  "documentType": "invoice" | "statement" | "payment_confirmation" | "dispute" | "credit_note" | "other",
  "priority": "critical" | "high" | "medium" | "low",
  "extractedData": {
    "customerName": string | null,
    "customerId": string | null,
    "invoiceNumber": string | null,
    "invoiceDate": string (YYYY-MM-DD) | null,
    "dueDate": string (YYYY-MM-DD) | null,
    "amount": number | null,
    "currency": string | null,
    "accountNumber": string | null,
    "paymentTerms": string | null,
    "notes": string | null,
    "confidence": number (0-1)
  },
  "actionDeadline": string (ISO 8601 date) | null,
  "escalationReasons": [{ "type": "low_confidence"|"missing_data"|"ambiguous"|"high_value"|"manual_review", "severity": "blocking"|"warning"|"informational", "description": string, "field": string? }],
  "requiresHumanReview": boolean,
  "confidence": number (0-1),
  "summary": string,
  "summary_es": string
}
PRIORITY THRESHOLDS:
- Critical: >$${t.critical.toLocaleString()} or disputes
- High: >$${t.high.toLocaleString()}
- Medium: $${t.medium.toLocaleString()}-$${t.high.toLocaleString()}
- Low: <$${t.medium.toLocaleString()}
ESCALATION RULES:
${escalationLines || '- No automatic escalation rules configured.'}
OTHER RULES:
- actionDeadline: the single most important date — due date, response deadline, or dispute window. null if none found.
- escalationReasons severity: "blocking" = cannot proceed without human, "warning" = should review but can proceed, "informational" = FYI only.
- summary: exactly 3 sentences max. Sentence 1: what this document IS and who it involves. Sentence 2: what ACTION is required and by when. Sentence 3 (only if escalation): why this needs human attention. Write in plain, clear English for someone whose first language is not English. Never exceed 3 sentences.
- summary_es: the SAME summary translated to professional Latin American Spanish. Same 3-sentence structure. Preserve all names, amounts, dates, and invoice numbers exactly as-is — only translate the surrounding language.
Return ONLY JSON.`, cache_control: { type: 'ephemeral' } }],
        messages: [{ role: 'user', content: `Analyze this document:\n\nFilename: ${filename}${truncated ? '\n\n[NOTE: Document truncated to first 50,000 characters]' : ''}\n\nContent:\n${safeContent}` }],
      }),
    });

    if (!response.ok) {
      return res.status(response.status).json({ error: 'AI analysis service error' });
    }

    const data = await response.json();
    const text = data.content?.[0]?.text;
    if (!text) return res.status(500).json({ error: 'Empty response from AI' });

    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) return res.status(500).json({ error: 'Could not parse AI response' });

    try { return res.status(200).json(JSON.parse(jsonMatch[0])); }
    catch { return res.status(500).json({ error: 'Malformed AI response' }); }
  } catch {
    return res.status(500).json({ error: 'Internal error' });
  }
}
