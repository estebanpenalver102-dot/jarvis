'use client'
import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Send, Mic, MicOff } from 'lucide-react'

interface Msg { role:'user'|'assistant'; content:string; agent?:string }

export default function ChatPanel({ open, onClose, lastGoal }: any) {
  const [msgs, setMsgs] = useState<Msg[]>([{role:'assistant',content:'Online. Give me a goal, ask a question, or use voice mode.'}])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [recording, setRecording] = useState(false)
  const [sid] = useState(()=>crypto.randomUUID())
  const endRef = useRef<HTMLDivElement>(null)
  const mrRef = useRef<MediaRecorder|null>(null)
  const chunks = useRef<BlobPart[]>([])
  const API = process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000'

  useEffect(()=>{ endRef.current?.scrollIntoView({behavior:'smooth'}) },[msgs,loading])
  useEffect(()=>{
    if(lastGoal?.synthesis&&open)
      setMsgs(p=>[...p,{role:'assistant',agent:'goal-engine',
        content:`**Goal complete** — agents hired: ${lastGoal.agents_hired?.join(', ')}\n\n${lastGoal.synthesis}`}])
  },[lastGoal])

  const send = async () => {
    if(!input.trim()||loading) return
    const t=input.trim(); setInput('')
    setMsgs(p=>[...p,{role:'user',content:t}]); setLoading(true)
    try {
      const r=await fetch(`${API}/chat`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:t,session_id:sid})})
      const d=await r.json()
      setMsgs(p=>[...p,{role:'assistant',content:d.response,agent:d.agent_used}])
    } catch { setMsgs(p=>[...p,{role:'assistant',content:'Connection error — is JARVIS running?'}]) }
    finally { setLoading(false) }
  }

  const toggleVoice = async () => {
    if(recording){ mrRef.current?.stop(); setRecording(false); return }
    try {
      const stream=await navigator.mediaDevices.getUserMedia({audio:true})
      const mr=new MediaRecorder(stream); chunks.current=[]
      mr.ondataavailable=e=>chunks.current.push(e.data)
      mr.onstop=async()=>{
        const blob=new Blob(chunks.current,{type:'audio/webm'})
        const b64=btoa(String.fromCharCode(...new Uint8Array(await blob.arrayBuffer())))
        setLoading(true)
        try {
          const r=await fetch(`${API}/voice/turn`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({audio_b64:b64,mime_type:'audio/webm'})})
          const d=await r.json()
          if(d.transcript) setMsgs(p=>[...p,{role:'user',content:`🎤 ${d.transcript}`}])
          if(d.response_text){
            setMsgs(p=>[...p,{role:'assistant',content:d.response_text}])
            if(d.audio_b64) new Audio(`data:audio/mpeg;base64,${d.audio_b64}`).play()
          }
        } finally { setLoading(false) }
      }
      mr.start(); mrRef.current=mr; setRecording(true)
    } catch { alert('Microphone access required') }
  }

  return (
    <AnimatePresence>
      {open&&(
        <motion.div className="fixed right-0 top-0 h-full w-[420px] glass z-30 flex flex-col"
          initial={{x:420}} animate={{x:0}} exit={{x:420}}
          transition={{type:'spring',stiffness:300,damping:30}}>
          <div className="flex items-center justify-between p-4 border-b border-white/10">
            <div>
              <div className="glow-text font-bold text-sm tracking-widest">JARVIS CHAT</div>
              <div className="text-xs text-blue-300/40 font-mono">5-tier memory · multi-agent</div>
            </div>
            <button onClick={onClose} className="text-white/40 hover:text-white transition-colors"><X size={18}/></button>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {msgs.map((m,i)=>(
              <div key={i} className={`flex ${m.role==='user'?'justify-end':'justify-start'}`}>
                <div className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap ${
                  m.role==='user'?'bg-blue-600/30 border border-blue-500/30 text-blue-50':'glass text-blue-100'}`}>
                  {m.agent&&<span className="text-xs opacity-40 font-mono block mb-1">[{m.agent}]</span>}
                  {m.content}
                </div>
              </div>
            ))}
            {loading&&<div className="flex gap-1 p-2">
              {[0,1,2].map(i=>(
                <motion.div key={i} className="w-2 h-2 rounded-full bg-jarvis-glow"
                  animate={{opacity:[.3,1,.3]}} transition={{duration:1,delay:i*.2,repeat:Infinity}} />
              ))}
            </div>}
            <div ref={endRef}/>
          </div>
          <div className="p-4 border-t border-white/10">
            <div className="flex gap-2">
              <input className="flex-1 glass rounded-xl px-4 py-2.5 text-sm text-white placeholder-white/30 outline-none"
                placeholder="Message JARVIS..." value={input}
                onChange={e=>setInput(e.target.value)} onKeyDown={e=>e.key==='Enter'&&!e.shiftKey&&send()} />
              <button onClick={toggleVoice}
                className={`w-10 h-10 rounded-xl flex items-center justify-center ${recording?'bg-red-500/30 border border-red-400':'glass'}`}>
                {recording?<MicOff size={16} className="text-red-400"/>:<Mic size={16} className="text-white/60"/>}
              </button>
              <button onClick={send} disabled={!input.trim()||loading}
                className="w-10 h-10 rounded-xl glass flex items-center justify-center disabled:opacity-30">
                <Send size={16} className="text-jarvis-glow"/>
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
