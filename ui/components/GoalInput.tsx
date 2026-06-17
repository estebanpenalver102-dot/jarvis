'use client'
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Zap } from 'lucide-react'

const EXAMPLES = [
  "Research top car dealership competitors and summarize their pricing",
  "Find today's top AI news and save key insights to memory",
  "Create a follow-up email template for new car leads",
  "Analyze openroad-autos.com for SEO improvements",
]

export default function GoalInput({ onSubmit, thinking }: any) {
  const [goal, setGoal] = useState('')
  const [ex, setEx] = useState(0)

  return (
    <div className="absolute bottom-8 left-1/2 -translate-x-1/2 w-[580px] z-20">
      <motion.div className="glass rounded-2xl p-4" initial={{opacity:0,y:20}} animate={{opacity:1,y:0}}>
        <div className="flex items-center gap-2 mb-2.5">
          <Zap size={13} className="text-jarvis-glow"/>
          <span className="text-xs font-mono text-blue-300/50">GIVE JARVIS A GOAL — AGENTS AUTO-HIRED</span>
        </div>
        <div className="flex gap-2">
          <input className="flex-1 bg-transparent text-sm text-white placeholder-white/20 outline-none"
            placeholder={EXAMPLES[ex%EXAMPLES.length]} value={goal}
            onChange={e=>setGoal(e.target.value)}
            onKeyDown={e=>{
              if(e.key==='Enter'&&goal.trim()){onSubmit(goal.trim());setGoal('')}
              if(e.key==='Tab'){e.preventDefault();setEx(p=>p+1)}
            }} />
          <button onClick={()=>{if(goal.trim()&&!thinking){onSubmit(goal.trim());setGoal('')}}}
            disabled={thinking||!goal.trim()}
            className="px-5 py-1.5 rounded-xl text-xs font-mono font-bold tracking-wider disabled:opacity-30 transition-all"
            style={{background:'linear-gradient(135deg,#0060dd,#00d4ff)',color:'#000a1a'}}>
            {thinking?'WORKING…':'EXECUTE'}
          </button>
        </div>
        <p className="text-xs text-white/15 mt-2 font-mono">Tab = example goals · Enter = execute</p>
      </motion.div>
    </div>
  )
}
