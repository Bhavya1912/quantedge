import React, { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from './components/layout/Layout'
import OptimizerPage from './pages/OptimizerPage'
import ChainPage from './pages/ChainPage'
import MonteCarloPage from './pages/MonteCarloPage'
import IVAnalysisPage from './pages/IVAnalysisPage'
import StressTestPage from './pages/StressTestPage'
import ComparePage from './pages/ComparePage'
import RoadmapPage from './pages/RoadmapPage'
import AlertsPage from './pages/AlertsPage'
import useStore from './store'

export default function App() {
  const { fetchChain } = useStore()

  // Load initial data
  useEffect(() => {
    fetchChain('BANKNIFTY')
  }, [])

  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#111520',
            color: '#e2e8f8',
            border: '1px solid #1e2840',
            fontFamily: 'Syne, sans-serif',
          },
        }}
      />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/optimizer" replace />} />
          <Route path="roadmap" element={<RoadmapPage />} />
          <Route path="optimizer" element={<OptimizerPage />} />
          <Route path="chain" element={<ChainPage />} />
          <Route path="monte-carlo" element={<MonteCarloPage />} />
          <Route path="iv-analysis" element={<IVAnalysisPage />} />
          <Route path="stress-test" element={<StressTestPage />} />
          <Route path="compare" element={<ComparePage />} />
          <Route path="alerts" element={<AlertsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
