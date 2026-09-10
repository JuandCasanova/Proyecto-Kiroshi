import { useEffect, useRef } from 'react'
import './ScanOverlay.css'

function ScanOverlay({ active }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    if (!active) return

    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    canvas.width = window.innerWidth
    canvas.height = window.innerHeight

    const resize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    window.addEventListener('resize', resize)

    let animFrame
    const startTime = Date.now()

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      const elapsed = (Date.now() - startTime) / 1000

      ctx.strokeStyle = '#ff2a2a33'
      ctx.lineWidth = 1

      for (let i = 0; i < 20; i++) {
        const y = ((i * 30 + elapsed * 50) % canvas.height)
        ctx.beginPath()
        ctx.moveTo(0, y)
        ctx.lineTo(canvas.width, y)
        ctx.stroke()
      }

      const cx = canvas.width / 2
      const cy = canvas.height / 2
      const scanRadius = 150 + Math.sin(elapsed * 2) * 30

      ctx.strokeStyle = '#ff2a2a'
      ctx.lineWidth = 2
      ctx.setLineDash([10, 5])

      ctx.beginPath()
      ctx.arc(cx, cy, scanRadius, 0, Math.PI * 2)
      ctx.stroke()

      ctx.beginPath()
      ctx.arc(cx, cy, scanRadius * 0.6, 0, Math.PI * 2)
      ctx.stroke()

      ctx.setLineDash([])

      const angle = elapsed * 1.5
      ctx.strokeStyle = '#ff2a2a'
      ctx.lineWidth = 3
      ctx.beginPath()
      ctx.moveTo(cx, cy)
      ctx.lineTo(
        cx + Math.cos(angle) * scanRadius,
        cy + Math.sin(angle) * scanRadius
      )
      ctx.stroke()

      ctx.font = '12px "Orbitron", sans-serif'
      ctx.fillStyle = '#ff2a2a'
      ctx.fillText('ESCANEANDO...', 20, canvas.height / 2 - 180)

      animFrame = requestAnimationFrame(draw)
    }
    draw()

    return () => {
      cancelAnimationFrame(animFrame)
      window.removeEventListener('resize', resize)
    }
  }, [active])

  if (!active) return null

  return (
    <canvas ref={canvasRef} className="scan-overlay" />
  )
}

export default ScanOverlay
