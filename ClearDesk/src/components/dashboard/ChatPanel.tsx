import { useState, useRef, useEffect, useCallback } from 'react';
import { MessageCircle, X, Send, Loader2, Trash2 } from 'lucide-react';
import { useDocuments } from '../../contexts/DocumentContext';
import type { Document } from '../../types/document';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

const STORAGE_KEY = 'cleardesk_chat';
const SUGGESTIONS = [
  "What needs attention today?",
  "Summarize all escalated items",
  "Who is most overdue?",
  "Draft a collections follow-up for the largest outstanding invoice",
];

function buildContext(docs: Document[], query: string): string {
  const q = query.toLowerCase();
  const total = docs.length;
  const escalated = docs.filter(d => d.isEscalated || d.status === 'escalated');
  const byPriority = { critical: 0, high: 0, medium: 0, low: 0 };
  const byStatus = { pending: 0, processing: 0, review: 0, completed: 0, escalated: 0 };
  docs.forEach(d => { byPriority[d.priority]++; byStatus[d.status]++; });

  // Always include summary stats
  let ctx = `SUMMARY: ${total} documents total. Priority: ${byPriority.critical} critical, ${byPriority.high} high, ${byPriority.medium} medium, ${byPriority.low} low. Status: ${byStatus.escalated} escalated, ${byStatus.review} in review, ${byStatus.pending} pending, ${byStatus.completed} completed.\n\n`;

  // Smart context injection — only relevant docs
  let relevant: Document[];
  if (/escalat|urgent|attention|flag/i.test(q)) {
    relevant = escalated;
  } else if (/overdue|past.?due|late/i.test(q)) {
    relevant = docs.filter(d => {
      if (!d.extractedData?.dueDate && !d.actionDeadline) return false;
      const due = new Date(d.actionDeadline || d.extractedData!.dueDate!);
      return due < new Date();
    });
  } else if (/critical/i.test(q)) {
    relevant = docs.filter(d => d.priority === 'critical');
  } else if (/high/i.test(q)) {
    relevant = docs.filter(d => d.priority === 'high' || d.priority === 'critical');
  } else {
    // Keyword match against customer name, type, filename, notes
    relevant = docs.filter(d => {
      const haystack = [
        d.extractedData?.customerName, d.type, d.filename, d.originalName,
        d.extractedData?.invoiceNumber, d.notes, d.assignee,
      ].filter(Boolean).join(' ').toLowerCase();
      return q.split(/\s+/).some(w => w.length > 2 && haystack.includes(w));
    });
    // Fallback: if no keyword match, send top 10 by priority
    if (!relevant.length) {
      const order = { critical: 0, high: 1, medium: 2, low: 3 };
      relevant = [...docs].sort((a, b) => order[a.priority] - order[b.priority]).slice(0, 10);
    }
  }

  // Cap at 15 docs to keep tokens reasonable
  relevant = relevant.slice(0, 15);

  if (relevant.length) {
    ctx += `RELEVANT DOCUMENTS (${relevant.length}):\n`;
    relevant.forEach((d, i) => {
      const e = d.extractedData;
      ctx += `${i + 1}. "${d.originalName}" | Type: ${d.type} | Priority: ${d.priority} | Status: ${d.status}`;
      if (e?.customerName) ctx += ` | Customer: ${e.customerName}`;
      if (e?.amount != null) ctx += ` | Amount: ${e.currency || '$'}${e.amount.toLocaleString()}`;
      if (e?.dueDate) ctx += ` | Due: ${e.dueDate}`;
      if (d.actionDeadline) ctx += ` | Deadline: ${d.actionDeadline.split('T')[0]}`;
      if (d.isEscalated && d.escalationReasons?.length) ctx += ` | Escalation: ${d.escalationReasons.map(r => r.description).join('; ')}`;
      if (e?.invoiceNumber) ctx += ` | Invoice#: ${e.invoiceNumber}`;
      ctx += '\n';
    });
  }

  return ctx;
}

