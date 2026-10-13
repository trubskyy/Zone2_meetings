import { useCallback, useEffect, useState } from 'react'
import { api, getToken } from './api'
import { initData, inTelegram, setBackButton, startParam } from './telegram'
import type { User } from './types'
import Login from './components/Login'
import MeetingList from './components/MeetingList'
import MeetingForm from './components/MeetingForm'
import LiveMeeting from './components/LiveMeeting'
import Summary from './components/Summary'
import Profile from './components/Profile'

export type View =
  | { name: 'list' }
  | { name: 'create' }
  | { name: 'profile' }
  | { name: 'live'; id: number }
  | { name: 'summary'; id: number }

/** Invite payload "m<id>" or "m<id>_<inviteCode>" (from t.me ?startapp= or web ?start=). */
function parseInvite(p: string | null): { id: number; code?: string } | null {
  const m = p?.match(/^m(\d+)(?:_(.+))?$/)
  return m ? { id: Number(m[1]), code: m[2] } : null
}

export default function App() {
  const [user, setUser] = useState<User | null>(null)
  const [booting, setBooting] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [view, setView] = useState<View>({ name: 'list' })

  const afterLogin = useCallback(async (u: User) => {
    setUser(u)
    const invite = parseInvite(startParam())
    if (invite) {
      try {
        await api.join(invite.id, invite.code)
        setView({ name: 'live', id: invite.id })
      } catch {
        setError('That invite link is invalid or has expired.')
      }
    }
  }, [])

  // Sign in automatically inside Telegram, or resume a stored session on the web.
  useEffect(() => {
    const boot = async () => {
      try {
        if (inTelegram()) await afterLogin(await api.loginTelegramWebApp(initData()))
        else if (getToken()) await afterLogin(await api.me())
      } catch (e) {
        if (inTelegram()) setError(`Sign-in failed: ${(e as Error).message}`)
      } finally {
        setBooting(false)
      }
    }
    void boot()
  }, [afterLogin])

  useEffect(() => setBackButton(view.name === 'list' ? null : () => setView({ name: 'list' })), [view])

  if (booting) return <main className="center muted">Loading…</main>
  if (!user) return <Login onLogin={afterLogin} error={error} />

  return (
    <main>
      <header className="topbar">
        <button className="link brand" onClick={() => setView({ name: 'list' })}>
          Zone 2 Club
        </button>
        <button className="link" onClick={() => setView({ name: 'profile' })}>
          {user.display_name}
        </button>
      </header>
      {error && <p className="error">{error}</p>}
      {view.name === 'list' && <MeetingList go={setView} />}
      {view.name === 'create' && <MeetingForm go={setView} />}
      {view.name === 'profile' && <Profile user={user} onSaved={setUser} />}
      {view.name === 'live' && <LiveMeeting id={view.id} me={user} go={setView} />}
      {view.name === 'summary' && <Summary id={view.id} me={user} go={setView} />}
    </main>
  )
}
