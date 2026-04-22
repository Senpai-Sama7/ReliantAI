import type { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) return res.status(500).json({ error: 'ANTHROPIC_API_KEY not configured' });

  try {
    if (!req.body || typeof req.body !== 'object') return res.status(400).json({ error: 'Invalid request body' });
    const { messages, context } = req.body;
    if (!messages?.length) return res.status(400).json({ error: 'messages required' });
    const safeMessages = messages.slice(-50);
    const safeContext = typeof context === 'string' ? context.slice(0, 50000) : '';

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-beta': 'prompt-caching-2024-07-31',
      },
      body: JSON.stringify({
        model: 'claude-haiku-4-5-20251001',
        max_tokens: 1024,
        system: [{ type: 'text', cache_control: { type: 'ephemeral' }, text: `You are ClearDesk Assistant. You have access to the user's AR document dashboard. Answer questions about their documents, flag urgent items, draft follow-up communications, and provide operational recommendations. Be direct and brief. You are talking to a senior operations manager.\n\nWhen drafting emails or follow-ups, write in plain, clear English suitable for multilingual teams.\n\nCURRENT DASHBOARD STATE:\n${safeContext || 'No documents loaded yet.'}` }],
        messages: safeMessages,
      }),
    });

    if (!response.ok) {
      return res.status(response.status).json({ error: 'Chat service error' });
    }

    const data = await response.json();
    const text = data.content?.[0]?.text;
    if (!text) return res.status(500).json({ error: 'Empty response' });

    return res.json({ response: text });
  } catch {
    return res.status(500).json({ error: 'Internal error' });
  }
}
