// pages/MonteCarloPage.jsx
import React, { useEffect, useRef } from 'react'
import useStore from '../store'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const S = {
  card: { background: '#111520', border: '1px solid #1e2840', borderRadius: 11, padding: 16 },
  label: { fontSize: 8, textTransform: 'uppercase', letterSpacing: '1.5px', color: '#718096', fontFamily: 'Space Mono', marginBottom: 7 },
  green: '#00e676', red: '#ff3d3d', cyan: '#00d4ff', yellow: '#ffc400',
}

export function MonteCarloPage() {
  const { mcResult, mcLoading, runMC, optimizerResult, selectedStrategy } = useStore()

  const handleRun = () => {
    const strat = optimizerResult?.strategies?.[selectedStrategy]
    if (!strat) return
    runMC({
      legs: strat.legs,
      spot: optimizerResult.spot,
      iv: optimizerResult.iv,
      expiry_days: 1,
      n_simulations: 10000,
    })
  }

  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: '16px 18px', display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <div style={{ fontSize: 20, fontWeight: 800 }}>Monte Carlo Simulation</div>
          <div style={{ fontSize: 10, color: '#718096', marginTop: 3, fontFamily: 'Space Mono' }}>
            GBM MODEL · dS = μSdt + σSdW · BOX-MULLER GAUSSIAN SAMPLING · NOT CLT APPROXIMATION
          </div>
        </div>
        <button onClick={handleRun} disabled={mcLoading || !optimizerResult}
          style={{ background: 'linear-gradient(135deg,#7c3aed,#00d4ff)', border: 'none', borderRadius: 9, color: '#fff', fontSize: 12, fontWeight: 800, padding: '10px 20px', cursor: 'pointer', fontFamily: 'Syne' }}>
          {mcLoading ? '⏳ Simulating...' : '🎲 Run 10K Simulations'}
        </button>
      </div>

      {!optimizerResult && (
        <div style={{ ...S.card, textAlign: 'center', padding: 40, color: '#4a5568' }}>
          <div style={{ fontSize: 36, marginBottom: 8 }}>🎲</div>
          <div>Run the optimizer first to select a strategy for simulation.</div>
        </div>
      )}

      {mcResult && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6,1fr)', gap: 10 }}>
            {[
              { l: 'Expected Value', v: `+₹${mcResult.ev.toLocaleString()}`, c: S.green },
              { l: 'Win Rate', v: `${(mcResult.win_rate * 100).toFixed(1)}%`, c: S.green },
              { l: 'Std Deviation', v: `₹${mcResult.std_dev.toLocaleString()}`, c: S.cyan },
              { l: 'Sharpe Ratio', v: mcResult.sharpe.toFixed(3), c: S.yellow },
              { l: 'VaR (95%)', v: `₹${mcResult.var_95.toLocaleString()}`, c: S.red },
              { l: 'CVaR (95%)', v: `₹${mcResult.cvar_95.toLocaleString()}`, c: S.red },
            ].map(({ l, v, c }) => (
              <div key={l} style={{ ...S.card, textAlign: 'center' }}>
                <div style={S.label}>{l}</div>
                <div style={{ fontSize: 16, fontWeight: 800, fontFamily: 'Space Mono', color: c }}>{v}</div>
              </div>
            ))}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 12 }}>
            <div style={S.card}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                <div style={S.label}>P&L Distribution – {mcResult.n_simulations.toLocaleString()} Simulations</div>
                <span style={{ fontSize: 8, padding: '3px 7px', borderRadius: 8, fontFamily: 'Space Mono', fontWeight: 700, background: 'rgba(124,58,237,0.08)', border: '1px solid rgba(124,58,237,0.2)', color: '#7c3aed' }}>GBM + BOX-MULLER</span>
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={mcResult.histogram} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
                  <XAxis dataKey="bin_low" tickFormatter={(v) => `₹${Math.round(v / 1000)}K`}
                    tick={{ fontSize: 7, fill: '#4a5568', fontFamily: 'Space Mono' }} />
                  <YAxis tick={{ fontSize: 7, fill: '#4a5568', fontFamily: 'Space Mono' }} />
                  <Tooltip
                    contentStyle={{ background: '#111520', border: '1px solid #1e2840', fontSize: 9, fontFamily: 'Space Mono' }}
                    formatter={(v, n, props) => [`${(props.payload.frequency * 100).toFixed(1)}% (${props.payload.count} sims)`, 'Frequency']}
                    labelFormatter={(v) => `₹${Math.round(v).toLocaleString()}`}
                  />
                  <Bar dataKey="count" radius={[2, 2, 0, 0]}>
                    {mcResult.histogram.map((entry, i) => (
                      <Cell key={i} fill={entry.is_profit ? '#00e676' : '#ff3d3d'} opacity={0.75} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div style={S.card}>
              <div style={S.label}>Simulation Parameters</div>
              {[
                ['GBM Model', 'dS = μSdt + σSdW'],
                ['Gaussian Sampling', 'Box-Muller Transform'],
                ['Variance Reduction', 'Antithetic Variates'],
                ['Simulations', mcResult.n_simulations.toLocaleString()],
                ['Sortino Ratio', mcResult.sortino.toFixed(3)],
                ['Terminal P5', `₹${mcResult.terminal_prices.p5.toLocaleString()}`],
                ['Terminal P95', `₹${mcResult.terminal_prices.p95.toLocaleString()}`],
              ].map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, padding: '6px 0', borderBottom: '1px solid rgba(30,40,64,0.4)' }}>
                  <span style={{ color: '#718096' }}>{k}</span>
                  <span style={{ fontFamily: 'Space Mono', fontWeight: 700, color: '#00d4ff' }}>{v}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}


// pages/RoadmapPage.jsx
export function RoadmapPage() {
  const navigate = useNavigateHook()
  const phases = [
    {
      ph: 'Phase 0', title: 'Foundation', period: 'Week 0 · Infrastructure',
      status: 'COMPLETE', statusColor: '#00e676',
      topColor: 'linear-gradient(90deg,#00e676,#00d4ff)',
      metrics: [{ l: 'Complete', v: '100%', c: '#00e676' }, { l: 'Modules', v: '5', c: '#e2e8f8' }],
      features: [
        { done: true, text: 'Project architecture design' },
        { done: true, text: 'UI/UX design system' },
        { done: true, text: 'Black-Scholes engine (exact)' },
        { done: true, text: 'NSE data pipeline' },
        { done: true, text: 'Docker + CI/CD setup' },
      ],
    },
    {
      ph: 'Phase 1', title: 'MVP', period: 'Weeks 1–4 · Core Product',
      status: 'BUILDING', statusColor: '#00d4ff',
      topColor: 'linear-gradient(90deg,#00d4ff,#7c3aed)',
      metrics: [{ l: 'Complete', v: '62%', c: '#00d4ff' }, { l: 'MRR Target', v: '₹4.5L', c: '#e2e8f8' }],
      features: [
        { done: true, text: 'Live option chain (NSE API)' },
        { done: true, text: 'True EV via lognormal integration' },
        { done: true, text: 'Black-Scholes Greeks (all orders)' },
        { done: true, text: 'Monte Carlo (Box-Muller GBM)' },
        { done: true, text: 'Risk-constrained optimizer' },
        { done: false, text: 'Razorpay subscription billing' },
        { done: false, text: 'Telegram alerts bot' },
      ],
    },
    {
      ph: 'Phase 2', title: 'Premium', period: 'Months 2–3 · Power Features',
      status: 'PLANNED', statusColor: '#7c3aed',
      topColor: 'linear-gradient(90deg,#7c3aed,#ff6d00)',
      metrics: [{ l: 'Complete', v: '0%', c: '#7c3aed' }, { l: 'Subs Target', v: '300', c: '#e2e8f8' }],
      features: [
        { done: false, text: 'IV Surface (Rank + Percentile)' },
        { done: false, text: 'Term structure analysis' },
        { done: false, text: 'Scenario stress testing' },
        { done: false, text: 'Auto-adjustment engine' },
        { done: false, text: 'Delta drift real-time alerts' },
      ],
    },
    {
      ph: 'Phase 3', title: 'Expansion', period: 'Month 4+ · Advanced Tools',
      status: 'PLANNED', statusColor: '#ffc400',
      topColor: 'linear-gradient(90deg,#ff6d00,#ffc400)',
      metrics: [{ l: 'Complete', v: '0%', c: '#ffc400' }, { l: 'Retention', v: '70%', c: '#e2e8f8' }],
      features: [
        { done: false, text: 'F&O auto-hedging bot' },
        { done: false, text: 'Backtesting engine (NSE 2019+)' },
        { done: false, text: 'AI regime detection' },
        { done: false, text: 'Portfolio optimizer' },
        { done: false, text: 'Mobile app (React Native)' },
      ],
    },
  ]

  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: '16px 18px', display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <div style={{ fontSize: 20, fontWeight: 800 }}>Product Roadmap</div>
          <div style={{ fontSize: 10, color: '#718096', marginTop: 3, fontFamily: 'Space Mono' }}>
            QUANTEDGE · INDIA'S FIRST PROBABILITY-WEIGHTED OPTIONS OPTIMIZER · VERSION 1.0
          </div>
        </div>
        <button onClick={() => navigate('/optimizer')}
          style={{ background: 'linear-gradient(135deg,#00b4d8,#0077b6)', border: 'none', borderRadius: 9, color: '#fff', fontSize: 12, fontWeight: 800, padding: '10px 20px', cursor: 'pointer', fontFamily: 'Syne' }}>
          ⚡ Launch Optimizer
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 14 }}>
        {phases.map((p) => (
          <div key={p.ph} style={{ background: '#111520', border: '1px solid #1e2840', borderRadius: 12, padding: 18, position: 'relative', overflow: 'hidden' }}>
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, background: p.topColor }} />
            <div style={{ fontSize: 9, fontFamily: 'Space Mono', textTransform: 'uppercase', letterSpacing: '1.5px', color: '#718096', marginBottom: 4 }}>{p.ph}</div>
            <div style={{ fontSize: 18, fontWeight: 800, marginBottom: 3 }}>{p.title}</div>
            <div style={{ fontSize: 9, color: '#718096', fontFamily: 'Space Mono', marginBottom: 10 }}>{p.period}</div>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 9, fontWeight: 700, padding: '3px 8px', borderRadius: 8, marginBottom: 12, fontFamily: 'Space Mono', background: `${p.statusColor}11`, border: `1px solid ${p.statusColor}33`, color: p.statusColor }}>
              {p.status}
            </div>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 5 }}>
              {p.features.map((f, i) => (
                <li key={i} style={{ fontSize: 11, color: f.done ? '#e2e8f8' : '#4a5568', display: 'flex', alignItems: 'center', gap: 7 }}>
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: f.done ? '#00e676' : '#1e2840', flexShrink: 0 }} />
                  {f.text}
                </li>
              ))}
            </ul>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 14 }}>
              {p.metrics.map(({ l, v, c }) => (
                <div key={l} style={{ background: '#151a26', borderRadius: 7, padding: 10, textAlign: 'center' }}>
                  <div style={{ fontSize: 16, fontWeight: 800, fontFamily: 'Space Mono', color: c }}>{v}</div>
                  <div style={{ fontSize: 8, color: '#718096', fontFamily: 'Space Mono', textTransform: 'uppercase', marginTop: 2 }}>{l}</div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,1fr)', gap: 12 }}>
        {[
          { l: 'Target Subs', v: '300', c: '#00d4ff', sub: '@ 6 months' },
          { l: 'Target ARPU', v: '₹1.5K', c: '#00e676', sub: 'per month' },
          { l: 'MRR Target', v: '₹4.5L', c: '#ffc400', sub: 'monthly recurring' },
          { l: 'Retention Goal', v: '70%', c: '#7c3aed', sub: 'at month 3' },
          { l: 'MVP Timeline', v: '30d', c: '#ff6d00', sub: 'to first paid user' },
        ].map(({ l, v, c, sub }) => (
          <div key={l} style={{ background: '#111520', border: '1px solid #1e2840', borderRadius: 11, padding: 16, textAlign: 'center' }}>
            <div style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '1.5px', color: '#718096', fontFamily: 'Space Mono', marginBottom: 6 }}>{l}</div>
            <div style={{ fontSize: 28, fontWeight: 800, fontFamily: 'Space Mono', color: c, margin: '6px 0' }}>{v}</div>
            <div style={{ fontSize: 9, color: '#718096', fontFamily: 'Space Mono' }}>{sub}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

// Hook shim for non-hook context
function useNavigateHook() {
  const { useNavigate } = require('react-router-dom')
  return useNavigate()
}
