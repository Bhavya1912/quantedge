import React, { useEffect, useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import useStore from '../../store'

const NAV = [
  { path: '/roadmap',     icon: '🗺️',  label: 'Roadmap',       phase: null },
  { path: '/optimizer',   icon: '⚡',   label: 'Optimizer',     phase: '1' },
  { path: '/chain',       icon: '🌐',  label: 'Option Chain',  phase: '1' },
  { path: '/monte-carlo', icon: '🎲',  label: 'Monte Carlo',   phase: '1' },
  { path: '/iv-analysis', icon: '📊',  label: 'IV Analysis',   phase: '2', pro: true },
  { path: '/stress-test', icon: '⚠️',  label: 'Stress Test',   phase: '2', pro: true },
  { path: '/compare',     icon: '📋',  label: 'Compare',       phase: '2', pro: true },
  { path: '/alerts',      icon: '🔔',  label: 'Alerts',        phase: '1' },
]

const TICKERS = [
  { name: 'NIFTY',     base: 24387, vol: 20 },
  { name: 'BANKNIFTY', base: 51204, vol: 30 },
  { name: 'INDIA VIX', base: 14.32, vol: 0.05, isVix: true },
  { name: 'SENSEX',    base: 80218, vol: 50 },
  { name: 'USD/INR',   base: 83.42, vol: 0.05 },
]

export default function Layout() {
  const { sidebarCollapsed, toggleSidebar, runOptimize, optimizing } = useStore()
  const navigate = useNavigate()
  const [prices, setPrices] = useState(TICKERS.map((t) => t.base))

  // Animate tickers
  useEffect(() => {
    const interval = setInterval(() => {
      setPrices((prev) =>
        prev.map((p, i) => {
          const t = TICKERS[i]
          const delta = (Math.random() - 0.5) * t.vol
          return parseFloat((p + delta).toFixed(t.isVix ? 2 : t.name === 'USD/INR' ? 2 : 0))
        })
      )
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  const pctChange = (current, base) => {
    const pct = ((current - base) / base) * 100
    return `${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%`
  }
  const isUp = (current, base) => current >= base

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', background: '#080a0f', color: '#e2e8f8', fontFamily: 'Syne, sans-serif' }}>

      {/* ── SIDEBAR ── */}
      <aside style={{
        width: sidebarCollapsed ? 60 : 228,
        background: '#0d1018',
        borderRight: '1px solid #1e2840',
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0,
        transition: 'width 0.25s',
        overflow: 'hidden',
      }}>
        {/* Logo */}
        <div style={{ padding: '16px 16px 12px', borderBottom: '1px solid #1e2840', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          {!sidebarCollapsed && (
            <div>
              <div style={{ fontSize: 17, fontWeight: 800 }}>Quant<span style={{ color: '#00d4ff' }}>Edge</span></div>
              <div style={{ fontSize: 8, color: '#718096', fontFamily: 'Space Mono', letterSpacing: '1.5px', textTransform: 'uppercase', marginTop: 2 }}>Options Optimizer</div>
            </div>
          )}
          <button onClick={toggleSidebar} style={{ background: 'none', border: '1px solid #1e2840', borderRadius: 5, color: '#718096', fontSize: 11, padding: '3px 7px', cursor: 'pointer' }}>
            {sidebarCollapsed ? '▶' : '◀'}
          </button>
        </div>

        {/* Live indicator */}
        {!sidebarCollapsed && (
          <div style={{ margin: '10px 12px', background: 'rgba(0,230,118,0.07)', border: '1px solid rgba(0,230,118,0.18)', borderRadius: 6, padding: '5px 10px', display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, color: '#00e676', fontFamily: 'Space Mono' }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#00e676', animation: 'blink 2s infinite', flexShrink: 0 }} />
            NSE/BSE LIVE
          </div>
        )}

        {/* Nav */}
        <nav style={{ padding: '8px 8px', flex: 1, overflowY: 'auto' }}>
          {NAV.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: sidebarCollapsed ? '9px 0' : '8px 10px',
                justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
                borderRadius: 7,
                marginBottom: 2,
                fontSize: 12,
                fontWeight: 600,
                color: isActive ? '#00d4ff' : '#718096',
                background: isActive ? 'rgba(0,212,255,0.08)' : 'transparent',
                border: isActive ? '1px solid rgba(0,212,255,0.12)' : '1px solid transparent',
                textDecoration: 'none',
                transition: 'all 0.15s',
                whiteSpace: 'nowrap',
              })}
            >
              <span style={{ fontSize: 14, flexShrink: 0 }}>{item.icon}</span>
              {!sidebarCollapsed && (
                <>
                  <span>{item.label}</span>
                  {item.pro && (
                    <span style={{ marginLeft: 'auto', background: '#7c3aed', color: '#fff', fontSize: 8, padding: '2px 5px', borderRadius: 8, fontFamily: 'Space Mono' }}>PRO</span>
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Upgrade */}
        {!sidebarCollapsed && (
          <div style={{ padding: '10px', borderTop: '1px solid #1e2840' }}>
            <div style={{ background: 'linear-gradient(135deg,rgba(124,58,237,0.15),rgba(0,212,255,0.08))', border: '1px solid rgba(124,58,237,0.25)', borderRadius: 10, padding: '12px', textAlign: 'center' }}>
              <div style={{ fontSize: 18, marginBottom: 4 }}>🚀</div>
              <div style={{ fontSize: 11, fontWeight: 700, marginBottom: 2 }}>Upgrade to Pro</div>
              <div style={{ fontSize: 9, color: '#718096', marginBottom: 8 }}>IV Surface, Auto-Hedge & Backtest</div>
              <button style={{ background: 'linear-gradient(135deg,#7c3aed,#00d4ff)', border: 'none', borderRadius: 6, color: '#fff', fontSize: 10, fontWeight: 700, padding: '7px 14px', cursor: 'pointer', width: '100%', fontFamily: 'Syne' }}>
                ₹1,500 / month
              </button>
            </div>
          </div>
        )}
      </aside>

      {/* ── MAIN ── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

        {/* Topbar */}
        <div style={{ height: 52, borderBottom: '1px solid #1e2840', background: '#0d1018', display: 'flex', alignItems: 'center', padding: '0 18px', gap: 16, flexShrink: 0 }}>
          <div style={{ display: 'flex', gap: 18, flex: 1, overflow: 'hidden' }}>
            {TICKERS.map((t, i) => (
              <div key={t.name} style={{ display: 'flex', alignItems: 'center', gap: 5, fontFamily: 'Space Mono', fontSize: 10, whiteSpace: 'nowrap' }}>
                <span style={{ color: '#718096', fontWeight: 700 }}>{t.name}</span>
                <span>{prices[i].toLocaleString()}</span>
                <span style={{ color: isUp(prices[i], t.base) ? '#00e676' : '#ff3d3d' }}>
                  {pctChange(prices[i], t.base)}
                </span>
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={() => navigate('/chain')} style={{ background: '#111520', border: '1px solid #1e2840', borderRadius: 7, color: '#e2e8f8', fontSize: 11, padding: '6px 12px', cursor: 'pointer', fontFamily: 'Syne', fontWeight: 600 }}>
              📋 Option Chain
            </button>
            <button
              onClick={() => { navigate('/optimizer'); runOptimize() }}
              disabled={optimizing}
              style={{ background: optimizing ? '#0d3a5a' : 'linear-gradient(135deg,#0099cc,#0066aa)', border: 'none', borderRadius: 7, color: '#fff', fontSize: 11, padding: '6px 14px', cursor: optimizing ? 'not-allowed' : 'pointer', fontFamily: 'Syne', fontWeight: 700 }}
            >
              {optimizing ? '⏳ Optimizing...' : '▶ Run Optimizer'}
            </button>
          </div>
        </div>

        {/* Page content */}
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <Outlet />
        </div>
      </div>

      <style>{`
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.2} }
        ::-webkit-scrollbar{width:4px;height:4px}
        ::-webkit-scrollbar-track{background:transparent}
        ::-webkit-scrollbar-thumb{background:#1e2840;border-radius:2px}
        * { box-sizing: border-box; margin: 0; padding: 0; }
      `}</style>
    </div>
  )
}