export function ChatPanel() {
  const { state } = useDocuments();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); } catch { return []; }
  });
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => { localStorage.setItem(STORAGE_KEY, JSON.stringify(messages)); }, [messages]);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, open]);
  useEffect(() => { if (open) inputRef.current?.focus(); }, [open]);

  const send = useCallback(async (text: string) => {
    const userMsg: ChatMessage = { role: 'user', content: text };
    const history = [...messages, userMsg];
    setMessages(history);
    setInput('');
    setLoading(true);

    try {
      const context = buildContext(state.documents, text);
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: history, context }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Chat failed');
      setMessages([...history, { role: 'assistant', content: data.response }]);
    } catch (err) {
      setMessages([...history, { role: 'assistant', content: `Error: ${err instanceof Error ? err.message : 'Something went wrong'}` }]);
    } finally {
      setLoading(false);
    }
  }, [messages, state.documents]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    send(input.trim());
  };

  const clearChat = () => { setMessages([]); localStorage.removeItem(STORAGE_KEY); };

  // Floating button when closed
  if (!open) return (
    <button
      onClick={() => setOpen(true)}
      className="fixed bottom-6 right-6 z-[9999] w-14 h-14 rounded-full bg-accent text-[#0A0A0F] flex items-center justify-center shadow-lg shadow-accent/25 hover:scale-105 transition-transform"
      aria-label="Open AI chat"
    >
      <MessageCircle className="w-6 h-6" />
    </button>
  );

  return (
    <div className="fixed bottom-6 right-6 z-[9999] w-[400px] h-[560px] max-h-[80vh] bg-surface border border-border rounded-2xl shadow-2xl flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-2">
          <MessageCircle className="w-4 h-4 text-accent" />
          <span className="font-heading text-sm font-semibold text-text-primary">ClearDesk AI</span>
        </div>
        <div className="flex items-center gap-1">
          {messages.length > 0 && (
            <button onClick={clearChat} className="p-1.5 text-text-secondary hover:text-text-primary rounded" aria-label="Clear chat"><Trash2 className="w-3.5 h-3.5" /></button>
          )}
          <button onClick={() => setOpen(false)} className="p-1.5 text-text-secondary hover:text-text-primary rounded" aria-label="Close chat"><X className="w-4 h-4" /></button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {messages.length === 0 ? (
          <div className="flex flex-col gap-2 pt-4">
            <p className="text-xs text-text-secondary mb-2">Ask anything about your documents:</p>
            {SUGGESTIONS.map(s => (
              <button key={s} onClick={() => send(s)} disabled={loading}
                className="text-left text-sm px-3 py-2 rounded-lg border border-border hover:border-accent/40 hover:bg-accent/5 text-text-secondary hover:text-text-primary transition-colors">
                {s}
              </button>
            ))}
          </div>
        ) : (
          messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] rounded-xl px-3 py-2 text-sm whitespace-pre-wrap ${
                m.role === 'user'
                  ? 'bg-accent/15 text-text-primary'
                  : 'bg-[#1a1a24] text-text-primary'
              }`}>
                {m.content}
              </div>
            </div>
          ))
        )}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-[#1a1a24] rounded-xl px-3 py-2">
              <Loader2 className="w-4 h-4 text-accent animate-spin" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="px-4 py-3 border-t border-border">
        <div className="flex items-end gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(e); } }}
            placeholder="Ask about your documents..."
            rows={1}
            className="flex-1 resize-none bg-[#0A0A0F] border border-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder:text-text-secondary focus:outline-none focus:border-accent/50"
            aria-label="Chat message"
          />
          <button type="submit" disabled={!input.trim() || loading}
            className="p-2 rounded-lg bg-accent text-[#0A0A0F] disabled:opacity-30 hover:bg-accent/90 transition-colors"
            aria-label="Send message">
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
}
