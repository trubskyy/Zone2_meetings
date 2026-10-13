import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { inTelegram, telegramBotUsername } from '../telegram'
import type { User } from '../types'

const DEV_LOGIN = import.meta.env.VITE_DEV_LOGIN === 'true'

declare global {
  interface Window {
    onTelegramAuth?: (user: Record<string, unknown>) => void
  }
}

/** Standalone sign-in: Telegram Login Widget (same identity as the Mini App) + optional dev login. */
export default function Login({ onLogin, error }: { onLogin: (u: User) => void; error: string | null }) {
  const widget = useRef<HTMLDivElement>(null)
  const [name, setName] = useState('')
  const [failure, setFailure] = useState<string | null>(null)
  const bot = telegramBotUsername()

  useEffect(() => {
    if (!bot || !widget.current || inTelegram()) return
    window.onTelegramAuth = (data) => {
      api.loginTelegramWidget(data).then(onLogin, (e: Error) => setFailure(e.message))
    }
    const s = document.createElement('script')
    s.src = 'https://telegram.org/js/telegram-widget.js?22'
    s.async = true
    s.dataset.telegramLogin = bot
    s.dataset.size = 'large'
    s.dataset.onauth = 'onTelegramAuth(user)'
    s.dataset.requestAccess = 'write'
    widget.current.replaceChildren(s)
    return () => {
      delete window.onTelegramAuth
    }
  }, [bot, onLogin])

  const devLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      onLogin(await api.loginDev(name.trim()))
    } catch (err) {
      setFailure((err as Error).message)
    }
  }

  return (
    <main className="center stack">
      <h1>Zone 2 Club</h1>
      <p className="muted">Talk while you move. Take meetings at a conversational pace.</p>
      {(error || failure) && <p className="error">{error || failure}</p>}
      {bot ? <div ref={widget} /> : !DEV_LOGIN && <p className="muted">Open this app from Telegram to sign in.</p>}
      {DEV_LOGIN && (
        <form className="card stack" onSubmit={devLogin}>
          <label>
            Dev login name
            <input value={name} onChange={(e) => setName(e.target.value)} required maxLength={64} />
          </label>
          <button className="primary" disabled={!name.trim()}>
            Continue
          </button>
        </form>
      )}
    </main>
  )
}
