import axios from 'axios'

export const api = axios.create({ baseURL: '/api' })

// Add request interceptor for auth tokens
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Add response interceptor for consistent error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      const status = error.response.status
      if (status === 401) {
        localStorage.removeItem('token')
        window.location.href = '/login'
      } else if (status === 403) {
        console.error('Access forbidden:', error.response.data)
      } else if (status >= 500) {
        console.error('Server error:', error.response.data)
      }
    } else if (error.request) {
      // Request made but no response received
      console.error('Network error - no response received')
    } else {
      // Something else happened
      console.error('Request error:', error.message)
    }
    return Promise.reject(error)
  }
)

// ── Incidents ──────────────────────────────────────────────────────────────
export const incidentsApi = {
  list: (status?: string) => api.get('/incidents', { params: status ? { status } : {} }),
  get: (id: string) => api.get(`/incidents/${id}`),
  create: (body: { title: string; severity: string; blast_radius?: string }) =>
    api.post('/incidents', body),
  advancePhase: (id: string, phase: string, note?: string) =>
    api.post(`/incidents/${id}/phase`, { phase, note: note ?? '' }),
  resolve: (id: string, root_cause: string) =>
    api.post(`/incidents/${id}/resolve`, { root_cause }),
  stats: () => api.get('/incidents/summary/stats'),
}

// ── Debt ──────────────────────────────────────────────────────────────────
export const debtApi = {
  list: (status?: string) => api.get('/debt', { params: status ? { status } : {} }),
  get: (id: string) => api.get(`/debt/${id}`),
  create: (body: { name: string; description?: string; interest_per_year: number; principal_cost: number }) =>
    api.post('/debt', body),
  updateStatus: (id: string, status: string) => api.patch(`/debt/${id}`, { status }),
  stats: () => api.get('/debt/summary/stats'),
}

// ── Costs ──────────────────────────────────────────────────────────────────
export const costsApi = {
  list: () => api.get('/costs'),
  create: (body: { service_name: string; monthly_cost: number; savings_opportunity?: number; category?: string; notes?: string }) =>
    api.post('/costs', body),
  stats: () => api.get('/costs/summary/stats'),
}

// ── Pipelines ──────────────────────────────────────────────────────────────
export const pipelinesApi = {
  list: () => api.get('/pipelines'),
  get: (id: string) => api.get(`/pipelines/${id}`),
  create: (body: { name: string; status?: string; quality_score?: number; cost_per_record?: number; records_per_day?: number; sla_minutes?: number; phase?: string }) =>
    api.post('/pipelines', body),
  update: (id: string, body: unknown) => api.put(`/pipelines/${id}`, body),
  stats: () => api.get('/pipelines/summary/stats'),
}

// ── Performance ────────────────────────────────────────────────────────────
export const performanceApi = {
  list: (status?: string) => api.get('/performance', { params: status ? { status } : {} }),
  create: (body: { service: string; metric: string; current_value: number; baseline_value: number; unit?: string; bottleneck?: string }) =>
    api.post('/performance', body),
  resolve: (id: string, root_cause: string) =>
    api.post(`/performance/${id}/resolve`, { root_cause }),
  stats: () => api.get('/performance/summary/stats'),
}

// ── Migrations ─────────────────────────────────────────────────────────────
export const migrationsApi = {
  list: () => api.get('/migrations'),
  get: (id: string) => api.get(`/migrations/${id}`),
  create: (body: { name: string; risk_level?: string }) => api.post('/migrations', body),
  advancePhase: (id: string, body: { phase: string; rollback_ready?: boolean; kill_switch?: boolean; validation_pct?: number }) =>
    api.post(`/migrations/${id}/phase`, body),
  stats: () => api.get('/migrations/summary/stats'),
}

// ── API Governance ─────────────────────────────────────────────────────────
export const apiGovernanceApi = {
  list: (service?: string) => api.get('/api-governance', { params: service ? { service } : {} }),
  create: (body: { endpoint: string; version?: string; method?: string; service: string; notes?: string }) =>
    api.post('/api-governance', body),
  check: (id: string, body: { breaking_changes?: number; doc_complete?: boolean; consistency_score?: number }) =>
    api.post(`/api-governance/${id}/check`, body),
  stats: () => api.get('/api-governance/summary/stats'),
}

// ── Global ─────────────────────────────────────────────────────────────────
export const globalApi = {
  summary: () => api.get('/summary'),
  health: () => api.get('/health'),
}
