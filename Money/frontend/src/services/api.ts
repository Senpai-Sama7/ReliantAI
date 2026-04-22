// API Service — HVAC Dispatch
import { ENV } from '../config/env';

// ── Types ─────────────────────────────────────────────────────

export interface Dispatch {
  dispatch_id: string;
  customer_name: string;
  customer_phone: string;
  address: string;
  issue_summary: string;
  urgency: string;
  tech_name: string;
  eta: string;
  status: string;
  crew_result?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface DispatchResponse {
  run_id: string;
  status: string;
  result?: Record<string, unknown>;
  timestamp: string;
}

export interface DashboardMetrics {
  total: number;
  emergency_count: number;
  completed_count: number;
  pending_count: number;
  today_count: number;
  today_emergency: number;
  emergency_pct: number;
}

export interface SearchResult {
  results: Dispatch[];
  count: number;
  offset: number;
}

export interface ApiError {
  detail: string;
}

export interface PricingPlan {
  name: string;
  price: number;
  dispatches_per_month: number;
  features: string[];
}

export interface Customer {
  id: number;
  email: string;
  name: string;
  company: string;
  phone: string;
  plan: string;
  status: string;
  billing_status: string;
  trial_ends_at: string | null;
  api_key_masked: string;
  dispatches_allowed: number;
  stripe_customer_id?: string;
  stripe_subscription_id?: string;
  monthly_revenue?: number;
  lead_source?: string;
  notes?: string;
  outreach_status: string;
  outreach_last_contact: string | null;
  outreach_next_contact: string | null;
  created_at: string;
  updated_at: string;
}

export interface RevenueSummary {
  period_days: number;
  active_customers: number;
  total_revenue: number;
  total_events: number;
  mrr_estimate: number;
}

export interface CheckoutRequest {
  email: string;
  name: string;
  company: string;
  phone: string;
  plan: string;
  success_url: string;
  cancel_url: string;
}

export interface CheckoutResponse {
  checkout_url: string;
  customer_id: number;
  api_key: string;
}

export type SSEEvent =
  | { type: 'metrics'; data: DashboardMetrics }
  | { type: 'dispatch_created'; data: { run_id: string; status: string; issue: string } }
  | { type: 'dispatch_completed'; data: { run_id: string; status: string; result: unknown } }
  | { type: 'dispatch_error'; data: { run_id: string; status: string; error: string } };

// ── Helpers ───────────────────────────────────────────────────

async function delay(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ── ApiService ────────────────────────────────────────────────

class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = ENV.API_BASE_URL;
  }

