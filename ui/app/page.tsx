'use client'
import { useState, useRef, useEffect, useCallback } from 'react'
import JarvisOrb from '../components/JarvisOrb'

const API = process.env.NEXT_PUBLIC_API_URL || 'https://jarvis-api-fufo.onrender.com'

interface Message { role: 'user' | 'assistant'; content: string; agent?: string; ts: number }

const MODES = ['JARVIS', 'Research', 'Voice', 'Browser', 'Code']

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [thinking, setThinking] = useState(false)
  const [active, setActive] = useState(false)
  const [mode, setMode] = useState('JARVIS')
  const [status, setStatus] = useState('Idle')
  const [recording, setRecording] = useState(false)
  const [chatOpen, setChatOpen] = useState(true)
  const [chatsOpen, setChatsOpen] = useState(false)
  const [chatList, setChatList] = useState<{ id: string; title: string; last_active: string }[]>([])
  const [awake, setAwake] = useState<boolean | null>(null) // null = checking
  const [wakeElapsed, setWakeElapsed] = useState(0)
  const [wakeEta, setWakeEta] = useState<number | null>(null) // median of past observed wake times (seconds)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textRef = useRef<HTMLTextAreaElement>(null)
  const mediaRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<BlobPart[]>([])
  const historyRef = useRef<{ role: string; content: string }[]>([])

  // Stable session id (persisted) so the backend keeps conversation + memory continuity
  const [sid, setSid] = useState(() => {
    if (typeof window === 'undefined') return ''
    let s = window.localStorage.getItem('jarvis_sid')
    if (!s) { s = crypto.randomUUID(); window.localStorage.setItem('jarvis_sid', s) }
    return s
  })

  const startNewChat = useCallback(() => {
    const fresh = crypto.randomUUID()
    window.localStorage.setItem('jarvis_sid', fresh)
    setSid(fresh)
    setMessages([])
    historyRef.current = []
    setChatsOpen(false)
  }, [])

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, thinking])

  // Real wake tracking — not a fake countdown. We ping /health, and while it's
  // down we show the actual elapsed seconds we've measured (never invented),
  // plus a learned ETA from previously observed wake durations for this
  // browser (localStorage), refined every time we witness a real one.
  useEffect(() => {
    let cancelled = false
    let start: number | null = null
    let timer: ReturnType<typeof setInterval> | null = null

    const past = JSON.parse(window.localStorage.getItem('jarvis_wake_times') || '[]') as number[]
    if (past.length) setWakeEta(Math.round(past.reduce((a, b) => a + b, 0) / past.length))

    const recordWake = (seconds: number) => {
      const updated = [...past, seconds].slice(-8) // keep last 8 observations
      window.localStorage.setItem('jarvis_wake_times', JSON.stringify(updated))
      setWakeEta(Math.round(updated.reduce((a, b) => a + b, 0) / updated.length))
    }

    const check = async () => {
      try {
        const res = await fetch(`${API}/health`, { signal: AbortSignal.timeout(6000) })
        if (!res.ok) throw new Error('not ok')
        if (cancelled) return
        if (start !== null) {
          recordWake(Math.round((Date.now() - start) / 1000))
          if (timer) clearInterval(timer)
          start = null
          setWakeElapsed(0)
        }
        setAwake(true)
      } catch {
        if (cancelled) return
        setAwake(false)
        if (start === null) {
          start = Date.now()
          timer = setInterval(() => { if (start) setWakeElapsed(Math.round((Date.now() - start) / 1000)) }, 1000)
        }
      }
    }
    check()
    const poll = setInterval(check, 3000)
    return () => { cancelled = true; clearInterval(poll); if (timer) clearInterval(timer) }
  }, [])

  // Load the recent-chats list (for the Chats tab + orb hover) once, and again
  // whenever it's opened so it reflects the latest session titles/order.
  const loadChatList = useCallback(async () => {
    try {
      const res = await fetch(`${API}/chat/sessions?limit=30`, { signal: AbortSignal.timeout(8000) })
      if (!res.ok) return
      const data = await res.json()
      setChatList(data.sessions || [])
    } catch {}
  }, [])
  useEffect(() => { loadChatList() }, [loadChatList])

  const openChat = useCallback(async (id: string) => {
    try {
      const res = await fetch(`${API}/chat/${id}/history`, { signal: AbortSignal.timeout(10000) })
      if (!res.ok) return
      const data = await res.json()
      setMessages((data.messages || []).map((m: any) => ({ role: m.role, content: m.content, ts: new Date(m.created_at).getTime() })))
      window.localStorage.setItem('jarvis_sid', id)
      setSid(id)
      setChatsOpen(false)
      setChatOpen(true)
    } catch {}
  }, [])

  const send = useCallback(async (text: string) => {
    const content = text.trim()
    if (!content || thinking) return
    setInput('')
    if (textRef.current) textRef.current.style.height = 'auto'
    const userMsg: Message = { role: 'user', content, ts: Date.now() }
    setMessages(prev => [...prev, userMsg])
    historyRef.current = [...historyRef.current, { role: 'user', content }]
    setThinking(true)
    setActive(true)
    setStatus('Processing…')
    // API expects { message, session_id, mode }. mode 'agent' routes through the
    // multi-agent orchestrator; plain JARVIS chat stays 'text'.
    const payload = { message: content, session_id: sid, mode: (mode === 'JARVIS' || mode === 'Voice') ? 'text' : 'agent' }
    let reply = ''
    let agentUsed: string | undefined
    let ok = false
    // Up to 3 tries — the first request after idle wakes the free-tier backend (~30-60s).
    for (let attempt = 0; attempt < 3 && !ok; attempt++) {
      try {
        const res = await fetch(`${API}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        reply = data.response || data.message || '…'
        agentUsed = data.agent_used
        ok = true
      } catch (err) {
        if (attempt < 2) {
          setStatus(wakeEta ? `Waking JARVIS… usually ~${wakeEta}s (based on past wakes)`           : 'Waking JARVIS (free tier naps after idle)…')
          await new Promise(r => setTimeout(r, 4000))
        }
      }
    }
    if (ok) {
      const agentMsg: Message = { role: 'assistant', content: reply, agent: agentUsed || 'JARVIS', ts: Date.now() }
      setMessages(prev => [...prev, agentMsg])
      historyRef.current = [...historyRef.current, { role: 'assistant', content: reply }]
      setStatus(agentUsed ? `${agentUsed} responded` : 'Ready')
      loadChatList()
    } else {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Still waking up — the backend was asleep and didn\'t answer in time. Give it ~30 seconds, then send again.', ts: Date.now() }])
      setStatus('Error')
    }
    setThinking(false)
    setActive(false)
  }, [thinking, mode, wakeEta])

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input) }
  }

  const autoResize = () => {
    const el = textRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 140) + 'px'
  }

  const startVoice = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const rec = new MediaRecorder(stream)
      chunksRef.current = []
      rec.ondataavailable = e => chunksRef.current.push(e.data)
      rec.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        const b64 = await new Promise<string>(resolve => {
          const reader = new FileReader()
          reader.onloadend = () => resolve((reader.result as string).split(',')[1])
          reader.readAsDataURL(blob)
        })
        try {
          const res = await fetch(`${API}/voice/transcribe`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ audio_b64: b64, mime_type: 'audio/webm' })
          })
          const d = await res.json()
          if (d.transcript) send(d.transcript)
        } catch {}
        stream.getTracks().forEach(t => t.stop())
      }
      rec.start()
      mediaRef.current = rec
      setRecording(true)
    } catch {}
  }

  const stopVoice = () => {
    mediaRef.current?.stop()
    setRecording(false)
  }

  const orbSize = typeof window !== 'undefined' ? Math.min(window.innerWidth * 0.55, 520) : 420

  return (
    <div style={{ position: 'fixed', inset: 0, background: '#000', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

      {/* Ambient background */}
      <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 80% 60% at 50% 40%, rgba(180,80,10,0.07) 0%, rgba(0,0,0,0) 70%)', pointerEvents: 'none' }} />

      {/* Corner HUD lines */}
      {[['top','left'],['top','right'],['bottom','left'],['bottom','right']].map(([v, h]) => (
        <div key={v+h} style={{
          position: 'absolute', [v as string]: 16, [h as string]: 16, width: 32, height: 32,
          borderTop: v === 'top' ? '1px solid rgba(255,140,40,0.3)' : 'none',
          borderBottom: v === 'bottom' ? '1px solid rgba(255,140,40,0.3)' : 'none',
          borderLeft: h === 'left' ? '1px solid rgba(255,140,40,0.3)' : 'none',
          borderRight: h === 'right' ? '1px solid rgba(255,140,40,0.3)' : 'none',
          pointerEvents: 'none'
        }} />
      ))}

      {/* Top bar */}
      <div style={{ position: 'relative', zIndex: 10, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 8, height: 8, borderRadius: '50%',
            background: awake === null ? '#999' : awake ? '#3ddc4a' : '#ff3b30',
            boxShadow: awake === false ? '0 0 8px #ff3b30' : awake ? '0 0 6px #3ddc4a' : 'none',
          }} />
          <span style={{ fontSize: 13, fontWeight: 700, letterSpacing: 3, color: 'rgba(255,200,80,0.9)', textTransform: 'uppercase' }}>JARVIS</span>
          <span style={{ fontSize: 10, color: awake ? 'rgba(60,220,80,0.7)' : 'rgba(255,80,60,0.75)', letterSpacing: 1 }}>
            {awake === null ? 'CHECKING…' : awake ? 'ONLINE' : (
              wakeEta ? `WAKING · ${wakeElapsed}s (usually ~${wakeEta}s)` : `WAKING · ${wakeElapsed}s elapsed`
            )}
          </span>
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          {MODES.map(m => (
            <button key={m} onClick={() => setMode(m)}
              style={{
                padding: '4px 12px', borderRadius: 20, fontSize: 11, fontWeight: 500, cursor: 'pointer',
                border: mode === m ? '1px solid rgba(255,140,40,0.6)' : '1px solid rgba(255,255,255,0.06)',
                background: mode === m ? 'rgba(255,120,20,0.12)' : 'transparent',
                color: mode === m ? 'rgba(255,180,60,0.95)' : 'rgba(255,255,255,0.35)',
                transition: 'all 0.15s',
              }}
            >{m}</button>
          ))}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)', letterSpacing: 0.5 }}>{status}</span>
          <button onClick={() => { setChatsOpen(o => !o); if (!chatsOpen) loadChatList() }}
            style={{ padding: '4px 10px', borderRadius: 8, fontSize: 11, border: chatsOpen ? '1px solid rgba(255,140,40,0.5)' : '1px solid rgba(255,255,255,0.1)', background: chatsOpen ? 'rgba(255,120,20,0.12)' : 'transparent', color: chatsOpen ? 'rgba(255,180,60,0.9)' : 'rgba(255,255,255,0.4)', cursor: 'pointer' }}>
            Chats
          </button>
          <button onClick={() => setChatOpen(o => !o)}
            style={{ padding: '4px 10px', borderRadius: 8, fontSize: 11, border: '1px solid rgba(255,255,255,0.1)', background: 'transparent', color: 'rgba(255,255,255,0.4)', cursor: 'pointer' }}>
            {chatOpen ? 'Hide Chat' : 'Show Chat'}
          </button>
        </div>
      </div>

      {/* Main content */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden', position: 'relative' }}>
        {/* Orb */}
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}
          onMouseEnter={() => loadChatList()}>
          <div style={{ position: 'relative' }}
            onMouseEnter={() => setChatsOpen(true)}
            onMouseLeave={() => setChatsOpen(false)}>
            <JarvisOrb size={orbSize} active={active || recording} />
            {chatsOpen && (
              <div style={{
                position: 'absolute', top: '50%', left: '100%', transform: 'translateY(-50%)',
                marginLeft: 16, width: 260, maxHeight: 360, overflowY: 'auto',
                background: 'rgba(10,6,0,0.95)', border: '1px solid rgba(255,140,40,0.2)',
                borderRadius: 12, padding: 10, zIndex: 20, backdropFilter: 'blur(12px)',
              }}>
                <div style={{ fontSize: 10, letterSpacing: 1.5, color: 'rgba(255,160,60,0.6)', textTransform: 'uppercase', marginBottom: 8, padding: '0 4px' }}>Recent Chats</div>
                <button onClick={startNewChat} style={{ width: '100%', textAlign: 'left', padding: '8px 10px', marginBottom: 4, borderRadius: 8, border: '1px dashed rgba(255,140,40,0.3)', background: 'transparent', color: 'rgba(255,180,80,0.8)', fontSize: 12, cursor: 'pointer' }}>+ New Chat</button>
                {chatList.length === 0 && <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.25)', padding: '8px 10px' }}>No past chats yet.</div>}
                {chatList.map(c => (
                  <button key={c.id} onClick={() => openChat(c.id)}
                    style={{ width: '100%', textAlign: 'left', padding: '8px 10px', marginBottom: 2, borderRadius: 8, border: c.id === sid ? '1px solid rgba(255,140,40,0.4)' : '1px solid transparent', background: c.id === sid ? 'rgba(255,120,20,0.1)' : 'transparent', color: 'rgba(240,230,220,0.8)', fontSize: 12, cursor: 'pointer', overflow: 'hidden' }}>
                    <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{c.title}</div>
                    <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)', marginTop: 2 }}>{new Date(c.last_active).toLocaleString()}</div>
                  </button>
                ))}
              </div>
            )}
            {/* Center label */}
            <div style={{ position: 'absolute', bottom: '18%', left: '50%', transform: 'translateX(-50%)', textAlign: 'center', pointerEvents: 'none' }}>
              {thinking ? (
                <div style={{ display: 'flex', gap: 5, justifyContent: 'center' }}>
                  {[0,1,2].map(i => <div key={i} className="dot-bounce" style={{ width: 6, height: 6, borderRadius: '50%', background: 'rgba(255,160,50,0.8)', animationDelay: `${i*0.2}s` }} />)}
                </div>
              ) : (
                <span style={{ fontSize: 11, color: 'rgba(255,160,50,0.4)', letterSpacing: 2, textTransform: 'uppercase' }}>{mode}</span>
              )}
            </div>
          </div>
        </div>

        {/* Persistent Chats sidebar — toggled from the top-bar "Chats" button */}
        {chatsOpen && chatOpen && (
          <div style={{
            width: 220, borderLeft: '1px solid rgba(255,140,40,0.08)', background: 'rgba(6,4,0,0.9)',
            backdropFilter: 'blur(16px)', display: 'flex', flexDirection: 'column', overflowY: 'auto', padding: 10,
          }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'rgba(255,160,60,0.6)', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 8, padding: '0 4px' }}>Chats</div>
            <button onClick={startNewChat} style={{ width: '100%', textAlign: 'left', padding: '8px 10px', marginBottom: 6, borderRadius: 8, border: '1px dashed rgba(255,140,40,0.3)', background: 'transparent', color: 'rgba(255,180,80,0.8)', fontSize: 12, cursor: 'pointer' }}>+ New Chat</button>
            {chatList.length === 0 && <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.25)', padding: '8px 4px' }}>No past chats yet.</div>}
            {chatList.map(c => (
              <button key={c.id} onClick={() => openChat(c.id)}
                style={{ width: '100%', textAlign: 'left', padding: '8px 10px', marginBottom: 2, borderRadius: 8, border: c.id === sid ? '1px solid rgba(255,140,40,0.4)' : '1px solid transparent', background: c.id === sid ? 'rgba(255,120,20,0.1)' : 'transparent', color: 'rgba(240,230,220,0.8)', fontSize: 12, cursor: 'pointer', overflow: 'hidden' }}>
                <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{c.title}</div>
                <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)', marginTop: 2 }}>{new Date(c.last_active).toLocaleString()}</div>
              </button>
            ))}
          </div>
        )}

        {/* Chat panel */}
        {chatOpen && (
          <div style={{
            width: 380, borderLeft: '1px solid rgba(255,140,40,0.08)', background: 'rgba(8,5,0,0.85)',
            backdropFilter: 'blur(16px)', display: 'flex', flexDirection: 'column',
          }}>
            <div style={{ padding: '12px 16px', borderBottom: '1px solid rgba(255,140,40,0.08)', fontSize: 11, fontWeight: 600, color: 'rgba(255,160,60,0.6)', letterSpacing: 2, textTransform: 'uppercase', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>Chat · {mode}</span>
              <button onClick={startNewChat} style={{ fontSize: 10, color: 'rgba(255,180,80,0.7)', background: 'transparent', border: 'none', cursor: 'pointer', letterSpacing: 0.5 }}>+ New</button>
            </div>

            {/* Messages */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '16px 14px', display: 'flex', flexDirection: 'column', gap: 12 }}>
              {messages.length === 0 && (
                <div style={{ textAlign: 'center', marginTop: 40 }}>
                  <div style={{ fontSize: 28, marginBottom: 8 }}>⬡</div>
                  <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.25)', lineHeight: 1.6 }}>JARVIS is ready.<br />Type or speak to begin.</div>
                  {/* Quick prompts */}
                  <div style={{ marginTop: 24, display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {['What can you do?', 'Search the web for me', 'Run a coding task'].map(q => (
                      <button key={q} onClick={() => send(q)}
                        style={{ padding: '8px 14px', borderRadius: 10, border: '1px solid rgba(255,140,40,0.15)', background: 'rgba(255,100,20,0.05)', color: 'rgba(255,200,100,0.6)', fontSize: 12, cursor: 'pointer', textAlign: 'left', transition: 'all 0.15s' }}
                        onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(255,140,40,0.4)')}
                        onMouseLeave={e => (e.currentTarget.style.borderColor = 'rgba(255,140,40,0.15)')}
                      >{q}</button>
                    ))}
                  </div>
                </div>
              )}
              {messages.map((msg, i) => (
                <div key={i} className="fade-up" style={{ display: 'flex', flexDirection: 'column', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                  {msg.role === 'assistant' && msg.agent && (
                    <span style={{ fontSize: 10, color: 'rgba(255,140,40,0.5)', marginBottom: 3, letterSpacing: 1, textTransform: 'uppercase' }}>{msg.agent}</span>
                  )}
                  <div style={{
                    maxWidth: '88%', padding: '10px 14px', borderRadius: msg.role === 'user' ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
                    background: msg.role === 'user' ? 'rgba(255,120,20,0.2)' : 'rgba(255,255,255,0.04)',
                    border: msg.role === 'user' ? '1px solid rgba(255,120,20,0.35)' : '1px solid rgba(255,255,255,0.07)',
                    fontSize: 13, lineHeight: 1.65, color: msg.role === 'user' ? 'rgba(255,210,130,0.95)' : 'rgba(240,240,248,0.85)',
                    whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                  }}>{msg.content}</div>
                </div>
              ))}
              {thinking && (
                <div className="fade-up" style={{ display: 'flex', gap: 5, padding: '10px 14px' }}>
                  {[0,1,2].map(i => <div key={i} className="dot-bounce" style={{ width: 6, height: 6, borderRadius: '50%', background: 'rgba(255,140,50,0.7)', animationDelay: `${i*0.2}s` }} />)}
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div style={{ padding: '12px', borderTop: '1px solid rgba(255,140,40,0.08)' }}>
              <div style={{
                display: 'flex', alignItems: 'flex-end', gap: 8,
                background: 'rgba(255,100,20,0.05)', border: '1px solid rgba(255,140,40,0.15)',
                borderRadius: 14, padding: '8px 10px', transition: 'border-color 0.15s',
              }}>
                <textarea
                  ref={textRef}
                  value={input}
                  onChange={e => { setInput(e.target.value); autoResize() }}
                  onKeyDown={handleKey}
                  placeholder={thinking ? 'JARVIS is thinking…' : 'Ask JARVIS anything…'}
                  disabled={thinking}
                  rows={1}
                  style={{
                    flex: 1, background: 'none', border: 'none', outline: 'none', resize: 'none',
                    color: 'rgba(255,220,140,0.9)', fontSize: 13, lineHeight: 1.6, maxHeight: 140,
                    fontFamily: 'inherit', paddingTop: 2, caretColor: '#ff9500',
                  }}
                />
                <button
                  onMouseDown={startVoice} onMouseUp={stopVoice}
                  onTouchStart={startVoice} onTouchEnd={stopVoice}
                  disabled={thinking}
                  style={{
                    width: 36, height: 36, borderRadius: '50%', border: 'none', cursor: 'pointer', flexShrink: 0,
                    background: recording ? 'rgba(255,80,80,0.3)' : 'rgba(255,100,20,0.08)',
                    color: recording ? '#ff6060' : 'rgba(255,160,60,0.6)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16,
                    boxShadow: recording ? '0 0 12px rgba(255,80,80,0.4)' : 'none',
                    transition: 'all 0.15s',
                  }}
                  title="Hold to talk"
                >🎤</button>
                <button
                  onClick={() => send(input)}
                  disabled={!input.trim() || thinking}
                  style={{
                    width: 36, height: 36, borderRadius: 10, cursor: input.trim() && !thinking ? 'pointer' : 'default', flexShrink: 0,
                    background: input.trim() && !thinking ? 'rgba(255,120,20,0.3)' : 'rgba(255,255,255,0.04)',
                    color: input.trim() && !thinking ? 'rgba(255,200,80,0.9)' : 'rgba(255,255,255,0.2)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16,
                    border: '1px solid rgba(255,120,20,0.2)', transition: 'all 0.15s',
                  }}
                >↑</button>
              </div>
              <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.15)', textAlign: 'center', marginTop: 6, letterSpacing: 0.5 }}>
                JARVIS · {API.replace('https://','')}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
