import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { healthCheck } from '../utils/api'

const S = {
  card: {
    background: '#111520',
    border: '1px solid #1e2840',
    borderRadius: 11,
    padding: 16,
  },
}

export default function Page() {
  const navigate = useNavigate()
  const [status, setStatus] = useState('checking')
  const [message, setMessage] = useState('Checking backend connectivity...')

  useEffect(() => {
    let mounted = true

    healthCheck()
      .then((data) => {
        if (!mounted) return
        setStatus('ok')
        setMessage(`Backend connected (${data.service || 'quantedge-backend'})`)
      })
      .catch(() => {
        if (!mounted) return
        setStatus('error')
        setMessage('Backend not reachable. Set VITE_API_BASE_URL to your Render backend URL.')
      })

    return () => {
      mounted = false
    }
  }, [])

  const statusColor = status === 'ok' ? '#22c55e' : status === 'error' ? '#ef4444' : '#f59e0b'

  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: '16px 18px' }}>
      <div style={{ ...S.card, textAlign: 'center', padding: 40 }}>
        <div style={{ fontSize: 36, marginBottom: 12 }}>🔌</div>
        <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 8, color: '#e2e8f8' }}>
          Backend Status
        </div>
        <div style={{ fontSize: 12, color: statusColor, fontWeight: 700, marginBottom: 8 }}>{status.toUpperCase()}</div>
        <div style={{ fontSize: 11, color: '#94a3b8', fontFamily: 'Space Mono', marginBottom: 20 }}>{message}</div>

        <button
          onClick={() => navigate('/optimizer')}
          style={{
            background: 'linear-gradient(135deg,#00b4d8,#0077b6)',
            border: 'none',
            borderRadius: 8,
            color: '#fff',
            fontSize: 12,
            fontWeight: 700,
            padding: '10px 20px',
            cursor: 'pointer',
          }}
        >
          Go to Optimizer
        </button>
      </div>
    </div>
  )
}
