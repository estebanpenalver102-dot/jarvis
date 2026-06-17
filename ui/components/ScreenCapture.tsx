'use client'
import { useState, useRef } from 'react'
import { Monitor, MonitorOff } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

export default function ScreenCapture() {
  const [active, setActive] = useState(false)
  const [note, setNote] = useState('')
  const streamRef = useRef<MediaStream|null>(null)
  const wsRef = useRef<WebSocket|null>(null)
  const intRef = useRef<any>(null)
  const API = (process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000').replace('http','ws')

  const start = async () => {
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({video:true})
      streamRef.current = stream
      const video = document.createElement('video'); video.srcObject=stream; await video.play()
      const canvas = document.createElement('canvas')
      const ws = new WebSocket(`${API}/screen/ws`)
      wsRef.current = ws
      ws.onmessage = e => setNote(JSON.parse(e.data).analysis||'')
      ws.onopen = () => {
        setActive(true)
        intRef.current = setInterval(() => {
          if(!video.videoWidth) return
          canvas.width=Math.min(video.videoWidth,1280); canvas.height=Math.min(video.videoHeight,720)
          canvas.getContext('2d')!.drawImage(video,0,0,canvas.width,canvas.height)
          const b64=canvas.toDataURL('image/png').split(',')[1]
          if(ws.readyState===1) ws.send(JSON.stringify({screenshot_b64:b64,question:'What do you see and what should I do?'}))
        }, 5000)
      }
      stream.getVideoTracks()[0].onended = stop
    } catch { setActive(false) }
  }

  const stop = () => {
    clearInterval(intRef.current); wsRef.current?.close()
    streamRef.current?.getTracks().forEach(t=>t.stop())
    setActive(false); setNote('')
  }

  return (
    <div className="relative">
      <button onClick={active?stop:start}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${active?'bg-red-500/20 border border-red-400/40 text-red-300':'glass text-white/50 hover:text-white'}`}>
        {active?<><MonitorOff size={12}/> STOP CONTROL</>:<><Monitor size={12}/> GIVE JARVIS CONTROL</>}
      </button>
      <AnimatePresence>
        {note&&active&&(
          <motion.div className="absolute right-0 top-10 glass rounded-xl p-3 w-72 z-50 text-xs text-blue-100"
            initial={{opacity:0,y:-5}} animate={{opacity:1,y:0}} exit={{opacity:0}}>
            <div className="glow-text text-xs font-mono mb-1">JARVIS SEES:</div>
            {note}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
