/**
 * QuantEdge API Client
 * Connects React frontend to FastAPI backend.
 * All calls go through this module — easy to mock in tests.
 */
import axios from 'axios'

const configuredBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').trim()
const BASE_URL = configuredBaseUrl || (import.meta.env.PROD ? 'https://quantedge-backend.onrender.com/api/v1' : '/api/v1')

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('qe_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Handle 401 → redirect to login
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('qe_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ── Optimizer ────────────────────────────────────────────────────────────────
export const runOptimizer = (params) =>
  api.post('/optimize', params).then((r) => r.data)

// ── Option Chain ─────────────────────────────────────────────────────────────
export const fetchChain = (symbol = 'BANKNIFTY', expiry = null) =>
  api.get(`/chain/${symbol}`, { params: expiry ? { expiry } : {} }).then((r) => r.data)

// ── Greeks ───────────────────────────────────────────────────────────────────
export const computeGreeks = (params) =>
  api.post('/greeks', params).then((r) => r.data)

// ── Monte Carlo ──────────────────────────────────────────────────────────────
export const runMonteCarlo = (params) =>
  api.post('/simulate', params).then((r) => r.data)

// ── IV Analysis ──────────────────────────────────────────────────────────────
export const fetchIVAnalysis = (symbol = 'BANKNIFTY') =>
  api.get(`/iv/${symbol}`).then((r) => r.data)

// ── Stress Test ──────────────────────────────────────────────────────────────
export const runStressTest = (params) =>
  api.post('/stress', params).then((r) => r.data)

// ── Auth ─────────────────────────────────────────────────────────────────────
export const login = (email, password) =>
  api.post('/auth/login', { email, password }).then((r) => {
    localStorage.setItem('qe_token', r.data.access_token)
    return r.data
  })

export const register = (email, password) =>
  api.post('/auth/register', { email, password }).then((r) => r.data)

// ── Health ───────────────────────────────────────────────────────────────────
export const healthCheck = () =>
  api.get('/health').then((r) => r.data)

export default api
