import { useEffect, useRef, useState } from 'react'
import Icon from './Icon.jsx'
import * as api from '../api.js'

const SUGGESTIONS = [
  'Where should I charge right now?',
  'When is the greenest time to charge tonight?',
  'Which nearby charger is cheapest for my car?',
]

export default function Chat({ getContext, onAction }) {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([{ role: 'assistant', content: 'Hi! I’m your GRIഢം assistant. Ask me where or when to charge, and I’ll use live grid data to answer.' }])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bodyRef = useRef(null)
  useEffect(() => { bodyRef.current?.scrollTo(0, bodyRef.current.scrollHeight) }, [messages, loading, open])

  async function send(text) {
    const q = (text ?? input).trim()
    if (!q || loading) return
    setInput('')
    const next = [...messages, { role: 'user', content: q }]
    setMessages(next); setLoading(true)
    try {
      const res = await api.chat(next.filter((m) => m.role !== 'system').slice(-8), getContext())
      setMessages((m) => [...m, { role: 'assistant', content: res.reply || '…' }])
      if (res.action) onAction?.(res.action)
    } catch {
      setMessages((m) => [...m, { role: 'assistant', content: 'I could not reach the assistant — check the Groq key and internet.' }])
    } finally { setLoading(false) }
  }

  return (
    <>
      <button className="chat-fab" onClick={() => setOpen((v) => !v)} title="Ask GRIഢം">
        <Icon name={open ? 'x' : 'bolt'} size={22} />
      </button>
      {open && (
        <div className="chat-panel">
          <div className="chat-head"><span className="live"><i /></span> GRIഢം assistant <span className="muted small" style={{ marginLeft: 'auto' }}>grid-aware</span></div>
          <div className="chat-body" ref={bodyRef}>
            {messages.map((m, i) => <div key={i} className={'msg ' + m.role}>{m.content}</div>)}
            {loading && <div className="msg assistant"><span className="dots"><i /><i /><i /></span></div>}
            {messages.length <= 1 && (
              <div className="chat-sugg">{SUGGESTIONS.map((s) => <button key={s} onClick={() => send(s)}>{s}</button>)}</div>
            )}
          </div>
          <div className="chat-input">
            <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && send()} placeholder="Ask about charging…" />
            <button className="btn primary" onClick={() => send()} disabled={loading}><Icon name="nav" size={16} /></button>
          </div>
        </div>
      )}
    </>
  )
}
