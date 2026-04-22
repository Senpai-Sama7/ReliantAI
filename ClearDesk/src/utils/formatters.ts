import { format, formatDistanceToNow, parseISO } from 'date-fns';
import type { DocumentPriority, DocumentStatus } from '../types/document';

export function formatDateTime(dateString: string | undefined): string {
  if (!dateString) return '—';
  try { return format(parseISO(dateString), 'MMM d, yyyy h:mm a'); } catch { return dateString; }
}

export function formatRelativeTime(dateString: string | undefined): string {
  if (!dateString) return '—';
  try { return formatDistanceToNow(parseISO(dateString), { addSuffix: true }); } catch { return dateString; }
}

export function formatCurrency(amount: number | undefined | null, currency: string = 'USD'): string {
  if (amount == null) return '—';
  try { return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amount); }
  catch { return `$${amount.toLocaleString()}`; }
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}


export function getStatusLabel(status: DocumentStatus): string {
  const m: Record<DocumentStatus, string> = {
    pending: 'Pending', processing: 'Processing', review: 'In Review',
    completed: 'Completed', escalated: 'Escalated',
  };
  return m[status] || status;
}

export function getPriorityLabel(priority: DocumentPriority): string {
  const m: Record<DocumentPriority, string> = {
    critical: 'Critical', high: 'High', medium: 'Medium', low: 'Low',
  };
  return m[priority] || priority;
}

export function getDocumentTypeLabel(type: string): string {
  const m: Record<string, string> = {
    invoice: 'Invoice', statement: 'Statement', payment_confirmation: 'Payment',
    dispute: 'Dispute', credit_note: 'Credit Note', other: 'Other',
  };
  return m[type] || 'Document';
}

export function generateId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).substr(2, 9)}`;
}

export function truncateText(text: string, max: number): string {
  if (!text || text.length <= max) return text;
  return text.substring(0, max) + '…';
}

export function classNames(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(' ');
}
