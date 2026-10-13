// Thin wrapper over the Telegram Mini App SDK (loaded in index.html).
// Every function is safe to call outside Telegram, where it falls back to plain web behaviour.
// SDK reference: https://core.telegram.org/bots/webapps

interface TelegramWebApp {
  initData: string
  initDataUnsafe: { start_param?: string }
  colorScheme: 'light' | 'dark'
  ready(): void
  expand(): void
  openLink(url: string): void
  openTelegramLink(url: string): void
  BackButton: { show(): void; hide(): void; onClick(cb: () => void): void; offClick(cb: () => void): void }
  HapticFeedback?: { impactOccurred(style: 'light' | 'medium' | 'heavy'): void }
}

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp }
  }
}

const webApp = (): TelegramWebApp | undefined => window.Telegram?.WebApp

/** True only when actually running inside Telegram (the SDK script alone isn't enough). */
export const inTelegram = (): boolean => Boolean(webApp()?.initData)

export const initData = (): string => webApp()?.initData ?? ''

export function initTelegram(): void {
  const tg = webApp()
  if (!inTelegram() || !tg) return
  tg.ready()
  tg.expand()
}

/** Deep-link payload: t.me/<bot>/<app>?startapp=... in Telegram, or ?start=... on the web. */
export function startParam(): string | null {
  return webApp()?.initDataUnsafe.start_param ?? new URLSearchParams(location.search).get('start')
}

export function openLink(url: string): void {
  const tg = webApp()
  if (inTelegram() && tg) {
    if (/^https:\/\/t\.me\//.test(url)) tg.openTelegramLink(url)
    else tg.openLink(url)
  } else {
    window.open(url, '_blank', 'noopener')
  }
}

export function haptic(style: 'light' | 'medium' | 'heavy' = 'light'): void {
  webApp()?.HapticFeedback?.impactOccurred(style)
}

/** Shows Telegram's native back button while `onBack` is set; no-op on the web. Returns a cleanup. */
export function setBackButton(onBack: (() => void) | null): () => void {
  const tg = webApp()
  if (!inTelegram() || !tg) return () => {}
  if (!onBack) {
    tg.BackButton.hide()
    return () => {}
  }
  tg.BackButton.onClick(onBack)
  tg.BackButton.show()
  return () => {
    tg.BackButton.offClick(onBack)
    tg.BackButton.hide()
  }
}

const BOT = import.meta.env.VITE_TELEGRAM_BOT_USERNAME as string | undefined
const APP = import.meta.env.VITE_TELEGRAM_APP_SHORT_NAME as string | undefined

export const telegramBotUsername = (): string | undefined => BOT || undefined

/** Invite links for a meeting: a Telegram deep link (if configured) and a plain web link. */
export function inviteLinks(payload: string): { telegram?: string; web: string } {
  const web = `${location.origin}/?start=${encodeURIComponent(payload)}`
  return BOT && APP ? { telegram: `https://t.me/${BOT}/${APP}?startapp=${payload}`, web } : { web }
}
