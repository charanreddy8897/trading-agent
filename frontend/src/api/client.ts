import axios from 'axios'
import type {
  PortfolioSummary, Position, SectorAllocation,
  ScreenerRow, Analysis, PegSetup,
  MoversResponse, Mover, NewsItem, Alert,
} from '@/types'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 15_000,
  headers: { 'Content-Type': 'application/json' },
})

// Add auth token to all requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res.data,
  (err) => {
    // If 401 Unauthorized, redirect to login
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    }
    const msg = err.response?.data?.detail ?? err.message ?? 'API error'
    return Promise.reject(new Error(String(msg)))
  },
)

export const portfolioApi = {
  summary:     (): Promise<PortfolioSummary>   => api.get('/portfolio/summary'),
  holdings:    (): Promise<Position[]>          => api.get('/portfolio/holdings'),
  sectorAlloc: (): Promise<SectorAllocation>   => api.get('/portfolio/sector-allocation'),
  performance: (period = '1M'): Promise<{ date: string; value: number }[]> =>
    api.get(`/portfolio/performance?period=${period}`),
}

export const screenerApi = {
  ranked: (sector = 'all', minScore = 0): Promise<ScreenerRow[]> =>
    api.get(`/screener/ranked?sector=${sector}&min_score=${minScore}`),
}

export const analysisApi = {
  get:     (ticker: string): Promise<Analysis> => api.get(`/analysis/${ticker}`),
  refresh: (ticker: string): Promise<Analysis> => api.post(`/analysis/${ticker}/refresh`),
}

export const pegApi = {
  active:  (): Promise<PegSetup[]> => api.get('/peg/active'),
  history: (): Promise<PegSetup[]> => api.get('/peg/history'),
}

export const moversApi = {
  top:     (count = 10): Promise<MoversResponse>  => api.get(`/movers/top?count=${count}`),
  unusual: (threshold = 2.0): Promise<Mover[]>    => api.get(`/movers/unusual-volume?threshold=${threshold}`),
}

export const newsApi = {
  feed: (sector = 'all', limit = 50): Promise<NewsItem[]> =>
    api.get(`/news/feed?sector=${sector}&limit=${limit}`),
}

export const alertsApi = {
  active:  (): Promise<Alert[]>       => api.get('/alerts/active'),
  dismiss: (id: number): Promise<{ dismissed: boolean }> => api.post(`/alerts/${id}/dismiss`),
}

export const systemApi = {
  health:      (): Promise<{ status: string }> => api.get('/health'),
  runPipeline: (): Promise<void>               => api.post('/system/run-pipeline'),
}

export default api
