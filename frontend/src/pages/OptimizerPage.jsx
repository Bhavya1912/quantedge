import React, { useEffect } from 'react'
import toast from 'react-hot-toast'
import useStore from '../store'
import {
  AreaChart, Area, LineChart, Line, XAxis, YAxis,
  Tooltip, ResponsiveContainer, ReferenceLine, CartesianGrid
} from 'recharts'

// ── Shared style tokens ──────────────────────────────────────────────────────
const S = {
  card: { background: '#111520', border: '1px solid #1e2840', borderRadius: 11, padding: 16 },
  label: { fontSize: 8, textTransform: 'uppercase', letterSpacing: '1.5px', color: '#718096', fontFamily: 'Space Mono', marginBottom: 7 },
  mono: { fontFamily: 'Space Mono' },
  green: '#00e676', red: '#ff3d3d', cyan: '#00d4ff', yellow: '#ffc400', purple: '#7c3aed',
}

const Badge = ({ children, color = 'cyan' }) => {
  const colors = {
    cyan: 'rgba(0,212,255,0.08)', green: 'rgba(0,230,118,0.08)',
    red: 'rgba(255,61,61,0.08)', yellow: 'rgba(255,196,0,0.08)', purple: 'rgba(124,58,237,0.08)',
  }
  const borders = {
    cyan: 'rgba(0,212,255,0.2)', green: 'rgba(0,230,118,0.2)',
    red: 'rgba(255,61,61,0.2)', yellow: 'rgba(255,196,0,0.2)', purple: 'rgba(124,58,237,0.2)',
  }
  const texts = { cyan: '#00d4ff', green: '#00e676', red: '#ff3d3d', yellow: '#ffc400', purple: '#7c3aed' }
  return (
    <span style={{ fontSize: 8, padding: '3px 7px', borderRadius: 8, fontFamily: 'Space Mono', fontWeight: 700, background: colors[color], border: `1px solid ${borders[color]}`, color: texts[color] }}>
      {children}
    </span>
  )
}

const SegBtn = ({ label, active, onClick, color = 'cyan' }) => {
  const activeColors = {
    cyan: { bg: 'rgba(0,212,255,0.1)', border: '#00d4ff', color: '#00d4ff' },
    green: { bg: 'rgba(0,230,118,0.1)', border: '#00e676', color: '#00e676' },
    red: { bg: 'rgba(255,61,61,0.1)', border: '#ff3d3d', color: '#ff3d3d' },
    purple: { bg: 'rgba(124,58,237,0.1)', border: '#7c3aed', color: '#7c3aed' },
  }
  const ac = activeColors[color] || activeColors.cyan
  return (
    <button
      onClick={onClick}
      style={{
        background: active ? ac.bg : '#151a26',
        border: `1px solid ${active ? ac.border : '#1e2840'}`,
        borderRadius: 5,
        color: active ? ac.color : '#718096',
        fontSize: 9,
        fontWeight: 700,
        padding: '5px 9px',
        cursor: 'pointer',
        fontFamily: 'Syne',
        transition: 'all 0.12s',
      }}
    >
      {label}
    </button>
  )
}

