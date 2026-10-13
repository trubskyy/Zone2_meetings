import { useState } from 'react'
import { api } from '../api'
import type { User } from '../types'
import { ZONE_LABEL } from '../zones'

type NumField = 'birth_year' | 'resting_hr' | 'max_hr' | 'zone2_low' | 'zone2_high'

const FIELDS: { key: NumField; label: string; hint?: string }[] = [
  { key: 'birth_year', label: 'Birth year', hint: 'Used to estimate max HR if you leave it empty' },
  { key: 'resting_hr', label: 'Resting HR' },
  { key: 'max_hr', label: 'Max HR' },
  { key: 'zone2_low', label: 'Zone 2 from', hint: 'From a lab or field test. Overrides the estimate.' },
  { key: 'zone2_high', label: 'Zone 2 to' },
]

export default function Profile({ user, onSaved }: { user: User; onSaved: (u: User) => void }) {
  const [form, setForm] = useState<Record<NumField, string>>(() =>
    Object.fromEntries(FIELDS.map((f) => [f.key, user[f.key]?.toString() ?? ''])) as Record<NumField, string>,
  )
  const [shareBpm, setShareBpm] = useState(user.share_bpm)
  const [status, setStatus] = useState<string | null>(null)

  const save = async (e: React.FormEvent) => {
    e.preventDefault()
    const patch: Partial<User> = { share_bpm: shareBpm }
    for (const f of FIELDS) patch[f.key] = form[f.key] ? Number(form[f.key]) : null
    try {
      onSaved(await api.updateMe(patch))
      setStatus('Saved')
    } catch (err) {
      setStatus((err as Error).message)
    }
  }

  return (
    <form className="stack" onSubmit={save}>
      <h2>Your zones</h2>
      <table className="zones">
        <tbody>
          {user.zones.zones.map((z) => (
            <tr key={z.zone} className={`zone-${z.zone}`}>
              <td>{ZONE_LABEL[z.zone]}</td>
              <td>{z.low}–{z.high} bpm</td>
            </tr>
          ))}
        </tbody>
      </table>
      {user.zones.estimated && (
        <p className="muted small">
          These are estimates. Add your resting and max heart rate, or tested Zone 2 numbers, to personalise them.
        </p>
      )}

      <div className="grid2">
        {FIELDS.map((f) => (
          <label key={f.key}>
            {f.label}
            <input type="number" inputMode="numeric" value={form[f.key]}
              onChange={(e) => setForm({ ...form, [f.key]: e.target.value })} />
            {f.hint && <span className="muted small">{f.hint}</span>}
          </label>
        ))}
      </div>

      <label className="check">
        <input type="checkbox" checked={shareBpm} onChange={(e) => setShareBpm(e.target.checked)} />
        Show my exact heart rate to others in a session (otherwise they only see my zone)
      </label>

      {status && <p className="small">{status}</p>}
      <button className="primary">Save</button>
      <p className="muted small">
        Zone 2 Meeting isn't a medical device. Check with a doctor before starting exercise if you have heart
        conditions or symptoms.
      </p>
    </form>
  )
}
