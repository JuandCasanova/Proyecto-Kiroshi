import { useState, useEffect } from 'react'
import './StatusBar.css'

function StatusBar({ connected, fps, scanMode }) {
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const formatTime = (d) => {
    return d.toLocaleTimeString('es-ES', { hour12: false })
  }

  return (
    <div className="status-bar">
      <div className="status-left">
        <span className={`status-dot ${connected ? 'online' : 'offline'}`} />
        <span className="status-text">{connected ? 'LINK ACTIVO' : 'DESCONECTADO'}</span>
      </div>

      <div className="status-center">
        <span className="kiroshi-logo">KIROSHI</span>
        <span className="kiroshi-version">OPTICS v1.0</span>
      </div>

      <div className="status-right">
        <span className="status-item">{fps} FPS</span>
        <span className={`status-mode ${scanMode ? 'scanning' : ''}`}>
          {scanMode ? 'MOD: ESCANEO' : 'MOD: NORMAL'}
        </span>
        <span className="status-time">{formatTime(time)}</span>
      </div>
    </div>
  )
}

export default StatusBar
