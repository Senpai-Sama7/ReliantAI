import { useCallback, useState, useRef, useEffect } from 'react';
import { Upload, File, X, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { classNames, formatFileSize, generateId } from '../../utils/formatters';
import { isValidDocumentFile, extractTextFromFile } from '../../utils/fileProcessing';
import { claudeService } from '../../services/claudeService';
import { useDocuments } from '../../contexts/DocumentContext';

const ANALYSIS_PHASES = [
  'Extracting document structure…',
  'Analyzing priority…',
  'Generating summary…',
] as const;

interface UploadingFile {
  id: string;
  file: File;
  status: 'reading' | 'analyzing' | 'done' | 'error';
  statusText?: string;
  error?: string;
}

export function FileUpload({ onHandleFiles }: { onHandleFiles?: (handler: (files: File[]) => void) => void } = {}) {
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<UploadingFile[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const { addDocument, updateDocument } = useDocuments();

  const setStatus = (id: string, status: UploadingFile['status'], extra?: Partial<UploadingFile>) =>
    setFiles(p => p.map(f => f.id === id ? { ...f, status, ...extra } : f));

  const processFile = async (uf: UploadingFile) => {
    try {
      const isImage = uf.file.type.startsWith('image/') || /\.(png|jpe?g|tiff?)$/i.test(uf.file.name);
      setStatus(uf.id, 'reading', { statusText: isImage ? 'Running OCR on image — this may take 20–30 seconds…' : 'Reading file contents…' });
      const content = await extractTextFromFile(uf.file);

      if (!content.trim()) {
        setStatus(uf.id, 'error', { error: `No readable text found in ${uf.file.name}. Try a text-based file.` });
        return;
      }

      const docId = addDocument({
        filename: uf.file.name, originalName: uf.file.name,
        type: 'other', status: 'processing', priority: 'medium',
        fileContent: content, isEscalated: false, tags: [],
      });

      // Cycle through analysis phases on a timer
      setStatus(uf.id, 'analyzing', { statusText: ANALYSIS_PHASES[0] });
      let phase = 0;
      const phaseTimer = setInterval(() => {
        phase = Math.min(phase + 1, ANALYSIS_PHASES.length - 1);
        setStatus(uf.id, 'analyzing', { statusText: ANALYSIS_PHASES[phase] });
      }, 2500);

      try {
        const analysis = await claudeService.analyzeDocument(content, uf.file.name);
        clearInterval(phaseTimer);
        updateDocument(docId, {
          type: analysis.documentType, priority: analysis.priority,
          status: analysis.requiresHumanReview ? 'escalated' : 'completed',
          extractedData: analysis.extractedData,
          actionDeadline: analysis.actionDeadline,
          escalationReasons: analysis.escalationReasons,
          isEscalated: analysis.requiresHumanReview,
          processedAt: new Date().toISOString(),
          notes: analysis.summary,
          summaryEs: analysis.summary_es,
        });
        setStatus(uf.id, 'done', { statusText: 'Complete' });
      } catch (err) {
        clearInterval(phaseTimer);
        const msg = err instanceof Error ? err.message : 'Unknown error';
        const specific = msg.includes('API key') ? 'Server missing ANTHROPIC_API_KEY — contact admin.'
          : msg.includes('401') ? 'Invalid API key configured on server.'
          : msg.includes('429') ? 'Rate limited by Claude API — wait a moment and retry.'
          : msg.includes('500') ? 'Claude API returned a server error — retry shortly.'
          : msg.includes('Failed to fetch') || msg.includes('NetworkError') ? 'Network error — check your connection.'
          : `AI analysis failed: ${msg}`;
        updateDocument(docId, { status: 'pending', notes: `${specific} Document saved — retry later.` });
        setStatus(uf.id, 'error', { error: specific });
      }
    } catch (error) {
      const msg = error instanceof Error ? error.message : 'Failed to read file';
      setStatus(uf.id, 'error', { error: msg });
    }
  };

  const handleFiles = useCallback((fileList: File[]) => {
    const MAX_SIZE = 25 * 1024 * 1024; // 25MB
    const valid: UploadingFile[] = fileList.filter(f => isValidDocumentFile(f) && f.size <= MAX_SIZE)
      .map(file => ({ id: generateId(), file, status: 'reading' as const }));
    const invalid: UploadingFile[] = fileList.filter(f => !isValidDocumentFile(f) || f.size > MAX_SIZE)
      .map(file => ({ id: generateId(), file, status: 'error' as const, error: file.size > MAX_SIZE ? 'File exceeds 25MB limit' : 'Unsupported file type' }));

    setFiles(p => [...p, ...valid, ...invalid]);
    valid.forEach(processFile);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Expose handleFiles to parent
  useEffect(() => { onHandleFiles?.((files) => handleFiles(files)); }, [handleFiles, onHandleFiles]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(Array.from(e.dataTransfer.files));
  }, [handleFiles]);

  return (
    <div className="space-y-4">
      <div
        onDragEnter={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={(e) => { e.preventDefault(); setIsDragging(false); }}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={classNames(
          'border border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
          isDragging ? 'border-accent bg-accent/5' : 'border-border hover:border-border-hover'
        )}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.txt,.csv,.jpg,.jpeg,.png,.tif,.tiff,.doc,.docx,.xls,.xlsx,.eml"
          onChange={(e) => { handleFiles(Array.from(e.target.files || [])); if (inputRef.current) inputRef.current.value = ''; }}
          className="hidden"
        />
        <Upload className={classNames('w-8 h-8 mx-auto mb-3', isDragging ? 'text-accent' : 'text-text-secondary')} />
        <p className="text-sm text-text-primary mb-1">Drop files here or click to browse</p>
        <p className="text-xs text-text-secondary">PDF, Word, Excel, images (OCR), email (.eml), TXT, CSV</p>
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((f) => (
            <div key={f.id} className="flex items-center gap-3 bg-surface border border-border rounded-lg px-4 py-3">
              {f.status === 'done' ? <CheckCircle className="w-4 h-4 text-accent flex-shrink-0" /> :
               f.status === 'error' ? <AlertCircle className="w-4 h-4 text-danger flex-shrink-0" /> :
               f.status === 'analyzing' ? <Loader2 className="w-4 h-4 text-status-processing animate-spin flex-shrink-0" /> :
               <File className="w-4 h-4 text-text-secondary flex-shrink-0" />}
              <div className="flex-1 min-w-0">
                <p className="text-sm text-text-primary truncate">{f.file.name}</p>
                <p className={classNames('text-[11px]', f.status === 'error' ? 'text-danger' : 'text-text-secondary')}>
                  {formatFileSize(f.file.size)}
                  {(f.status === 'analyzing' || f.status === 'reading') && ` · ${f.statusText || 'Processing…'}`}
                  {f.status === 'error' && ` · ${f.error}`}
                  {f.status === 'done' && ' · ✓ Processed'}
                </p>
              </div>
              <button onClick={() => setFiles(p => p.filter(x => x.id !== f.id))} className="text-text-secondary hover:text-text-primary flex-shrink-0">
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
