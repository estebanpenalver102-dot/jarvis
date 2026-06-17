'use client'
import { useEffect, useRef } from 'react'

interface Node { x: number; y: number; z: number; vx: number; vy: number; vz: number }

function project(x: number, y: number, z: number, cx: number, cy: number): [number, number, number] {
  const fov = 400
  const scale = fov / (fov + z)
  return [cx + x * scale, cy + y * scale, scale]
}

export default function JarvisOrb({ size = 420, active = false }: { size?: number; active?: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')!
    const cx = size / 2, cy = size / 2
    const R = size * 0.38
    const NODE_COUNT = 80

    // Generate nodes on sphere surface
    const nodes: Node[] = Array.from({ length: NODE_COUNT }, () => {
      const theta = Math.random() * Math.PI * 2
      const phi = Math.acos(2 * Math.random() - 1)
      return {
        x: R * Math.sin(phi) * Math.cos(theta),
        y: R * Math.sin(phi) * Math.sin(theta),
        z: R * Math.cos(phi),
        vx: (Math.random() - 0.5) * 0.003,
        vy: (Math.random() - 0.5) * 0.003,
        vz: (Math.random() - 0.5) * 0.003,
      }
    })

    let angle = 0
    let frame = 0
    let raf: number

    const draw = () => {
      frame++
      angle += active ? 0.006 : 0.003
      canvas.width = size
      canvas.height = size

      // Background glow
      const bg = ctx.createRadialGradient(cx, cy, 0, cx, cy, size * 0.5)
      bg.addColorStop(0, 'rgba(255, 140, 20, 0.08)')
      bg.addColorStop(0.5, 'rgba(180, 80, 10, 0.03)')
      bg.addColorStop(1, 'rgba(0,0,0,0)')
      ctx.fillStyle = bg
      ctx.fillRect(0, 0, size, size)

      // Rotate nodes
      const cos = Math.cos(angle), sin = Math.sin(angle)
      const projected = nodes.map(n => {
        const rx = n.x * cos - n.z * sin
        const rz = n.x * sin + n.z * cos
        return project(rx, n.y, rz, cx, cy)
      })

      // Draw connections
      for (let i = 0; i < NODE_COUNT; i++) {
        for (let j = i + 1; j < NODE_COUNT; j++) {
          const [x1, y1, s1] = projected[i]
          const [x2, y2, s2] = projected[j]
          const dist = Math.hypot(x1 - x2, y1 - y2)
          if (dist < R * 0.55) {
            const avgScale = (s1 + s2) / 2
            const alpha = (1 - dist / (R * 0.55)) * avgScale * 0.55
            ctx.beginPath()
            ctx.moveTo(x1, y1)
            ctx.lineTo(x2, y2)
            ctx.strokeStyle = `rgba(255, ${130 + Math.floor(avgScale * 60)}, ${Math.floor(avgScale * 30)}, ${alpha})`
            ctx.lineWidth = avgScale * 0.6
            ctx.stroke()
          }
        }
      }

      // Draw nodes
      projected.forEach(([px, py, sc]) => {
        const r = sc * 2.5
        const grd = ctx.createRadialGradient(px, py, 0, px, py, r * 3)
        grd.addColorStop(0, `rgba(255, 200, 80, ${sc * 0.9})`)
        grd.addColorStop(1, 'rgba(255, 120, 20, 0)')
        ctx.beginPath()
        ctx.arc(px, py, r * 3, 0, Math.PI * 2)
        ctx.fillStyle = grd
        ctx.fill()
        ctx.beginPath()
        ctx.arc(px, py, r, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(255, 220, 120, ${sc})`
        ctx.fill()
      })

      // Core glow
      const pulse = 0.85 + Math.sin(frame * 0.04) * 0.15
      const core = ctx.createRadialGradient(cx, cy, 0, cx, cy, R * 0.35 * pulse)
      core.addColorStop(0, `rgba(255, 200, 80, ${active ? 0.5 : 0.3})`)
      core.addColorStop(0.4, `rgba(255, 120, 30, ${active ? 0.15 : 0.08})`)
      core.addColorStop(1, 'rgba(255, 80, 0, 0)')
      ctx.beginPath()
      ctx.arc(cx, cy, R * 0.35 * pulse, 0, Math.PI * 2)
      ctx.fillStyle = core
      ctx.fill()

      // Outer ring
      ctx.beginPath()
      ctx.arc(cx, cy, R * 1.02, 0, Math.PI * 2)
      ctx.strokeStyle = `rgba(255, 140, 40, ${0.06 + Math.sin(frame * 0.03) * 0.02})`
      ctx.lineWidth = 1
      ctx.stroke()

      raf = requestAnimationFrame(draw)
    }

    draw()
    return () => cancelAnimationFrame(raf)
  }, [size, active])

  return (
    <canvas
      ref={canvasRef}
      width={size}
      height={size}
      style={{ display: 'block' }}
    />
  )
}