// ── Main Optimizer Page ──────────────────────────────────────────────────────
export default function OptimizerPage() {
  const {
    inputs, setInput, runOptimize, optimizing, optimizerResult, optimizerError,
    selectedStrategy, selectStrategy,
  } = useStore()

  useEffect(() => {
    if (optimizerError) toast.error(optimizerError)
  }, [optimizerError])

  const strat = optimizerResult?.strategies?.[selectedStrategy]

  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: '16px 18px', display: 'flex', flexDirection: 'column', gap: 12 }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <div style={{ fontSize: 20, fontWeight: 800 }}>Strategy Optimizer</div>
          <div style={{ fontSize: 10, color: '#718096', marginTop: 3, fontFamily: 'Space Mono' }}>
            {optimizerResult
              ? `${optimizerResult.symbol} · SPOT ${optimizerResult.spot.toLocaleString()} · IV ${optimizerResult.iv}% · ${optimizerResult.n_candidates_evaluated} candidates in ${optimizerResult.optimization_time_ms}ms`
              : 'Configure inputs below and run optimizer'}
          </div>
        </div>
        <button
          onClick={() => {
            runOptimize()
            toast.loading('Running optimizer...', { id: 'opt', duration: 3000 })
          }}
          disabled={optimizing}
          style={{ background: optimizing ? '#0d3a5a' : 'linear-gradient(135deg,#00b4d8,#0077b6)', border: 'none', borderRadius: 9, color: '#fff', fontSize: 12, fontWeight: 800, padding: '10px 20px', cursor: optimizing ? 'not-allowed' : 'pointer', fontFamily: 'Syne', boxShadow: '0 3px 16px rgba(0,119,182,0.3)' }}
        >
          {optimizing ? '⏳ Optimizing...' : '⚡ Run Optimizer'}
        </button>
      </div>

      {/* Inputs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,1fr)', gap: 10 }}>
        <div style={S.card}>
          <div style={S.label}>Capital Available</div>
          <input
            value={`₹ ${Number(inputs.capital).toLocaleString()}`}
            onChange={(e) => {
              const v = parseInt(e.target.value.replace(/[^0-9]/g, ''))
              if (!isNaN(v)) setInput('capital', v)
            }}
            style={{ background: '#151a26', border: '1px solid #1e2840', borderRadius: 6, color: '#e2e8f8', fontSize: 13, fontWeight: 700, fontFamily: 'Space Mono', padding: '6px 9px', width: '100%', outline: 'none' }}
          />
        </div>
        <div style={S.card}>
          <div style={S.label}>Market View</div>
          <div style={{ display: 'flex', gap: 3 }}>
            {['bullish', 'bearish', 'neutral'].map((v) => (
              <SegBtn key={v} label={v.charAt(0).toUpperCase() + v.slice(1)} active={inputs.market_view === v}
                onClick={() => setInput('market_view', v)}
                color={v === 'bullish' ? 'green' : v === 'bearish' ? 'red' : 'cyan'} />
            ))}
          </div>
        </div>
        <div style={S.card}>
          <div style={S.label}>Vol Outlook</div>
          <div style={{ display: 'flex', gap: 3 }}>
            {['rising', 'falling', 'stable'].map((v) => (
              <SegBtn key={v} label={v.charAt(0).toUpperCase() + v.slice(1)} active={inputs.volatility_outlook === v}
                onClick={() => setInput('volatility_outlook', v)}
                color={v === 'rising' ? 'red' : v === 'falling' ? 'green' : 'cyan'} />
            ))}
          </div>
        </div>
        <div style={S.card}>
          <div style={S.label}>Risk Appetite</div>
          <div style={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
            {['conservative', 'moderate', 'aggressive'].map((v) => (
              <SegBtn key={v} label={v.charAt(0).toUpperCase() + v.slice(1)} active={inputs.risk_appetite === v}
                onClick={() => setInput('risk_appetite', v)} color='cyan' />
            ))}
          </div>
        </div>
        <div style={S.card}>
          <div style={S.label}>Time Horizon</div>
          <div style={{ display: 'flex', gap: 3 }}>
            {['weekly', 'monthly'].map((v) => (
              <SegBtn key={v} label={v.charAt(0).toUpperCase() + v.slice(1)} active={inputs.time_horizon === v}
                onClick={() => setInput('time_horizon', v)} color='purple' />
            ))}
          </div>
        </div>
      </div>

      {/* Results */}
      {!optimizerResult && !optimizing && (
        <div style={{ ...S.card, textAlign: 'center', padding: '40px', color: '#4a5568' }}>
          <div style={{ fontSize: 36, marginBottom: 8 }}>⚡</div>
          <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 6 }}>Configure and run the optimizer</div>
          <div style={{ fontSize: 11, fontFamily: 'Space Mono' }}>
            Set your inputs above, then click "Run Optimizer" to get EV-ranked strategies
          </div>
        </div>
      )}

      {optimizing && (
        <div style={{ ...S.card, textAlign: 'center', padding: '40px', color: '#718096' }}>
          <div style={{ fontSize: 24, marginBottom: 8, animation: 'spin 1s linear infinite', display: 'inline-block' }}>⚙️</div>
          <div style={{ fontSize: 12, fontFamily: 'Space Mono' }}>
            Fetching live chain · Generating strategy universe · Computing EV via lognormal integration...
          </div>
        </div>
      )}

      {optimizerResult && !optimizing && (
        <>
          {/* Strategy list + payoff */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.6fr 1fr', gap: 12 }}>

            {/* Ranked strategies */}
            <div style={S.card}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div style={S.label}>Optimized Rankings</div>
                <Badge color='cyan'>EV RANKED</Badge>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {optimizerResult.strategies.map((s, i) => (
                  <div
                    key={i}
                    onClick={() => selectStrategy(i)}
                    style={{
                      background: selectedStrategy === i ? 'rgba(0,212,255,0.05)' : '#151a26',
                      border: `1px solid ${selectedStrategy === i ? '#00d4ff' : '#1e2840'}`,
                      borderLeft: `3px solid ${i === 0 ? '#00d4ff' : i === 1 ? '#00e676' : '#ffc400'}`,
                      borderRadius: 8, padding: '10px 12px', cursor: 'pointer',
                      transition: 'all 0.15s',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <div>
                        <div style={{ fontSize: 12, fontWeight: 700 }}>{s.name}</div>
                        <div style={{ fontSize: 9, color: '#718096', fontFamily: 'Space Mono', marginTop: 2 }}>
                          {s.legs.map(l => `${l.position === 'long' ? '+' : '-'}${l.K}${l.option_type === 'call' ? 'CE' : 'PE'}`).join(' / ')}
                        </div>
                      </div>
                      <div style={{ fontSize: 9, color: '#718096', fontFamily: 'Space Mono' }}>#{i + 1}</div>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 4 }}>
                      {[
                        { l: 'EV', v: `+₹${Math.abs(s.ev).toLocaleString()}`, c: S.green },
                        { l: 'POP', v: `${(s.pop * 100).toFixed(1)}%`, c: S.cyan },
                        { l: 'Max Loss', v: `-₹${Math.abs(s.max_loss).toLocaleString()}`, c: S.red },
                        { l: 'Sharpe', v: s.sharpe.toFixed(2), c: '#e2e8f8' },
                      ].map(({ l, v, c }) => (
                        <div key={l}>
                          <div style={{ fontSize: 7, color: '#4a5568', fontFamily: 'Space Mono', textTransform: 'uppercase', letterSpacing: '0.8px' }}>{l}</div>
                          <div style={{ fontSize: 11, fontWeight: 700, fontFamily: 'Space Mono', color: c, marginTop: 1 }}>{v}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Payoff chart */}
            {strat && (
              <div style={S.card}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                  <div style={S.label}>Payoff at Expiry – {strat.name}</div>
                  <Badge color='green'>LIVE IV</Badge>
                </div>
                <ResponsiveContainer width="100%" height={180}>
                  <AreaChart data={strat.payoff_curve.prices.map((p, i) => ({ price: p, pnl: strat.payoff_curve.payoffs[i] }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e2840" />
                    <XAxis dataKey="price" tickFormatter={(v) => v.toLocaleString()} tick={{ fontSize: 8, fill: '#4a5568', fontFamily: 'Space Mono' }} />
                    <YAxis tickFormatter={(v) => `₹${v >= 0 ? '+' : ''}${v.toLocaleString()}`} tick={{ fontSize: 8, fill: '#4a5568', fontFamily: 'Space Mono' }} width={70} />
                    <Tooltip
                      contentStyle={{ background: '#111520', border: '1px solid #1e2840', borderRadius: 7, fontSize: 10, fontFamily: 'Space Mono' }}
                      formatter={(v) => [`₹${v.toFixed(0)}`, 'P&L']}
                      labelFormatter={(v) => `Price: ${Number(v).toLocaleString()}`}
                    />
                    <ReferenceLine y={0} stroke="#1e2840" strokeWidth={1} />
                    {strat.payoff_curve.breakevens.map((be, i) => (
                      <ReferenceLine key={i} x={be} stroke="#00d4ff" strokeDasharray="4 3" strokeWidth={1} />
                    ))}
                    <defs>
                      <linearGradient id="pgGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#00e676" stopOpacity={0.3} />
                        <stop offset="100%" stopColor="#00e676" stopOpacity={0.02} />
                      </linearGradient>
                      <linearGradient id="plGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#ff3d3d" stopOpacity={0.02} />
                        <stop offset="100%" stopColor="#ff3d3d" stopOpacity={0.3} />
                      </linearGradient>
                    </defs>
                    <Area type="monotone" dataKey="pnl" stroke="#00e676" strokeWidth={2}
                      fill="url(#pgGrad)" dot={false} activeDot={{ r: 4, fill: '#00e676' }} />
                  </AreaChart>
                </ResponsiveContainer>
                <div style={{ display: 'flex', gap: 16, marginTop: 8, fontSize: 9, color: '#718096', fontFamily: 'Space Mono' }}>
                  <span>Breakeven: {strat.payoff_curve.breakevens.map(b => b.toLocaleString()).join(', ')}</span>
                  <span style={{ marginLeft: 'auto' }}>Spot: <b style={{ color: '#e2e8f8' }}>{optimizerResult.spot.toLocaleString()}</b></span>
                </div>
              </div>
            )}

            {/* Greeks */}
            {strat && (
              <div style={S.card}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                  <div style={S.label}>Greeks (Black-Scholes Exact)</div>
                  <Badge color='yellow'>IV: {optimizerResult.iv}%</Badge>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                  {[
                    { name: 'Delta (Δ)', key: 'delta', color: S.green, pct: Math.abs(strat.greeks.delta) * 100 },
                    { name: 'Gamma (Γ)', key: 'gamma', color: S.cyan, pct: strat.greeks.gamma * 5000 },
                    { name: 'Vega (ν)', key: 'vega', color: S.yellow, pct: Math.abs(strat.greeks.vega) * 200 },
                    { name: 'Theta (Θ)', key: 'theta', color: S.red, pct: Math.abs(strat.greeks.theta) * 50 },
                  ].map(({ name, key, color, pct }) => (
                    <div key={key} style={{ background: '#151a26', borderRadius: 7, padding: 10 }}>
                      <div style={{ fontSize: 8, color: '#718096', fontFamily: 'Space Mono', textTransform: 'uppercase', letterSpacing: 1 }}>{name}</div>
                      <div style={{ fontSize: 17, fontWeight: 800, fontFamily: 'Space Mono', color, margin: '4px 0 6px' }}>
                        {strat.greeks[key] >= 0 && key !== 'theta' ? '+' : ''}{strat.greeks[key].toFixed(key === 'gamma' ? 5 : 3)}
                      </div>
                      <div style={{ height: 3, background: '#1e2840', borderRadius: 2 }}>
                        <div style={{ height: 3, background: color, borderRadius: 2, width: `${Math.min(pct, 100)}%`, transition: 'width 0.8s ease' }} />
                      </div>
                    </div>
                  ))}
                </div>
                <div style={{ background: '#151a26', borderRadius: 7, padding: 10, marginTop: 8 }}>
                  <div style={{ fontSize: 8, color: '#718096', fontFamily: 'Space Mono', textTransform: 'uppercase', marginBottom: 6 }}>IV Shock (±5%)</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, fontFamily: 'Space Mono', padding: '3px 0' }}>
                    <span style={{ color: '#718096' }}>IV −5%</span>
                    <span style={{ color: S.red }}>P&L: calculating...</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, fontFamily: 'Space Mono', padding: '3px 0' }}>
                    <span style={{ color: '#718096' }}>IV +5%</span>
                    <span style={{ color: S.green }}>P&L: calculating...</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Bottom row */}
          {strat && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>

              {/* POP */}
              <div style={S.card}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                  <div style={S.label}>Probability Model</div>
                  <Badge color='green'>LOGNORMAL CDF</Badge>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                  <div style={{ position: 'relative', width: 88, height: 88, flexShrink: 0 }}>
                    <svg viewBox="0 0 88 88" style={{ transform: 'rotate(-90deg)' }}>
                      <circle cx="44" cy="44" r="34" fill="none" stroke="#1e2840" strokeWidth={7} />
                      <circle cx="44" cy="44" r="34" fill="none" stroke="#00e676" strokeWidth={7}
                        strokeDasharray={`${strat.pop * 214} 214`} strokeLinecap="round"
                        style={{ transition: 'stroke-dasharray 1s ease' }} />
                    </svg>
                    <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                      <div style={{ fontSize: 17, fontWeight: 800, fontFamily: 'Space Mono', color: S.green }}>{(strat.pop * 100).toFixed(0)}%</div>
                      <div style={{ fontSize: 7, color: '#718096', fontFamily: 'Space Mono' }}>POP</div>
                    </div>
                  </div>
                  <div style={{ flex: 1 }}>
                    {[
                      { l: 'Prob of Profit', v: `${(strat.pop * 100).toFixed(1)}%`, c: S.green },
                      { l: 'Breakeven(s)', v: strat.breakevens.map(b => b.toLocaleString()).join(', '), c: S.cyan },
                      { l: 'EV / MaxLoss', v: strat.ev_per_max_loss.toFixed(3), c: '#e2e8f8' },
                      { l: 'Capital Eff.', v: `${(strat.capital_efficiency * 100).toFixed(1)}%`, c: S.yellow },
                    ].map(({ l, v, c }) => (
                      <div key={l} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, padding: '4px 0', borderBottom: '1px solid rgba(30,40,64,0.5)' }}>
                        <span style={{ color: '#718096' }}>{l}</span>
                        <span style={{ fontFamily: 'Space Mono', fontWeight: 700, color: c }}>{v}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Margin */}
              <div style={S.card}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                  <div style={S.label}>Capital & Margin</div>
                  <Badge color='cyan'>SPAN CALC</Badge>
                </div>
                <div style={{ fontSize: 10, display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                  <span style={{ color: '#718096' }}>Margin Used</span>
                  <span style={{ fontFamily: 'Space Mono', fontWeight: 700, color: S.cyan }}>
                    ₹{strat.margin.total.toLocaleString()} / ₹{inputs.capital.toLocaleString()} ({((strat.margin.total / inputs.capital) * 100).toFixed(1)}%)
                  </span>
                </div>
                <div style={{ height: 8, background: '#151a26', borderRadius: 5, overflow: 'hidden' }}>
                  <div style={{ height: 8, background: 'linear-gradient(90deg,#00d4ff,#7c3aed)', borderRadius: 5, width: `${Math.min((strat.margin.total / inputs.capital) * 100, 100)}%`, transition: 'width 0.8s ease' }} />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 10 }}>
                  {[
                    { l: 'SPAN Margin', v: `₹${strat.margin.span.toLocaleString()}` },
                    { l: 'Exposure', v: `₹${strat.margin.exposure.toLocaleString()}` },
                    { l: 'Available', v: `₹${(inputs.capital - strat.margin.total).toLocaleString()}`, c: S.green },
                    { l: 'Net Premium', v: `${strat.net_premium >= 0 ? '+' : ''}₹${strat.net_premium.toLocaleString()}`, c: strat.net_premium >= 0 ? S.green : S.red },
                  ].map(({ l, v, c }) => (
                    <div key={l} style={{ background: '#151a26', borderRadius: 7, padding: 10 }}>
                      <div style={{ fontSize: 8, color: '#718096', fontFamily: 'Space Mono', textTransform: 'uppercase' }}>{l}</div>
                      <div style={{ fontSize: 14, fontWeight: 800, fontFamily: 'Space Mono', marginTop: 3, color: c || '#e2e8f8' }}>{v}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Strategy comparison table */}
              <div style={S.card}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                  <div style={S.label}>All Strategies Compared</div>
                  <Badge color='cyan'>EV RANKED</Badge>
                </div>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr>
                      {['Strategy', 'POP', 'EV', 'Sharpe'].map(h => (
                        <th key={h} style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: 1, color: '#4a5568', fontFamily: 'Space Mono', padding: '0 0 8px', textAlign: 'left', borderBottom: '1px solid #1e2840' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {optimizerResult.strategies.map((s, i) => (
                      <tr key={i} onClick={() => selectStrategy(i)} style={{ cursor: 'pointer' }}>
                        <td style={{ fontSize: 10, fontWeight: 700, padding: '7px 0', borderBottom: '1px solid rgba(30,40,64,0.4)', color: selectedStrategy === i ? S.cyan : '#e2e8f8' }}>{s.name}</td>
                        <td style={{ fontSize: 10, fontFamily: 'Space Mono', padding: '7px 0', borderBottom: '1px solid rgba(30,40,64,0.4)', color: s.pop > 0.6 ? S.green : S.yellow }}>{(s.pop * 100).toFixed(1)}%</td>
                        <td style={{ fontSize: 10, fontFamily: 'Space Mono', padding: '7px 0', borderBottom: '1px solid rgba(30,40,64,0.4)', color: s.ev > 0 ? S.green : S.red }}>+₹{Math.abs(s.ev).toLocaleString()}</td>
                        <td style={{ fontSize: 10, fontFamily: 'Space Mono', padding: '7px 0', borderBottom: '1px solid rgba(30,40,64,0.4)' }}>{s.sharpe.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Mock data warning */}
          {optimizerResult?.is_mock_data && (
            <div style={{ background: 'rgba(255,196,0,0.05)', border: '1px solid rgba(255,196,0,0.15)', borderRadius: 7, padding: '8px 14px', fontSize: 9, color: '#718096', fontFamily: 'Space Mono' }}>
              ⚠️ Using simulated data. NSE live data requires active NSE session. Configure API credentials in .env for live data.
            </div>
          )}
        </>
      )}

      <div style={{ background: 'rgba(255,196,0,0.03)', border: '1px solid rgba(255,196,0,0.1)', borderRadius: 7, padding: '8px 14px', fontSize: 9, color: '#4a5568', fontFamily: 'Space Mono' }}>
        ⚠️ Educational & analytical tool only. Not investment advice. Options trading involves substantial risk of loss.
      </div>

      <style>{`@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }`}</style>
    </div>
  )
}
