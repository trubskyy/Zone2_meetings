import { useEffect, useState } from 'react'
import { api } from '../api'
import type { MeetingSummary, User } from '../types'
import type { View } from '../App'

const mins = (s: number) => Math.round(s / 60)

export default function Summary({ id, me, go }: { id: number; me: User; go: (v: View) => void }) {
  const [summary, setSummary] = useState<MeetingSummary | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Give the server a moment to persist our live totals after the socket closes.
    const t = window.setTimeout(() => api.summary(id).then(setSummary, (e: Error) => setError(e.message)), 500)
    return () => window.clearTimeout(t)
  }, [id])

  if (error) return <p className="error">{error}</p>
  if (!summary) return <p className="muted">Saving your session…</p>

  const mine = summary.attendees.find((a) => a.user.id === me.id)
  const pct = mine && mine.tracked_seconds ? Math.round((100 * mine.zone2_seconds) / mine.tracked_seconds) : null

  return (
    <section className="stack">
      <h2>Nice work 👏</h2>
      <p className="muted">{summary.meeting.title}</p>
      {mine && (
        <div className="card zone-2 stack-sm">
          <div className="big">{mins(mine.zone2_seconds)} min in Zone 2</div>
          {pct !== null && <div className="small">{pct}% of your tracked time</div>}
          {mine.avg_hr !== null && <div className="small">Average heart rate: {Math.round(mine.avg_hr)} bpm</div>}
        </div>
      )}
      <p className="small">
        Together, {summary.attendees.length} {summary.attendees.length === 1 ? 'person' : 'people'} logged{' '}
        <strong>{Math.round(summary.total_zone2_minutes)} Zone 2 minutes</strong>.
      </p>
      <button className="primary" onClick={() => go({ name: 'list' })}>
        Back to sessions
      </button>
    </section>
  )
}
