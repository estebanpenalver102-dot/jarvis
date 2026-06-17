'use client'
import { motion } from 'framer-motion'

const C: Record<string,string> = {research:'#00d4ff',sales:'#ff6b35',coding:'#a855f7',cto:'#22c55e',operations:'#f59e0b',browser:'#ec4899',general:'#64748b'}

export default function AgentStatus({ agents, lastGoal }: any) {
  const hired = lastGoal?.agents_hired || []
  return (
    <div className="absolute left-8 top-1/2 -translate-y-1/2 space-y-2 z-10">
      <div className="text-xs font-mono text-white/25 mb-3 tracking-widest">AGENTS</div>
      {agents.map((a: any) => {
        const active = hired.includes(a.name); const c = C[a.name]||'#00d4ff'
        return (
          <motion.div key={a.name} className="flex items-center gap-2" animate={{opacity:active?1:.3}}>
            <motion.div className="w-2 h-2 rounded-full" style={{background:c}}
              animate={{scale:active?[1,1.6,1]:1,boxShadow:active?`0 0 8px ${c}`:'none'}}
              transition={{duration:.6,repeat:active?Infinity:0}} />
            <span className="text-xs font-mono" style={{color:active?c:'#fff3'}}>{a.name}</span>
            {active&&<span className="text-xs font-mono text-white/25">● active</span>}
          </motion.div>
        )
      })}
    </div>
  )
}