  private async fetch<T>(
    endpoint: string,
    options: RequestInit = {},
    retries = 2,
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const response = await fetch(url, { ...options, headers, credentials: 'include' });
        if (!response.ok) {
          const error: ApiError = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
          // Don't retry 4xx — those are client errors
          if (response.status >= 400 && response.status < 500) {
            throw new Error(error.detail || `HTTP ${response.status}`);
          }
          if (attempt < retries) {
            await delay(300 * (attempt + 1));
            continue;
          }
          throw new Error(error.detail || `HTTP ${response.status}`);
        }
        return response.json() as Promise<T>;
      } catch (err) {
        if (attempt >= retries) throw err;
        await delay(300 * (attempt + 1));
      }
    }
    throw new Error('Request failed after retries');
  }

  // ── Core dispatch API ──────────────────────────────────────

  async health(): Promise<{ status: string; database: string }> {
    return this.fetch('/health');
  }

  async getDispatches(limit = 50): Promise<Dispatch[]> {
    return this.fetch(`/dispatches?limit=${limit}`);
  }

  async getDispatchStatus(runId: string): Promise<DispatchResponse> {
    return this.fetch(`/run/${runId}`);
  }

  async createDispatch(message: string, temp = 95): Promise<{ run_id: string }> {
    return this.fetch('/dispatch', {
      method: 'POST',
      body: JSON.stringify({ customer_message: message, outdoor_temp_f: temp, async_mode: true }),
    });
  }

  // ── Enhanced metrics (server-side aggregation) ─────────────

  async getMetrics(): Promise<DashboardMetrics> {
    return this.fetch<DashboardMetrics>('/api/metrics');
  }

  // ── Search & filter ────────────────────────────────────────

  async searchDispatches(params: {
    q?: string;
    status?: string;
    urgency?: string;
    limit?: number;
    offset?: number;
  }): Promise<SearchResult> {
    const qs = new URLSearchParams();
    if (params.q) qs.set('q', params.q);
    if (params.status) qs.set('status', params.status);
    if (params.urgency) qs.set('urgency', params.urgency);
    if (params.limit) qs.set('limit', String(params.limit));
    if (params.offset) qs.set('offset', String(params.offset));
    return this.fetch(`/api/dispatches/search?${qs}`);
  }

  // ── Manual status override ─────────────────────────────────

  async updateDispatchStatus(
    dispatchId: string,
    update: { status?: string; tech_name?: string; eta?: string },
  ): Promise<Dispatch> {
    return this.fetch(`/api/dispatch/${dispatchId}/status`, {
      method: 'PATCH',
      body: JSON.stringify(update),
    });
  }

  // ── Dispatch timeline ──────────────────────────────────────

  async getDispatchTimeline(dispatchId: string): Promise<{
    dispatch_id: string;
    current_state: string;
    time_in_state_seconds: number;
    event_count: number;
    events: unknown[];
  }> {
    return this.fetch(`/api/dispatch/${dispatchId}/timeline`);
  }

  // ── Session auth ───────────────────────────────────────────

  async checkSession(): Promise<boolean> {
    try {
      await this.health();
      return true;
    } catch {
      return false;
    }
  }

  private async getLoginCsrfToken(): Promise<string> {
    const response = await fetch(`${this.baseUrl}/login`, {
      method: 'GET',
      credentials: 'include',
    });
    const html = await response.text();
    const match = html.match(/name="csrf_token" value="([^"]+)"/);
    if (!match?.[1]) throw new Error('Unable to load login form');
    return match[1];
  }

  async login(username: string, password: string): Promise<boolean> {
    const csrfToken = await this.getLoginCsrfToken();
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    formData.append('csrf_token', csrfToken);

    const response = await fetch(`${this.baseUrl}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
      credentials: 'include',
      redirect: 'manual',
    });

    return response.status === 0 ||
      Boolean(response.headers.get('location')?.includes('/admin')) ||
      response.ok;
  }

  async logout(): Promise<void> {
    await fetch(`${this.baseUrl}/logout`, { credentials: 'include' });
  }

  // ── Billing API ────────────────────────────────────────────

  async getPricing(): Promise<{ plans: Record<string, PricingPlan> }> {
    return this.fetch('/billing/pricing');
  }

  async getCustomer(apiKey: string): Promise<Customer> {
    return this.fetch('/billing/customer', { headers: { 'X-API-Key': apiKey } });
  }

  async listCustomers(status?: string, plan?: string): Promise<{ customers: Customer[]; count: number }> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (plan) params.append('plan', plan);
    return this.fetch(`/billing/customers?${params}`);
  }

  async createCheckout(data: CheckoutRequest): Promise<CheckoutResponse> {
    return this.fetch('/billing/checkout', { method: 'POST', body: JSON.stringify(data) });
  }

  async getRevenue(days = 30): Promise<RevenueSummary> {
    return this.fetch(`/billing/revenue?days=${days}`);
  }

  async createPortalSession(apiKey: string): Promise<{ portal_url: string }> {
    return this.fetch('/billing/portal', { method: 'POST', headers: { 'X-API-Key': apiKey } });
  }

  // ── Server-Sent Events stream ──────────────────────────────

  openStream(onEvent: (event: SSEEvent) => void, onError?: (err: Event) => void): () => void {
    const es = new EventSource(`${this.baseUrl}/api/stream/dispatches`, {
      withCredentials: true,
    });

    es.addEventListener('metrics', (e: MessageEvent) => {
      try { onEvent({ type: 'metrics', data: JSON.parse(e.data) }); } catch { /* skip */ }
    });

    es.onmessage = (e: MessageEvent) => {
      try { onEvent(JSON.parse(e.data) as SSEEvent); } catch { /* skip */ }
    };

    es.onerror = (e) => {
      onError?.(e);
    };

    return () => es.close();
  }
}

export const api = new ApiService();
export default api;
