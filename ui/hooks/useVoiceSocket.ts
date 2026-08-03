'use client'
import { useCallback, useEffect, useRef, useState } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const WS_URL = API.replace(/^http/, 'ws') + '/voice/ws'

// Exponential backoff: 1s, 2s, 4s, 8s, 16s, capped at 30s. A cold-start
// disconnect (Render spinning the backend down/up) previously had no retry at
// all — the socket would just die silently. This reconnects automatically
// instead, up to MAX_ATTEMPTS, and exposes `status` so the UI can show it.
const BACKOFF_SCHEDULE_MS = [1000, 2000, 4000, 8000, 16000, 30000]
const MAX_ATTEMPTS = 8

export type VoiceSocketStatus = 'idle' | 'connecting' | 'open' | 'reconnecting' | 'failed'

/**
 * Reconnecting WebSocket client for /voice/ws with exponential-backoff retry.
 * Not yet wired into the mic button (current voice flow uses the REST
 * /voice/transcribe endpoint) — this is a ready-to-use client for switching
 * to streaming voice, built to the same cold-start-resilience standard as
 * the rest of the app.
 */
export function useVoiceSocket(onMessage: (data: any) => void) {
  const [status, setStatus] = useState<VoiceSocketStatus>('idle')
  const wsRef = useRef<WebSocket | null>(null)
  const attemptRef = useRef(0)
  const closedIntentionallyRef = useRef(false)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const connect = useCallback(() => {
    if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current)
    closedIntentionallyRef.current = false
    setStatus(attemptRef.current === 0 ? 'connecting' : 'reconnecting')

    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      attemptRef.current = 0
      setStatus('open')
    }
    ws.onmessage = (evt) => {
      try { onMessage(JSON.parse(evt.data)) } catch { /* ignore malformed frame */ }
    }
    ws.onclose = () => {
      if (closedIntentionallyRef.current) { setStatus('idle'); return }
      if (attemptRef.current >= MAX_ATTEMPTS) { setStatus('failed'); return }
      const delay = BACKOFF_SCHEDULE_MS[Math.min(attemptRef.current, BACKOFF_SCHEDULE_MS.length - 1)]
      attemptRef.current += 1
      setStatus('reconnecting')
      reconnectTimerRef.current = setTimeout(connect, delay)
    }
    ws.onerror = () => { ws.close() }
  }, [onMessage])

  const send = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data))
      return true
    }
    return false
  }, [])

  const disconnect = useCallback(() => {
    closedIntentionallyRef.current = true
    if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current)
    wsRef.current?.close()
  }, [])

  useEffect(() => () => disconnect(), [disconnect])

  return { connect, disconnect, send, status }
}

export default useVoiceSocket
