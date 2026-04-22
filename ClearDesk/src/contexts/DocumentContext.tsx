import React, { createContext, useContext, useReducer, useCallback, useMemo, useEffect, useRef } from 'react';
import type { Document, DocumentFilters, DocumentStatus, DailySummary } from '../types/document';
import { generateId } from '../utils/formatters';
import { initSyncSession, syncToKV, pullFromKV } from '../services/syncService';
const STORAGE_KEY = 'cleardesk_documents';

function loadDocuments(): Document[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch { return []; }
}

function saveDocuments(docs: Document[]) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(docs)); }
  catch { /* QuotaExceededError — localStorage full, skip persist */ }
}

interface DocumentState {
  documents: Document[];
  filters: DocumentFilters;
  selectedDocumentId: string | null;
  isLoading: boolean;
  error: string | null;
}

type DocumentAction =
  | { type: 'SET_DOCUMENTS'; payload: Document[] }
  | { type: 'ADD_DOCUMENT'; payload: Document }
  | { type: 'UPDATE_DOCUMENT'; payload: { id: string; updates: Partial<Document> } }
  | { type: 'DELETE_DOCUMENT'; payload: string }
  | { type: 'SET_FILTERS'; payload: Partial<DocumentFilters> }
  | { type: 'CLEAR_FILTERS' }
  | { type: 'SELECT_DOCUMENT'; payload: string | null }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'BULK_UPDATE_STATUS'; payload: { ids: string[]; status: DocumentStatus } }
  | { type: 'BULK_ASSIGN'; payload: { ids: string[]; assignee: string } };

const defaultFilters: DocumentFilters = {
  status: 'all',
  type: 'all',
  priority: 'all',
  assignee: 'all',
  searchQuery: '',
};

function documentReducer(state: DocumentState, action: DocumentAction): DocumentState {
  switch (action.type) {
    case 'SET_DOCUMENTS':
      return { ...state, documents: action.payload };
    case 'ADD_DOCUMENT':
      return { ...state, documents: [action.payload, ...state.documents] };
    case 'UPDATE_DOCUMENT':
      return {
        ...state,
        documents: state.documents.map((doc) =>
          doc.id === action.payload.id
            ? { ...doc, ...action.payload.updates, updatedAt: new Date().toISOString() }
            : doc
        ),
      };
    case 'DELETE_DOCUMENT':
      return {
        ...state,
        documents: state.documents.filter((doc) => doc.id !== action.payload),
        selectedDocumentId: state.selectedDocumentId === action.payload ? null : state.selectedDocumentId,
      };
    case 'SET_FILTERS':
      return { ...state, filters: { ...state.filters, ...action.payload } };
    case 'CLEAR_FILTERS':
      return { ...state, filters: defaultFilters };
    case 'SELECT_DOCUMENT':
      return { ...state, selectedDocumentId: action.payload };
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    case 'BULK_UPDATE_STATUS':
      return {
        ...state,
        documents: state.documents.map((doc) =>
          action.payload.ids.includes(doc.id)
            ? { ...doc, status: action.payload.status, updatedAt: new Date().toISOString() }
            : doc
        ),
      };
    case 'BULK_ASSIGN':
      return {
        ...state,
        documents: state.documents.map((doc) =>
          action.payload.ids.includes(doc.id)
            ? { ...doc, assignee: action.payload.assignee, updatedAt: new Date().toISOString() }
            : doc
        ),
      };
    default:
      return state;
  }
}

interface DocumentContextType {
  state: DocumentState;
  filteredDocuments: Document[];
  selectedDocument: Document | null;
  dispatch: React.Dispatch<DocumentAction>;
  addDocument: (document: Omit<Document, 'id' | 'createdAt' | 'updatedAt'>) => string;
  updateDocument: (id: string, updates: Partial<Document>) => void;
  deleteDocument: (id: string) => void;
  setFilters: (filters: Partial<DocumentFilters>) => void;
  clearFilters: () => void;
  selectDocument: (id: string | null) => void;
  bulkUpdateStatus: (ids: string[], status: DocumentStatus) => void;
  bulkAssign: (ids: string[], assignee: string) => void;
  getDailySummary: (date?: string) => DailySummary;
}

const DocumentContext = createContext<DocumentContextType | undefined>(undefined);

