import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { connectHeartRate, heartRateSupported, type HeartRateConnection } from '../heartRate'
import { haptic, openLink } from '../telegram'
import type { Effort, Meeting, User } from '../types'
import type { View } from '../App'
import { useLive } from '../useLive'
import { EFFORTS, ZONE_COACHING, ZONE_LABEL } from '../zones'

export default function LiveMeeting({ id, me, go }: { id: number; me: User; go: (v: View) => void }) {
  const [meeting, setMeeting] = useState<Meeting | null>(null)
  const { participants, status, setBpm, setEffort } = useLive(id)
  const [effort, setEffortState] = useState<Effort | null>(null)
  const [sensor, setSensor] = useState<HeartRateConnection | null>(null)
  const [myBpm, setMyBpm] = useState<number | null>(null)
  const [sensorError, setSensorError] = useState<string | null>(null)
  const sensorRef = useRef<HeartRateConnection | null>(null)

  useEffect(() => {
    api.meeting(id).then(setMeeting, () => go({ name: 'list' }))
  }, [id, go])

  useEffect(() => () => sensorRef.current?.disconnect(), [])

  const self = participants.find((p) => p.user_id === me.id)
  const others = participants.filter((p) => p.user_id !== me.id)

  // A gentle buzz when you leave Zone 2, so you can course-correct without looking.
  const lastZone = useRef<number | null>(null)
  useEffect(() => {
    const z = self?.zone ?? null
    if (lastZone.current === 2 && z !== null && z !== 2) haptic('medium')
    lastZone.current = z
  }, [self?.zone])

  const connectSensor = async () => {
    setSensorError(null)
    try {
      const conn = await connectHeartRate(
        (bpm) => {
          setMyBpm(bpm)
          setBpm(bpm)
        },
        () => {
          setSensor(null)
          sensorRef.current = null
        },
      )
      sensorRef.current = conn
      setSensor(conn)
    } catch (e) {
      setSensorError((e as Error).message)
    }
  }

  const pickEffort = (level: Effort) => {
    haptic()
    setEffortState(level)
    setEffort(level)
  }

  const leave = () => {
    sensorRef.current?.disconnect()
    go({ name: 'summary', id })
  }

  if (!meeting) return <p className="muted">Loading…</p>

  return (
    <section className="stack">
      <div className="row">
        <h2>{meeting.title}</h2>
        <span className={`pill ${status === 'live' ? 'live' : ''}`}>{status}</span>
      </div>
      {meeting.topic && <p className="small">{meeting.topic}</p>}

      {meeting.voice_link ? (
        <button className="primary" onClick={() => openLink(meeting.voice_link!)}>
          🎧 Open voice chat
        </button>
      ) : (
        <p className="muted small">The host hasn't added a voice chat link yet.</p>
      )}

      <div className={`card me zone-${self?.zone ?? 0}`}>
        <div className="big">{self?.zone ? ZONE_LABEL[self.zone] : 'Waiting for a reading'}</div>
        {myBpm !== null && sensor && <div className="muted">{myBpm} bpm</div>}
        <div className="small">
          {self?.zone ? ZONE_COACHING[self.zone] : 'Connect a heart-rate sensor or tap how talking feels.'}
        </div>
        {self?.zone2_pct != null && <div className="muted small">{self.zone2_pct}% of this session in Zone 2</div>}
      </div>

      <div className="stack-sm">
        <strong className="small">Heart rate</strong>
        {sensor ? (
          <div className="row">
            <span className="small">✅ {sensor.deviceName}</span>
            <button onClick={() => { sensor.disconnect(); setSensor(null); sensorRef.current = null }}>Disconnect</button>
          </div>
        ) : heartRateSupported() ? (
          <button onClick={() => void connectSensor()}>Connect Bluetooth heart-rate sensor</button>
        ) : (
          <p className="muted small">
            Bluetooth sensors aren't available in this browser (for example on iPhone). Use the talk test below.
          </p>
        )}
        {sensorError && <p className="error small">{sensorError}</p>}
      </div>

      <div className="stack-sm">
        <strong className="small">Talk test: how does talking feel right now?</strong>
        <div className="grid2">
          {EFFORTS.map((e) => (
            <button key={e.level} className={effort === e.level ? 'active' : ''} onClick={() => pickEffort(e.level)}>
              {e.label}
              <span className="muted small block">{e.hint}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="stack-sm">
        <strong className="small">Riding with you ({others.length})</strong>
        <div className="grid2">
          {others.map((p) => (
            <div key={p.user_id} className={`card tile zone-${p.zone ?? 0}`}>
              <div>{p.name}</div>
              <div className="small">
                {p.zone ? ZONE_LABEL[p.zone] : '—'}
                {p.bpm !== null && ` · ${p.bpm} bpm`}
              </div>
            </div>
          ))}
        </div>
      </div>

      <button onClick={leave}>Finish session</button>
    </section>
  )
}
