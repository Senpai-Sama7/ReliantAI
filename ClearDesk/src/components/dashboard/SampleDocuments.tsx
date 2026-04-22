import { useState } from 'react';
import { FileText, Play, Eye, Download, X, FolderOpen } from 'lucide-react';
import { Button } from '../ui/Button';
import mammoth from 'mammoth';

const formats = ['All', 'PDF', 'DOCX', 'CSV', 'JSON', 'TXT'] as const;

const samples = [
  { name: 'Swift Haul Invoice', file: 'Swift Haul Invoice.docx', fmt: 'DOCX', mime: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', desc: 'Freight invoice — Word' },
  { name: 'Invoice (Swift Haul → Lone Star)', file: 'Invoice_SwiftHaul_LoneStarDist.csv', fmt: 'CSV', mime: 'text/csv', desc: 'Freight invoice — CSV' },
  { name: 'Invoice (Swift Haul → Lone Star)', file: 'Invoice_SwiftHaul_LoneStarDist.json', fmt: 'JSON', mime: 'application/json', desc: 'Freight invoice — JSON' },
  { name: 'Invoice (Swift Haul → Lone Star)', file: 'Invoice_SwiftHaul_LoneStarDist.txt', fmt: 'TXT', mime: 'text/plain', desc: 'Freight invoice — TXT' },
  { name: 'AR Statement Swift Haul', file: 'AR Statement Swift Haul.pdf', fmt: 'PDF', mime: 'application/pdf', desc: 'Receivable statement with aging buckets' },
  { name: 'AR Statement Swift Haul', file: 'AR Statement Swift Haul.docx', fmt: 'DOCX', mime: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', desc: 'AR statement — Word' },
  { name: 'AR Statement (Swift Haul / Lone Star)', file: 'AR_SwiftHaul_LoneStarDist.csv', fmt: 'CSV', mime: 'text/csv', desc: 'AR statement — CSV' },
  { name: 'AR Statement (Swift Haul / Lone Star)', file: 'AR_SwiftHaul_LoneStarDist.json', fmt: 'JSON', mime: 'application/json', desc: 'AR statement — JSON' },
  { name: 'AR Statement (Swift Haul / Lone Star)', file: 'AR_SwiftHaul_LoneStarDist.txt', fmt: 'TXT', mime: 'text/plain', desc: 'AR statement — TXT' },
  { name: 'Collections Notice', file: 'Collections Notice.pdf', fmt: 'PDF', mime: 'application/pdf', desc: 'Final notice — triggers escalation' },
  { name: 'Collections Notice', file: 'Collections Notice.docx', fmt: 'DOCX', mime: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', desc: 'Collections notice — Word' },
  { name: 'Collections (Ironclads → Panhandle)', file: 'Collections_IroncladsRG_PanhandleFreight.csv', fmt: 'CSV', mime: 'text/csv', desc: 'Collections notice — CSV' },
  { name: 'Collections (Ironclads → Panhandle)', file: 'Collections_IroncladsRG_PanhandleFreight.json', fmt: 'JSON', mime: 'application/json', desc: 'Collections notice — JSON' },
  { name: 'Collections (Ironclads → Panhandle)', file: 'Collections_IroncladsRG_PanhandleFreight.txt', fmt: 'TXT', mime: 'text/plain', desc: 'Collections notice — TXT' },
];

interface Props { onProcessFile: (file: File) => void; }

export function SampleDocuments({ onProcessFile }: Props) {
  const [open, setOpen] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [previewContent, setPreviewContent] = useState<string | null>(null);
  const [loading, setLoading] = useState<string | null>(null);
  const [fmt, setFmt] = useState<string>('All');

  const filtered = fmt === 'All' ? samples : samples.filter(s => s.fmt === fmt);

  const processNow = async (s: typeof samples[0]) => {
    setLoading(s.file);
    try {
      const r = await fetch(`/samples/${encodeURIComponent(s.file)}`);
      const blob = await r.blob();
      onProcessFile(new File([blob], s.file, { type: s.mime }));
      setOpen(false);
      setPreview(null);
    } finally { setLoading(null); }
  };

  const downloadFile = (s: typeof samples[0]) => {
    const a = document.createElement('a');
    a.href = `/samples/${encodeURIComponent(s.file)}`;
    a.download = s.file;
    a.click();
  };

  const openPreview = async (s: typeof samples[0]) => {
    if (preview === s.file) { setPreview(null); setPreviewContent(null); return; }
    setPreview(s.file);
    if (s.file.endsWith('.docx')) {
      const r = await fetch(`/samples/${encodeURIComponent(s.file)}`);
      const { value } = await mammoth.extractRawText({ arrayBuffer: await r.arrayBuffer() });
      setPreviewContent(value);
    } else if (!s.file.endsWith('.pdf')) {
      const r = await fetch(`/samples/${encodeURIComponent(s.file)}`);
      setPreviewContent(await r.text());
    } else { setPreviewContent(null); }
  };

  if (!open) {
    return (
      <div className="mt-4 pt-4 border-t border-border">
        <Button variant="secondary" size="sm" onClick={() => setOpen(true)} leftIcon={<FolderOpen className="w-3.5 h-3.5" />}>
          Try a sample document
        </Button>
        <p className="text-[11px] text-text-secondary mt-1.5">14 samples across 5 formats — no upload needed</p>
      </div>
    );
  }

  return (
    <div className="mt-4 pt-4 border-t border-border space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-text-secondary">14 samples across 5 formats — click Process to analyze directly.</p>
        <button onClick={() => { setOpen(false); setPreview(null); setPreviewContent(null); }} aria-label="Close sample documents" className="text-text-secondary hover:text-text-primary">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="flex gap-1 flex-wrap">
        {formats.map(f => (
          <button key={f} onClick={() => setFmt(f)}
            className={`px-2.5 py-1 rounded text-[11px] transition-colors ${fmt === f ? 'bg-accent/20 text-text-primary font-medium' : 'text-text-secondary hover:text-text-primary hover:bg-surface'}`}>
            {f}
          </button>
        ))}
      </div>

      <div className={`flex gap-3 ${preview ? '' : ''}`}>
        {/* Sample list */}
        <div className={`grid gap-1.5 max-h-[28rem] overflow-y-auto ${preview ? 'w-1/2' : 'w-full'}`}>
          {filtered.map(s => (
            <div key={s.file} className={`flex items-center gap-3 bg-bg border rounded-lg px-3 py-2 transition-colors ${preview === s.file ? 'border-accent' : 'border-border hover:border-border-hover'}`}>
              <FileText className="w-3.5 h-3.5 text-text-secondary flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-text-primary truncate">{s.name}</p>
                <p className="text-[11px] text-text-secondary">{s.desc} · <span className="font-mono">{s.fmt}</span></p>
              </div>
              <div className="flex gap-1.5 flex-shrink-0">
                <button onClick={() => openPreview(s)} aria-label={`Preview ${s.name} ${s.fmt}`}
                    className={`p-1.5 rounded transition-colors ${preview === s.file ? 'text-accent bg-accent/10' : 'text-text-secondary hover:text-text-primary hover:bg-surface'}`} title="Preview">
                  <Eye className="w-3.5 h-3.5" />
                </button>
                <button onClick={() => downloadFile(s)} aria-label={`Download ${s.name} ${s.fmt}`}
                    className="p-1.5 rounded text-text-secondary hover:text-text-primary hover:bg-surface transition-colors" title="Download">
                  <Download className="w-3.5 h-3.5" />
                </button>
                <Button variant="primary" size="sm" onClick={() => processNow(s)} disabled={loading === s.file}
                  leftIcon={<Play className="w-3 h-3" />}>
                  {loading === s.file ? '…' : 'Process'}
                </Button>
              </div>
            </div>
          ))}
        </div>

        {/* Preview panel — side by side */}
        {preview && (
          <div className="w-1/2 border border-border rounded-lg overflow-hidden bg-bg flex flex-col max-h-[28rem]">
            <div className="flex items-center justify-between px-3 py-2 border-b border-border bg-surface">
              <p className="text-xs text-text-primary truncate font-medium">{preview}</p>
              <button onClick={() => { setPreview(null); setPreviewContent(null); }} aria-label="Close preview" className="text-text-secondary hover:text-text-primary">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
            <div className="flex-1 overflow-hidden">
              {preview.endsWith('.pdf') ? (
                <iframe src={`/samples/${encodeURIComponent(preview)}`} className="w-full h-[25rem] border-0" title="Sample preview" />
              ) : preview.endsWith('.docx') ? (
                <pre className="p-4 text-xs text-text-primary font-mono whitespace-pre-wrap">{previewContent ?? 'Loading…'}</pre>
              ) : (
                <pre className="p-4 text-xs text-text-primary font-mono whitespace-pre-wrap">{previewContent ?? 'Loading…'}</pre>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
