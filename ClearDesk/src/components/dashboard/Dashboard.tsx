import { useState, useRef, useEffect } from 'react';
import { Layout } from './Layout';
import { StatsOverview } from './StatsOverview';

import { FilterPanel } from './FilterPanel';
import { DocumentCard } from './DocumentCard';
import { DocumentDetail } from './DocumentDetail';
import { ExportPanel } from './ExportPanel';
import { FileUpload } from '../upload/FileUpload';
import { SettingsPanel } from './SettingsPanel';
import { HelpPanel } from './HelpPanel';
import { AboutPanel } from './AboutPanel';
import { ChatPanel } from './ChatPanel';
import { useDocuments } from '../../contexts/DocumentContext';
import { Button } from '../ui/Button';
import { Plus, Upload } from 'lucide-react';

export function Dashboard() {
  const { filteredDocuments, selectDocument } = useDocuments();
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [isExportOpen, setIsExportOpen] = useState(false);
  const [activeView, setActiveView] = useState('dashboard');

  const handleFilesRef = useRef<((files: File[]) => void) | null>(null);

  const handleCardClick = (id: string) => {
    selectDocument(id);
    setIsDetailOpen(true);
  };

  const handleNavigate = (view: string) => {
    setActiveView(view);
  };

  return (
    <Layout onNavigate={handleNavigate} activeView={activeView}>
      {activeView === 'settings' ? (
        <SettingsPanel />
      ) : activeView === 'help' ? (
        <HelpPanel />
      ) : activeView === 'about' ? (
        <AboutPanel />
      ) : activeView === 'upload' ? (
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
            <h1 className="font-heading text-2xl font-bold text-text-primary">Upload &amp; Process</h1>
            <p className="text-sm text-text-secondary mt-1">Drop files for instant AI analysis.</p>
          </div>

          <div className="bg-surface border border-border rounded-lg p-6 mb-6">
            <FileUpload onHandleFiles={(h) => { handleFilesRef.current = h; }} />
          </div>

          {/* Recently processed — upload confirmation */}
          {filteredDocuments.length > 0 && (
            <div>
              <h2 className="text-sm font-medium text-text-secondary mb-3">Recently Processed</h2>
              <div className="space-y-1.5">
                {filteredDocuments.slice(0, 5).map(doc => (
                  <button key={doc.id} onClick={() => handleCardClick(doc.id)}
                    className="w-full flex items-center gap-3 bg-surface border border-border rounded-lg px-4 py-2.5 text-left hover:border-border-hover transition-colors">
                    <span className={`w-2 h-2 rounded-full flex-shrink-0 ${
                      doc.priority === 'critical' ? 'bg-[#FF4444]' : doc.priority === 'high' ? 'bg-[#FF8800]' : doc.priority === 'medium' ? 'bg-[#FFCC00]' : 'bg-accent'
                    }`} />
                    <span className="text-sm text-text-primary truncate flex-1">{doc.originalName}</span>
                    <span className="text-[11px] text-text-secondary capitalize flex-shrink-0">{doc.status.replace('-', ' ')}</span>
                  </button>
                ))}
              </div>
              <button onClick={() => handleNavigate('documents')} className="mt-3 text-xs text-accent hover:text-accent/80 transition-colors">
                View all {filteredDocuments.length} documents →
              </button>
            </div>
          )}
        </div>
      ) : activeView === 'documents' ? (
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="font-heading text-2xl font-bold text-text-primary">Documents</h1>
              <p className="text-sm text-text-secondary mt-1">
                {filteredDocuments.length} document{filteredDocuments.length !== 1 ? 's' : ''} processed
              </p>
            </div>
            <Button variant="primary" size="md" onClick={() => handleNavigate('upload')} leftIcon={<Plus className="w-4 h-4" />}>
              Upload More
            </Button>
          </div>

          <FilterPanel onExport={() => setIsExportOpen(true)} />

          {filteredDocuments.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredDocuments.map((doc, i) => (
                <DocumentCard
                  key={doc.id}
                  document={doc}
                  onClick={() => handleCardClick(doc.id)}
                  style={{ animationDelay: `${i * 60}ms` }}
                />
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-20">
              <Upload className="w-8 h-8 text-text-secondary mb-4" />
              <p className="text-text-secondary text-sm">No documents yet</p>
              <Button variant="secondary" size="sm" className="mt-4" onClick={() => handleNavigate('upload')}>
                Upload your first document
              </Button>
            </div>
          )}
        </div>
      ) : (
        <DashboardHome onNavigate={handleNavigate} />
      )}

      <DocumentDetail isOpen={isDetailOpen} onClose={() => { setIsDetailOpen(false); selectDocument(null); }} />
      <ExportPanel isOpen={isExportOpen} onClose={() => setIsExportOpen(false)} />
      <ChatPanel />
    </Layout>
  );
}

const faqs = [
  { q: 'What file formats are supported?', a: 'PDF, PNG, JPG, WEBP, DOCX, XLSX, CSV, EML, TXT, JSON, and Markdown.' },
  { q: 'How does priority scoring work?', a: 'Claude AI scores each document as Critical, High, Medium, or Low based on dollar thresholds, due dates, and escalation triggers you configure in Settings.' },
  { q: 'What languages are summaries generated in?', a: 'Every document gets a 3-sentence summary in both English and Spanish automatically.' },
  { q: 'Is my data stored on a server?', a: 'Documents live in your browser by default. Optional Cloudflare KV sync uses a signed browser session and short-lived share codes instead of a public UUID lookup.' },
  { q: 'What AI models are used?', a: 'Claude Sonnet 4 for document analysis and Claude Haiku 4.5 for the chat assistant. API keys stay server-side.' },
];

const actions = [
  { icon: '🔍', title: 'Insights', desc: 'View entity extraction, priority scoring, and confidence analysis.', nav: 'documents' },
  { icon: '📝', title: 'Summaries', desc: 'Read dual-language EN/ES summaries for every document.', nav: 'documents' },
  { icon: '🚨', title: 'Escalations', desc: 'Review flagged disputes, low-confidence items, and overdue amounts.', nav: 'documents' },
];

const infoCards = [
  { icon: '💬', title: 'AI Chat', desc: 'Ask questions about your AR queue — get answers, draft emails, surface what needs attention.' },
  { icon: '📊', title: 'Classification', desc: 'Invoices, statements, payment confirmations, disputes, and credit notes — sorted automatically.' },
  { icon: '📤', title: 'Export', desc: 'Generate filtered summary reports for standups, reviews, or downstream systems.' },
];

type ChartMetric = 'priority' | 'status' | 'type' | 'amount';
const chartOptions: { id: ChartMetric; label: string }[] = [
  { id: 'priority', label: 'By Priority' },
  { id: 'status', label: 'By Status' },
  { id: 'type', label: 'By Type' },
  { id: 'amount', label: 'Top Amounts' },
];

function DashboardHome({ onNavigate }: { onNavigate: (v: string) => void }) {
  const [visible, setVisible] = useState(false);
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [chartMetric, setChartMetric] = useState<ChartMetric>('priority');
  const { state } = useDocuments();
  const docs = state.documents;

  useEffect(() => { requestAnimationFrame(() => setVisible(true)); }, []);

  const chartData = (() => {
    if (chartMetric === 'priority') {
      const groups = { critical: 0, high: 0, medium: 0, low: 0 };
      docs.forEach(d => { if (d.priority in groups) groups[d.priority as keyof typeof groups]++; });
      return [
        { label: 'Critical', value: groups.critical, color: '#FF4444' },
        { label: 'High', value: groups.high, color: '#FF8800' },
        { label: 'Medium', value: groups.medium, color: '#FFCC00' },
        { label: 'Low', value: groups.low, color: '#00FF94' },
      ];
    }
    if (chartMetric === 'status') {
      const groups: Record<string, number> = {};
      docs.forEach(d => { groups[d.status] = (groups[d.status] || 0) + 1; });
      const colors: Record<string, string> = { pending: '#6B6B80', processing: '#FFCC00', 'in-review': '#FF8800', completed: '#00FF94', escalated: '#FF4444' };
      return Object.entries(groups).map(([k, v]) => ({ label: k.replace('-', ' '), value: v, color: colors[k] || '#6B6B80' }));
    }
    if (chartMetric === 'type') {
      const groups: Record<string, number> = {};
      docs.forEach(d => { groups[d.type] = (groups[d.type] || 0) + 1; });
      const palette = ['#00FF94', '#FF8800', '#FFCC00', '#FF4444', '#8B5CF6', '#6B6B80'];
      return Object.entries(groups).map(([k, v], i) => ({ label: k.replace('-', ' '), value: v, color: palette[i % palette.length] }));
    }
    // amount — top 5 by dollar value
    return [...docs]
      .filter(d => d.extractedData?.amount)
      .sort((a, b) => (b.extractedData?.amount ?? 0) - (a.extractedData?.amount ?? 0))
      .slice(0, 5)
      .map((d, i) => ({
        label: d.extractedData?.customerName || d.originalName.slice(0, 15),
        value: d.extractedData?.amount ?? 0,
        color: ['#00FF94', '#FF8800', '#FFCC00', '#8B5CF6', '#FF4444'][i],
      }));
  })();

  const maxVal = Math.max(...chartData.map(d => d.value), 1);

  return (
    <div className="max-w-4xl mx-auto py-8">
      {/* Animated header */}
      <div className="text-center mb-12">
        <h1
          className="font-heading text-5xl md:text-6xl font-bold text-text-primary transition-all duration-700"
          style={{ opacity: visible ? 1 : 0, transform: visible ? 'translateY(0)' : 'translateY(20px)' }}
        >
          Clear<span className="text-accent-text">Desk</span>
        </h1>
        <p
          className="mt-4 text-lg text-text-secondary max-w-xl mx-auto transition-all duration-700 delay-200"
          style={{ opacity: visible ? 1 : 0, transform: visible ? 'translateY(0)' : 'translateY(20px)' }}
        >
          AI-powered accounts receivable processing — upload any document, get structured intelligence in seconds.
        </p>
        <div
          className="mt-6 flex items-center justify-center gap-2 transition-all duration-700 delay-300"
          style={{ opacity: visible ? 1 : 0 }}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
          <span className="font-mono text-[11px] text-text-secondary tracking-widest uppercase">Powered by Claude</span>
        </div>
      </div>

      {/* Stats dashboard */}
      <div
        className="mb-8 transition-all duration-700 delay-300"
        style={{ opacity: visible ? 1 : 0, transform: visible ? 'translateY(0)' : 'translateY(16px)' }}
      >
        <StatsOverview />
      </div>

      {/* Chart with metric selector */}
      <div
        className="bg-surface border border-border rounded-lg p-5 mb-10 transition-all duration-700 delay-[400ms]"
        style={{ opacity: visible ? 1 : 0, transform: visible ? 'translateY(0)' : 'translateY(16px)' }}
      >
        <div className="flex items-center justify-between mb-5 flex-wrap gap-2">
          <h2 className="text-sm font-medium text-text-primary">Analytics</h2>
          <div className="flex gap-1">
            {chartOptions.map(o => (
              <button
                key={o.id}
                onClick={() => setChartMetric(o.id)}
                className={`px-3 py-1 rounded-md text-xs transition-colors ${
                  chartMetric === o.id
                    ? 'bg-accent/20 text-text-primary font-medium'
                    : 'text-text-secondary hover:text-text-primary hover:bg-surface'
                }`}
              >
                {o.label}
              </button>
            ))}
          </div>
        </div>
        {docs.length === 0 ? (
          <p className="text-sm text-text-secondary text-center py-8">Upload documents to see analytics</p>
        ) : (
          <div className="space-y-3">
            {chartData.map((d, i) => (
              <div key={d.label + i} className="flex items-center gap-3">
                <span className="text-xs text-text-secondary w-20 truncate capitalize text-right">{d.label}</span>
                <div className="flex-1 h-7 bg-bg rounded overflow-hidden">
                  <div
                    className="h-full rounded transition-all duration-700 ease-out flex items-center px-2"
                    style={{
                      width: `${Math.max((d.value / maxVal) * 100, d.value > 0 ? 8 : 0)}%`,
                      backgroundColor: d.color + '30',
                      borderLeft: `3px solid ${d.color}`,
                      transitionDelay: `${500 + i * 100}ms`,
                    }}
                  >
                    <span className="font-mono text-xs" style={{ color: d.color }}>
                      {chartMetric === 'amount' ? `$${d.value.toLocaleString()}` : d.value}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Action buttons — visually distinct */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
        {actions.map((a, i) => (
          <button
            key={a.title}
            onClick={() => onNavigate(a.nav)}
            className="group bg-accent/5 border border-accent/20 rounded-lg p-4 text-left hover:bg-accent/10 hover:border-accent/40 transition-all duration-300 cursor-pointer"
            style={{
              opacity: visible ? 1 : 0,
              transform: visible ? 'translateY(0)' : 'translateY(16px)',
              transitionDelay: `${600 + i * 80}ms`,
              transitionDuration: '600ms',
            }}
          >
            <div className="flex items-center justify-between">
              <span className="text-xl">{a.icon}</span>
              <span className="text-accent text-sm opacity-60 group-hover:opacity-100 group-hover:translate-x-1 transition-all">→</span>
            </div>
            <h3 className="mt-2 text-sm font-medium text-text-primary">{a.title}</h3>
            <p className="mt-1 text-[12px] text-text-secondary leading-relaxed">{a.desc}</p>
          </button>
        ))}
      </div>

      {/* Info cards — muted, non-interactive */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-16">
        {infoCards.map((c, i) => (
          <div
            key={c.title}
            className="bg-surface border border-border rounded-lg p-4"
            style={{
              opacity: visible ? 1 : 0,
              transform: visible ? 'translateY(0)' : 'translateY(16px)',
              transitionDelay: `${840 + i * 80}ms`,
              transitionDuration: '600ms',
            }}
          >
            <span className="text-xl">{c.icon}</span>
            <h3 className="mt-2 text-sm font-medium text-text-primary">{c.title}</h3>
            <p className="mt-1 text-[12px] text-text-secondary leading-relaxed">{c.desc}</p>
          </div>
        ))}
      </div>

      {/* FAQ */}
      <div
        className="transition-all duration-700"
        style={{ opacity: visible ? 1 : 0, transitionDelay: '1100ms' }}
      >
        <h2 className="font-heading text-lg font-semibold text-text-primary mb-4">FAQ</h2>
        <div className="space-y-1">
          {faqs.map((f, i) => (
            <div key={i} className="border border-border rounded-lg overflow-hidden">
              <button
                onClick={() => setOpenFaq(openFaq === i ? null : i)}
                className="w-full text-left px-4 py-3 flex items-center justify-between hover:bg-surface/50 transition-colors"
              >
                <span className="text-sm text-text-primary">{f.q}</span>
                <span className="text-text-secondary text-xs ml-4 flex-shrink-0">{openFaq === i ? '−' : '+'}</span>
              </button>
              {openFaq === i && (
                <div className="px-4 pb-3">
                  <p className="text-[13px] text-text-secondary leading-relaxed">{f.a}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
