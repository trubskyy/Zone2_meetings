import { useCallback, useEffect, useRef, useState } from 'react'
import { liveUrl } from './api'
import type { Effort, LiveParticipant } from './types'

const SEND_EVERY_MS = 3000
const HR_STALE_MS = 10000
// Close codes from backend/app/api/live.py — don't retry these.
const FATAL_CLOSE = new Set([4401, 4403])

type Status = 'connecting' | 'live' | 'reconnecting' | 'closed'

/**
 * Connects to a meeting's live room. Readings are re-sent every few seconds even when unchanged,
 * because the server credits time between readings (see backend/app/live.py).
 * A fresh sensor BPM wins over self-reported effort.
 */
export function useLive(meetingId: number) {
  const [participants, setParticipants] = useState<LiveParticipant[]>([])
  const [status, setStatus] = useState<Status>('connecting')
  const ws = useRef<WebSocket | null>(null)
  const reading = useRef<{ bpm: number | null; bpmAt: number; effort: Effort | null }>({
    bpm: null,
    bpmAt: 0,
    effort: null,
  })

  const sendCurrent = useCallback(() => {
    const socket = ws.current
    if (!socket || socket.readyState !== WebSocket.OPEN) return
    const r = reading.current
    if (r.bpm !== null && Date.now() - r.bpmAt < HR_STALE_MS) {
      socket.send(JSON.stringify({ type: 'hr', bpm: r.bpm }))
    } else if (r.effort) {
      socket.send(JSON.stringify({ type: 'effort', level: r.effort }))
    }
  }, [])

  useEffect(() => {
    let stopped = false
    let retry: number | undefined

    const open = () => {
      const socket = new WebSocket(liveUrl(meetingId))
      ws.current = socket
      socket.onopen = () => {
        setStatus('live')
        sendCurrent()
      }
      socket.onmessage = (e) => {
        const msg = JSON.parse(e.data)
        if (msg.type === 'state') setParticipants(msg.participants)
      }
      socket.onclose = (e) => {
        if (stopped || FATAL_CLOSE.has(e.code)) {
          setStatus('closed')
          return
        }
        setStatus('reconnecting')
        retry = window.setTimeout(open, 2000)
      }
    }
    open()
    const tick = window.setInterval(sendCurrent, SEND_EVERY_MS)

    return () => {
      stopped = true
      window.clearInterval(tick)
      window.clearTimeout(retry)
      ws.current?.close()
    }
  }, [meetingId, sendCurrent])

  const setBpm = useCallback((bpm: number) => {
    reading.current.bpm = bpm
    reading.current.bpmAt = Date.now()
  }, [])

  const setEffort = useCallback(
    (effort: Effort) => {
      reading.current.effort = effort
      reading.current.bpm = null // explicit self-report overrides a stale sensor
      sendCurrent()
    },
    [sendCurrent],
  )

  return { participants, status, setBpm, setEffort }
}
