'use client'
import { useState, useEffect } from 'react'
import JarvisOrb from '@/components/JarvisOrb'
import ChatPanel from '@/components/ChatPanel'
import GoalInput from '@/components/GoalInput'
import AgentStatus from '@/components/AgentStatus'
import ScreenCapture from '@/components/ScreenCapture'

export default function Home() {
  const [chatOpen, setChatOpen] = useState(false)
  const [thinking, setThinking] = useState(false)
  const [agents, setAgents] = useState<any[]>([])
  const [lastGoal, setLastGoal] = useState<any>(null)
  const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    fetch(`${API}/goals/agents`).then(r=>r.json()).then(d=>setAgents(d.agents||[])).catch(()=>{})
  }, [])

  const handleGoal = async (goal: string) => {
    setThinking(true); setChatOpen(true)
    try {
      const res = await fetch(`${API}/goals`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({goal}) })
      setLastGoal(await res.json())
    } finally { setThinking(false) }
  }

  return (
    <div className="w-screen h-screen relative flex items-center justify-center overflow-hidden"
         style={{background:'radial-gradient(ellipse at center, #000d1f 0%, #000408 70%)'}}>
      <div className="absolute inset-0 opacity-5"
           style={{backgroundImage:'linear-gradient(#00d4ff 1px,transparent 1px),linear-gradient(90deg,#00d4ff 1px,transparent 1px)',backgroundSize:'60px 60px'}} />
      <div className="absolute top-0 left-0 right-0 flex items-center justify-between px-8 py-4 z-20">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-jarvis-glow animate-pulse" />
          <span className="glow-text text-sm font-mono tracking-widest">JARVIS v1.0 — AI OS</span>
        </div>
        <ScreenCapture />
      </div>
      <AgentStatus agents={agents} lastGoal={lastGoal} />
      <JarvisOrb thinking={thinking} onActivate={()=>setChatOpen(true)} projects={agents} />
      <GoalInput onSubmit={handleGoal} thinking={thinking} />
      <ChatPanel open={chatOpen} onClose={()=>setChatOpen(false)} lastGoal={lastGoal} />
    </div>
  )
}
