import { useEffect, useState } from 'react'
import { api } from '../api'
import { haptic } from '../telegram'
import type { Meeting } from '../types'
import type { View } from '../App'
import { ACTIVITY_LABEL } from '../zones'

const fmt = new Intl.DateTimeFormat(undefined, { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })

export function isLiveNow(m: Meeting, now = Date.now()): boolean {
  const start = Date.parse(m.starts_at)
  return now >= start - 10 * 60_000 && now <= start + m.duration_min * 60_000
}

export default function MeetingList({ go }: { go: (v: View) => void }) {
  const [mine, setMine] = useState(false)
  const [meetings, setMeetings] = useState<Meeting[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setMeetings(null)
    api.meetings(mine).then(setMeetings, (e: Error) => setError(e.message))
  }, [mine])

  const join = async (m: Meeting) => {
    haptic()
    const updated = await api.join(m.id)
    setMeetings((ms) => ms?.map((x) => (x.id === m.id ? updated : x)) ?? null)
  }

  return (
    <section className="stack">
      <div className="row">
        <div className="tabs">
          <button className={!mine ? 'active' : ''} onClick={() => setMine(false)}>
            Upcoming
          </button>
          <button className={mine ? 'active' : ''} onClick={() => setMine(true)}>
            Mine
          </button>
        </div>
        <button className="primary" onClick={() => go({ name: 'create' })}>
          + Host
        </button>
      </div>

      {error && <p className="error">{error}</p>}
      {meetings === null && !error && <p className="muted">Loading…</p>}
      {meetings?.length === 0 && (
        <p className="muted">No sessions yet. Host the first one: pick a topic and a time.</p>
      )}

      {meetings?.map((m) => (
        <article key={m.id} className="card stack-sm">
          <div className="row">
            <strong>{m.title}</strong>
            {isLiveNow(m) && <span className="pill live">Live</span>}
          </div>
          <div className="muted small">
            {fmt.format(new Date(m.starts_at))} · {m.duration_min} min · {ACTIVITY_LABEL[m.activity]} ·{' '}
            {m.attendee_count} going{m.visibility === 'private' ? ' · 🔒' : ''}
          </div>
          {m.topic && <p className="small">{m.topic}</p>}
          <div className="row">
            <span className="muted small">Host: {m.host.display_name}</span>
            {m.joined ? (
              <button className="primary" onClick={() => go({ name: 'live', id: m.id })}>
                {isLiveNow(m) ? 'Enter' : 'Open'}
              </button>
            ) : (
              <button onClick={() => void join(m)}>Join</button>
            )}
          </div>
        </article>
      ))}
    </section>
  )
}
