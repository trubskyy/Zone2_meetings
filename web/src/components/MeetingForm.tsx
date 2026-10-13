import { useState } from 'react'
import { api } from '../api'
import { inviteLinks } from '../telegram'
import type { Activity, Meeting, Visibility } from '../types'
import type { View } from '../App'
import { ACTIVITY_LABEL } from '../zones'

/** Value for <input type="datetime-local"> in local time, rounded up to the next quarter hour. */
function defaultStart(): string {
  const d = new Date(Date.now() + 15 * 60_000)
  d.setMinutes(Math.ceil(d.getMinutes() / 15) * 15, 0, 0)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export default function MeetingForm({ go }: { go: (v: View) => void }) {
  const [title, setTitle] = useState('')
  const [topic, setTopic] = useState('')
  const [start, setStart] = useState(defaultStart)
  const [duration, setDuration] = useState(45)
  const [activity, setActivity] = useState<Activity>('bike')
  const [visibility, setVisibility] = useState<Visibility>('public')
  const [voiceLink, setVoiceLink] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [created, setCreated] = useState<Meeting | null>(null)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      const m = await api.createMeeting({
        title: title.trim(),
        topic: topic.trim(),
        starts_at: new Date(start).toISOString(),
        duration_min: duration,
        activity,
        visibility,
        voice_link: voiceLink.trim() || null,
      })
      if (m.visibility === 'private') setCreated(m)
      else go({ name: 'list' })
    } catch (err) {
      setError((err as Error).message)
    }
  }

  if (created) {
    const links = inviteLinks(`m${created.id}_${created.invite_code}`)
    return (
      <section className="stack">
        <h2>Private session created</h2>
        <p className="muted">Share one of these links. Only people with a link can join.</p>
        {links.telegram && <input readOnly value={links.telegram} onFocus={(e) => e.target.select()} />}
        <input readOnly value={links.web} onFocus={(e) => e.target.select()} />
        <button className="primary" onClick={() => go({ name: 'list' })}>
          Done
        </button>
      </section>
    )
  }

  return (
    <form className="stack" onSubmit={submit}>
      <h2>Host a session</h2>
      <label>
        Title
        <input value={title} onChange={(e) => setTitle(e.target.value)} required maxLength={140} placeholder="Founders ride" />
      </label>
      <label>
        Topic
        <textarea value={topic} onChange={(e) => setTopic(e.target.value)} maxLength={2000} rows={3}
          placeholder="What will you talk about? Add 2–3 prompt questions." />
      </label>
      <div className="grid2">
        <label>
          Starts
          <input type="datetime-local" value={start} onChange={(e) => setStart(e.target.value)} required />
        </label>
        <label>
          Minutes
          <input type="number" min={10} max={240} step={5} value={duration} onChange={(e) => setDuration(Number(e.target.value))} />
        </label>
        <label>
          Activity
          <select value={activity} onChange={(e) => setActivity(e.target.value as Activity)}>
            {Object.entries(ACTIVITY_LABEL).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
        </label>
        <label>
          Who can join
          <select value={visibility} onChange={(e) => setVisibility(e.target.value as Visibility)}>
            <option value="public">Anyone</option>
            <option value="private">Invite link only</option>
          </select>
        </label>
      </div>
      <label>
        Voice chat link
        <input type="url" value={voiceLink} onChange={(e) => setVoiceLink(e.target.value)}
          placeholder="https://t.me/yourgroup?videochat" />
        <span className="muted small">
          Start a voice chat in your Telegram group and paste its invite link. Audio runs in Telegram.
        </span>
      </label>
      {error && <p className="error">{error}</p>}
      <button className="primary" disabled={!title.trim()}>
        Create session
      </button>
    </form>
  )
}
