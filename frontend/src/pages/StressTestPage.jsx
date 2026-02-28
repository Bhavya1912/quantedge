import React from 'react'
import { useNavigate } from 'react-router-dom'
const S = { card: { background: '#111520', border: '1px solid #1e2840', borderRadius: 11, padding: 16 } }
export default function Page() {
  const navigate = useNavigate()
  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: '16px 18px' }}>
      <div style={{ ...S.card, textAlign: 'center', padding: 40 }}>
        <div style={{ fontSize: 36, marginBottom: 12 }}>🔌</div>
        <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 8, color: '#e2e8f8' }}>Backend API Ready</div>
        <div style={{ fontSize: 11, color: '#718096', fontFamily: 'Space Mono', marginBottom: 20 }}>
          Start backend: cd backend && uvicorn main:app --reload
        </div>
        <button onClick={() => navigate('/optimizer')}
          style={{ background: 'linear-gradient(135deg,#00b4d8,#0077b6)', border: 'none', borderRadius: 8, color: '#fff', fontSize: 12, fontWeight: 700, padding: '10px 20px', cursor: 'pointer' }}>
          Back to Optimizer
        </button>
      </div>
    </div>
  )
}
