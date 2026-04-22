export type DocumentStatus = 'pending' | 'processing' | 'review' | 'completed' | 'escalated';
export type DocumentPriority = 'critical' | 'high' | 'medium' | 'low';
export type DocumentType = 'invoice' | 'statement' | 'payment_confirmation' | 'dispute' | 'credit_note' | 'other';

export interface ExtractedData {
  customerName?: string | null;
  customerId?: string | null;
  invoiceNumber?: string | null;
  invoiceDate?: string | null;
  dueDate?: string | null;
  amount?: number | null;
  currency?: string | null;
  accountNumber?: string | null;
  paymentTerms?: string | null;
  notes?: string | null;
  confidence: number;
}

export interface EscalationReason {
  type: 'low_confidence' | 'missing_data' | 'ambiguous' | 'high_value' | 'manual_review';
  severity?: 'blocking' | 'warning' | 'informational';
  description: string;
  field?: string;
}

export interface Document {
  id: string;
  filename: string;
  originalName: string;
  type: DocumentType;
  status: DocumentStatus;
  priority: DocumentPriority;
  fileUrl?: string;
  fileContent?: string;
  extractedData?: ExtractedData;
  actionDeadline?: string | null;
  escalationReasons?: EscalationReason[];
  isEscalated: boolean;
  assignee?: string;
  createdAt: string;
  updatedAt: string;
  processedAt?: string;
  notes?: string;
  summaryEs?: string;
  tags: string[];
}

export interface DocumentFilters {
  status?: DocumentStatus | 'all';
  type?: DocumentType | 'all';
  priority?: DocumentPriority | 'all';
  assignee?: string | 'all';
  searchQuery?: string;
  dateRange?: {
    start: string;
    end: string;
  };
}

export interface DailySummary {
  date: string;
  totalDocuments: number;
  processedCount: number;
  escalatedCount: number;
  pendingCount: number;
  criticalCount: number;
  byType: Record<DocumentType, number>;
  byAssignee: Record<string, number>;
  averageProcessingTime?: number;
}

export interface ClaudeAnalysisResponse {
  documentType: DocumentType;
  priority: DocumentPriority;
  extractedData: ExtractedData;
  actionDeadline: string | null;
  escalationReasons: EscalationReason[];
  requiresHumanReview: boolean;
  confidence: number;
  summary: string;
  summary_es?: string;
}

export interface UploadProgress {
  fileId: string;
  fileName: string;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
}
