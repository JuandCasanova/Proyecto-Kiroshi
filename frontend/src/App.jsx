import { useState, useEffect, useRef, useCallback } from 'react'
import StatusBar from './components/StatusBar.jsx'
import ScanOverlay from './components/ScanOverlay.jsx'
import './App.css'

const WS_URL = 'ws://localhost:8000/ws/detect'

function App() {
  const [connected, setConnected] = useState(false)
  const [detections, setDetections] = useState([])
  const [frame, setFrame] = useState(null)
  const [fps, setFps] = useState(0)
  const [scanMode, setScanMode] = useState(false)
  const [voiceActive, setVoiceActive] = useState(false)
  const wsRef = useRef(null)
  const reconnectTimer = useRef(null)

  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current)
      reconnectTimer.current = null
    }

    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      setFrame(null)
      console.log('Conectado al servidor Kiroshi')
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setFrame(`data:image/jpeg;base64,${data.frame}`)
        setDetections(data.detections)
        setFps(data.fps)
      } catch (e) {
        console.error('Error parseando frame:', e)
      }
    }

    ws.onclose = () => {
      setConnected(false)
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
      reconnectTimer.current = setTimeout(connectWebSocket, 2000)
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [])

  useEffect(() => {
    connectWebSocket()
    return () => {
      if (wsRef.current) wsRef.current.close()
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
    }
  }, [connectWebSocket])

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Tab') {
        e.preventDefault()
        setScanMode(prev => !prev)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <div className="kiroshi-container">
      <div className="video-layer">
        {frame && <img src={frame} alt="camera" className="camera-feed" />}
        {!frame && (
          <div className="no-signal">
            <div className="glitch-text" data-text="SIN SEÑAL">SIN SEÑAL</div>
          </div>
        )}
      </div>

      <canvas
        className="hud-layer"
        ref={useCallback((canvas) => {
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
          const draw = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height)

            if (scanMode) {
              drawScanWave(ctx, canvas.width, canvas.height)
            }

            drawCrosshair(ctx, canvas.width / 2, canvas.height / 2)
            drawCompass(ctx, canvas.width, canvas.height)

            const scaleX = canvas.width / 640
            const scaleY = canvas.height / 480

            detections.forEach((det) => {
              drawDetection(ctx, det, scaleX, scaleY)
            })

            drawSystemMetrics(ctx, canvas.width, canvas.height, fps, detections.length)

            animFrame = requestAnimationFrame(draw)
          }
          draw()

          return () => {
            cancelAnimationFrame(animFrame)
            window.removeEventListener('resize', resize)
          }
        }, [detections, fps, scanMode])}
      />

      <ScanOverlay active={scanMode} />
      <StatusBar connected={connected} fps={fps} scanMode={scanMode} />
    </div>
  )
}

function drawCrosshair(ctx, cx, cy) {
  ctx.strokeStyle = '#ff2a2a'
  ctx.lineWidth = 1.5
  ctx.shadowColor = '#ff2a2a'
  ctx.shadowBlur = 8

  const size = 30
  const gap = 8

  ctx.beginPath()
  ctx.moveTo(cx - size, cy)
  ctx.lineTo(cx - gap, cy)
  ctx.moveTo(cx + gap, cy)
  ctx.lineTo(cx + size, cy)
  ctx.moveTo(cx, cy - size)
  ctx.lineTo(cx, cy - gap)
  ctx.moveTo(cx, cy + gap)
  ctx.lineTo(cx, cy + size)
  ctx.stroke()

  ctx.beginPath()
  ctx.arc(cx, cy, 2, 0, Math.PI * 2)
  ctx.fillStyle = '#ff2a2a'
  ctx.fill()

  ctx.shadowBlur = 0
}

