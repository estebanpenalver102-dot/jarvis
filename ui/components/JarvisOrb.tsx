'use client'
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const COLORS: Record<string,string> = {
  research:'#00d4ff',sales:'#ff6b35',coding:'#a855f7',
  cto:'#22c55e',operations:'#f59e0b',browser:'#ec4899',general:'#64748b'
}

export default function JarvisOrb({ thinking, onActivate, projects }: any) {
  const [hovered, setHovered] = useState(false)
  const [tip, setTip] = useState<any>(null)
  const [drag, setDrag] = useState<any>(null)
  const [drop, setDrop] = useState<any>(null)

  return (
    <div className="relative flex items-center justify-center" style={{width:580,height:580}}>
      {[300,370,440].map((sz,i)=>(
        <motion.div key={sz} className="orb-ring absolute"
          style={{width:sz,height:sz,top:'50%',left:'50%',transform:'translate(-50%,-50%)'}}
          animate={{rotate:i%2===0?360:-360,opacity:hovered?0.5:0.15}}
          transition={{duration:9+i*4,repeat:Infinity,ease:'linear'}} />
      ))}
      <AnimatePresence>
        {hovered && projects.map((p:any,i:number)=>{
          const a=(i/projects.length)*2*Math.PI-Math.PI/2
          const x=Math.cos(a)*210, y=Math.sin(a)*210
          const c=COLORS[p.name]||'#00d4ff'
          return (
            <motion.div key={p.name} className="absolute flex flex-col items-center cursor-pointer z-10"
              style={{left:'50%',top:'50%'}}
              initial={{opacity:0,x,y,scale:0}} animate={{opacity:1,x,y,scale:1}} exit={{opacity:0,scale:0}}
              transition={{delay:i*0.06,type:'spring',stiffness:220}}
              draggable onDragStart={()=>setDrag(p)} onDragEnd={()=>{setDrag(null);setDrop(null)}}
              onDragOver={e=>{e.preventDefault();setDrop(p)}}
              onDrop={()=>{ if(drag&&drop&&drag.name!==drop.name) console.log(`${drag.name} → ${drop.name}`) }}
              onClick={()=>setTip(tip?.name===p.name?null:p)}
              whileHover={{scale:1.25}}>
              <div className="w-12 h-12 rounded-full flex items-center justify-center text-xs font-bold uppercase"
                   style={{background:`${c}22`,border:`2px solid ${c}`,color:c,
                           boxShadow:drop?.name===p.name?`0 0 20px ${c}`:'none'}}>
                {p.name.slice(0,2)}
              </div>
              <span className="text-xs mt-1 font-mono" style={{color:c,opacity:.75}}>{p.name}</span>
            </motion.div>
          )
        })}
      </AnimatePresence>
      <motion.div className="relative z-10 rounded-full flex items-center justify-center cursor-pointer select-none"
        style={{width:150,height:150,background:'radial-gradient(circle at 35% 35%,#0060dd,#000d2a)',border:'2px solid rgba(0,212,255,0.5)'}}
        animate={{boxShadow:thinking
          ?['0 0 40px #00d4ff,0 0 80px #0080ff','0 0 80px #00d4ff,0 0 180px #0080ff']
          :['0 0 20px #00d4ff44','0 0 50px #00d4ff99'],
          scale:hovered?1.07:1}}
        transition={{duration:thinking?.35:2,repeat:Infinity,repeatType:'reverse'}}
        onHoverStart={()=>setHovered(true)} onHoverEnd={()=>setHovered(false)}
        onClick={onActivate}>
        <div className="text-center">
          <div className="glow-text text-lg font-bold tracking-widest">J.A.R.V.I.S</div>
          <div className="text-xs text-blue-300/50 mt-1 font-mono">
            {thinking?'THINKING..':hovered?'TAP TO CHAT':'AI OS'}
          </div>
          {thinking&&<motion.div className="mt-2 flex gap-1 justify-center">
            {[0,1,2].map(i=>(
              <motion.div key={i} className="w-1.5 h-1.5 rounded-full bg-jarvis-glow"
                animate={{scaleY:[1,2.2,1]}} transition={{duration:.55,delay:i*.15,repeat:Infinity}} />
            ))}
          </motion.div>}
        </div>
      </motion.div>
      <AnimatePresence>
        {tip&&(
          <motion.div className="absolute glass rounded-xl p-2.5 z-20 max-w-xs"
            style={{bottom:16,left:'50%',transform:'translateX(-50%)'}}
            initial={{opacity:0,y:8}} animate={{opacity:1,y:0}} exit={{opacity:0}}>
            <p className="text-xs font-mono" style={{color:COLORS[tip.name]||'#00d4ff'}}>
              [{tip.name.toUpperCase()}] {tip.specialty}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