export function DocumentProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(documentReducer, {
    documents: loadDocuments(),
    filters: defaultFilters,
    selectedDocumentId: null,
    isLoading: false,
    error: null,
  });

  const hydrated = useRef(false);

  // Persist to localStorage + background KV sync on every change
  useEffect(() => {
    saveDocuments(state.documents);
    if (hydrated.current) syncToKV(state.documents);
  }, [state.documents]);

  // Hydrate from KV on first load
  useEffect(() => {
    initSyncSession()
      .then(() => pullFromKV())
      .then((docs) => {
        if (docs && state.documents.length === 0) {
          dispatch({ type: 'SET_DOCUMENTS', payload: docs as Document[] });
        }
        hydrated.current = true;
      })
      .catch((error) => {
        console.error('Failed to hydrate from KV:', error);
        hydrated.current = true; // Mark as hydrated even on error to prevent retries
      });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const filteredDocuments = useMemo(() => {
    return state.documents.filter((doc) => {
      const { status, type, priority, assignee, searchQuery } = state.filters;
      if (status && status !== 'all' && doc.status !== status) return false;
      if (type && type !== 'all' && doc.type !== type) return false;
      if (priority && priority !== 'all' && doc.priority !== priority) return false;
      if (assignee && assignee !== 'all' && doc.assignee !== assignee) return false;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const text = [doc.originalName, doc.extractedData?.customerName, doc.extractedData?.invoiceNumber, doc.notes, doc.assignee]
          .filter(Boolean).join(' ').toLowerCase();
        if (!text.includes(q)) return false;
      }
      return true;
    });
  }, [state.documents, state.filters]);

  const selectedDocument = useMemo(() => {
    return state.documents.find((doc) => doc.id === state.selectedDocumentId) || null;
  }, [state.documents, state.selectedDocumentId]);

  const addDocument = useCallback((document: Omit<Document, 'id' | 'createdAt' | 'updatedAt'>): string => {
    const id = generateId();
    const newDocument: Document = {
      ...document,
      id,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    dispatch({ type: 'ADD_DOCUMENT', payload: newDocument });
    return id;
  }, []);

  const updateDocument = useCallback((id: string, updates: Partial<Document>) => {
    dispatch({ type: 'UPDATE_DOCUMENT', payload: { id, updates } });
  }, []);

  const deleteDocument = useCallback((id: string) => {
    dispatch({ type: 'DELETE_DOCUMENT', payload: id });
  }, []);

  const setFilters = useCallback((filters: Partial<DocumentFilters>) => {
    dispatch({ type: 'SET_FILTERS', payload: filters });
  }, []);

  const clearFilters = useCallback(() => {
    dispatch({ type: 'CLEAR_FILTERS' });
  }, []);

  const selectDocument = useCallback((id: string | null) => {
    dispatch({ type: 'SELECT_DOCUMENT', payload: id });
  }, []);

  const bulkUpdateStatus = useCallback((ids: string[], status: DocumentStatus) => {
    dispatch({ type: 'BULK_UPDATE_STATUS', payload: { ids, status } });
  }, []);

  const bulkAssign = useCallback((ids: string[], assignee: string) => {
    dispatch({ type: 'BULK_ASSIGN', payload: { ids, assignee } });
  }, []);

  const getDailySummary = useCallback((date?: string): DailySummary => {
    const targetDate = date || new Date().toISOString().split('T')[0];
    const dayStart = new Date(targetDate);
    const dayEnd = new Date(dayStart);
    dayEnd.setDate(dayEnd.getDate() + 1);
    const dayDocs = state.documents.filter((doc) => {
      const d = new Date(doc.createdAt);
      return d >= dayStart && d < dayEnd;
    });
    const byType = dayDocs.reduce((a, d) => { a[d.type] = (a[d.type] || 0) + 1; return a; }, {} as Record<string, number>);
    const byAssignee = dayDocs.reduce((a, d) => { if (d.assignee) a[d.assignee] = (a[d.assignee] || 0) + 1; return a; }, {} as Record<string, number>);
    return {
      date: targetDate,
      totalDocuments: dayDocs.length,
      processedCount: dayDocs.filter((d) => d.status === 'completed').length,
      escalatedCount: dayDocs.filter((d) => d.status === 'escalated').length,
      pendingCount: dayDocs.filter((d) => d.status === 'pending' || d.status === 'processing').length,
      criticalCount: dayDocs.filter((d) => d.priority === 'critical').length,
      byType,
      byAssignee,
    };
  }, [state.documents]);

  return (
    <DocumentContext.Provider value={{
      state, filteredDocuments, selectedDocument, dispatch,
      addDocument, updateDocument, deleteDocument, setFilters, clearFilters,
      selectDocument, bulkUpdateStatus, bulkAssign, getDailySummary,
    }}>
      {children}
    </DocumentContext.Provider>
  );
}

export function useDocuments() {
  const context = useContext(DocumentContext);
  if (!context) throw new Error('useDocuments must be used within DocumentProvider');
  return context;
}