function drawDetection(ctx, det, scaleX, scaleY) {
  const { bbox, class: cls, confidence, id } = det
  const x1 = bbox.x1 * scaleX
  const y1 = bbox.y1 * scaleY
  const x2 = bbox.x2 * scaleX
  const y2 = bbox.y2 * scaleY

  const colors = {
    person: '#ff2a2a',
    car: '#ff8c00',
    dog: '#00ff88',
    bottle: '#00bfff',
    'cell phone': '#bf00ff',
  }

  const color = colors[cls] || '#ff2a2a'

  ctx.strokeStyle = color
  ctx.lineWidth = 2
  ctx.shadowColor = color
  ctx.shadowBlur = 10

  const cornerLen = 20

  ctx.beginPath()
  ctx.moveTo(x1, y1 + cornerLen)
  ctx.lineTo(x1, y1)
  ctx.lineTo(x1 + cornerLen, y1)
  ctx.stroke()

  ctx.beginPath()
  ctx.moveTo(x2 - cornerLen, y1)
  ctx.lineTo(x2, y1)
  ctx.lineTo(x2, y1 + cornerLen)
  ctx.stroke()

  ctx.beginPath()
  ctx.moveTo(x2, y2 - cornerLen)
  ctx.lineTo(x2, y2)
  ctx.lineTo(x2 - cornerLen, y2)
  ctx.stroke()

  ctx.beginPath()
  ctx.moveTo(x1 + cornerLen, y2)
  ctx.lineTo(x1, y2)
  ctx.lineTo(x1, y2 - cornerLen)
  ctx.stroke()

  ctx.shadowBlur = 0

  const labelY = y1 - 8
  ctx.font = '600 14px "Orbitron", sans-serif'
  ctx.fillStyle = color
  ctx.fillText(`[${id}] ${cls.toUpperCase()}`, x1, labelY)

  ctx.font = '11px "Share Tech Mono", monospace'
  ctx.fillStyle = '#ffffff'
  ctx.fillText(`${(confidence * 100).toFixed(1)}%`, x1, labelY - 16)

  const barWidth = (x2 - x1) * confidence
  ctx.fillStyle = `${color}44`
  ctx.fillRect(x1, y2 + 4, x2 - x1, 3)
  ctx.fillStyle = color
  ctx.fillRect(x1, y2 + 4, barWidth, 3)

  const cx = (x1 + x2) / 2
  const cy = (y1 + y2) / 2
  ctx.strokeStyle = `${color}66`
  ctx.lineWidth = 0.5
  ctx.setLineDash([4, 4])
  ctx.beginPath()
  ctx.moveTo(cx, cy)
  ctx.lineTo(window.innerWidth / 2, window.innerHeight / 2)
  ctx.stroke()
  ctx.setLineDash([])
}

function drawCompass(ctx, w, h) {
  const cx = w / 2
  const y = 50

  ctx.font = '10px "Share Tech Mono", monospace'
  ctx.fillStyle = '#ff2a2a88'
  ctx.textAlign = 'center'
  ctx.fillText('N', cx, y)
  ctx.fillText('W', cx - 80, y + 5)
  ctx.fillText('E', cx + 80, y + 5)
  ctx.fillText('S', cx, y + 15)

  ctx.strokeStyle = '#ff2a2a44'
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(cx - 100, y + 3)
  ctx.lineTo(cx + 100, y + 3)
  ctx.stroke()

  ctx.fillStyle = '#ff2a2a'
  ctx.beginPath()
  ctx.moveTo(cx - 3, y - 8)
  ctx.lineTo(cx + 3, y - 8)
  ctx.lineTo(cx, y - 14)
  ctx.closePath()
  ctx.fill()

  ctx.textAlign = 'start'
}

function drawScanWave(ctx, w, h) {
  const t = (Date.now() % 3000) / 3000
  const maxRadius = Math.sqrt(w * w + h * h) / 2
  const radius = t * maxRadius

  ctx.strokeStyle = `rgba(255, 42, 42, ${0.6 * (1 - t)})`
  ctx.lineWidth = 3
  ctx.beginPath()
  ctx.arc(w / 2, h / 2, radius, 0, Math.PI * 2)
  ctx.stroke()

  ctx.strokeStyle = `rgba(255, 42, 42, ${0.3 * (1 - t)})`
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.arc(w / 2, h / 2, radius * 0.8, 0, Math.PI * 2)
  ctx.stroke()
}

function drawSystemMetrics(ctx, w, h, fps, objCount) {
  ctx.font = '11px "Share Tech Mono", monospace'
  ctx.fillStyle = '#ff2a2a88'
  ctx.textAlign = 'left'

  const metrics = [
    `FPS: ${fps}`,
    `OBJ: ${objCount}/5`,
    `MODEL: YOLOv8-N`,
    `GPU: CUDA`,
  ]

  metrics.forEach((m, i) => {
    ctx.fillText(m, 20, h - 20 - (metrics.length - 1 - i) * 18)
  })

  ctx.textAlign = 'right'
  ctx.fillText('KIROSHI OPTICS v1.0', w - 20, h - 20)
  ctx.textAlign = 'start'
}

export default App
