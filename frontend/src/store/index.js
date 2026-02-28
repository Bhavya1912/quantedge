/**
 * Global State — Zustand Store
 * Central state for optimizer inputs, results, and UI state.
 */
import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import {
  runOptimizer,
  fetchChain,
  runMonteCarlo,
  fetchIVAnalysis,
  runStressTest,
} from '../utils/api'

const useStore = create(
  devtools((set, get) => ({
    // ── UI State ──────────────────────────────────────────────────────────
    activeTab: 'optimizer',
    sidebarCollapsed: false,
    setActiveTab: (tab) => set({ activeTab: tab }),
    toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),

    // ── Optimizer Inputs ─────────────────────────────────────────────────
    inputs: {
      symbol: 'BANKNIFTY',
      capital: 250000,
      market_view: 'bullish',
      volatility_outlook: 'falling',
      risk_appetite: 'moderate',
      time_horizon: 'weekly',
      top_n: 3,
    },
    setInput: (key, value) =>
      set((s) => ({ inputs: { ...s.inputs, [key]: value } })),

    // ── Optimizer Results ─────────────────────────────────────────────────
    optimizerResult: null,
    selectedStrategy: 0,
    optimizing: false,
    optimizerError: null,

    runOptimize: async () => {
      set({ optimizing: true, optimizerError: null })
      try {
        const result = await runOptimizer(get().inputs)
        set({ optimizerResult: result, selectedStrategy: 0, optimizing: false })
      } catch (err) {
        set({
          optimizerError: err.response?.data?.detail || 'Optimization failed.',
          optimizing: false,
        })
      }
    },
    selectStrategy: (idx) => set({ selectedStrategy: idx }),

    // ── Option Chain ──────────────────────────────────────────────────────
    chainData: null,
    chainLoading: false,
    fetchChain: async (symbol = 'BANKNIFTY') => {
      set({ chainLoading: true })
      try {
        const data = await fetchChain(symbol)
        set({ chainData: data, chainLoading: false })
      } catch (e) {
        set({ chainLoading: false })
      }
    },

    // ── Monte Carlo ───────────────────────────────────────────────────────
    mcResult: null,
    mcLoading: false,
    runMC: async (params) => {
      set({ mcLoading: true })
      try {
        const result = await runMonteCarlo(params)
        set({ mcResult: result, mcLoading: false })
      } catch (e) {
        set({ mcLoading: false })
      }
    },

    // ── IV Analysis ───────────────────────────────────────────────────────
    ivData: null,
    ivLoading: false,
    fetchIV: async (symbol = 'BANKNIFTY') => {
      set({ ivLoading: true })
      try {
        const data = await fetchIVAnalysis(symbol)
        set({ ivData: data, ivLoading: false })
      } catch (e) {
        set({ ivLoading: false })
      }
    },

    // ── Stress Test ───────────────────────────────────────────────────────
    stressResult: null,
    stressInputs: { spot_move_pct: 3.0, iv_move_pct: 0.0, days_forward: 1 },
    setStressInput: (key, val) =>
      set((s) => ({ stressInputs: { ...s.stressInputs, [key]: val } })),
    runStress: async () => {
      const { optimizerResult, selectedStrategy, stressInputs } = get()
      const strat = optimizerResult?.strategies?.[selectedStrategy]
      if (!strat) return
      try {
        const result = await runStressTest({
          legs: strat.legs,
          spot: optimizerResult.spot,
          iv: optimizerResult.iv,
          expiry_days: 1,
          ...stressInputs,
        })
        set({ stressResult: result })
      } catch (e) {
        console.error('Stress test failed:', e)
      }
    },
  }))
)

export default useStore
