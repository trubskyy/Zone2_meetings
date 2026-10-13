import type { Meeting, MeetingCreate, MeetingSummary, User } from './types'

const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? ''
const TOKEN_KEY = 'z2.token'

let token: string | null = null
try {
  token = sessionStorage.getItem(TOKEN_KEY)
} catch {
  /* storage unavailable (private mode / some web views) — stay in memory */
}

export const getToken = () => token

export function setToken(t: string | null): void {
  token = t
  try {
    if (t) sessionStorage.setItem(TOKEN_KEY, t)
    else sessionStorage.removeItem(TOKEN_KEY)
  } catch {
    /* ignore */
  }
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (token) headers.Authorization = `Bearer ${token}`
  const res = await fetch(`${BASE}/api${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (res.status === 401) setToken(null)
  if (!res.ok) {
    let detail = res.statusText
    try {
      const data = await res.json()
      detail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)
    } catch {
      /* non-JSON error */
    }
    throw new ApiError(res.status, detail)
  }
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T)
}

interface TokenOut {
  token: string
  user: User
}

async function authenticate(path: string, body: unknown): Promise<User> {
  const out = await request<TokenOut>('POST', path, body)
  setToken(out.token)
  return out.user
}

export const api = {
  loginTelegramWebApp: (init_data: string) => authenticate('/auth/telegram-webapp', { init_data }),
  loginTelegramWidget: (data: Record<string, unknown>) => authenticate('/auth/telegram-login', data),
  loginDev: (name: string) => authenticate('/auth/dev', { name }),

  me: () => request<User>('GET', '/me'),
  updateMe: (patch: Partial<User>) => request<User>('PATCH', '/me', patch),

  meetings: (mine = false) => request<Meeting[]>('GET', `/meetings${mine ? '?mine=true' : ''}`),
  meeting: (id: number, inviteCode?: string) =>
    request<Meeting>('GET', `/meetings/${id}${inviteCode ? `?invite_code=${encodeURIComponent(inviteCode)}` : ''}`),
  createMeeting: (body: MeetingCreate) => request<Meeting>('POST', '/meetings', body),
  join: (id: number, invite_code?: string) => request<Meeting>('POST', `/meetings/${id}/join`, { invite_code }),
  leave: (id: number) => request<void>('POST', `/meetings/${id}/leave`),
  summary: (id: number) => request<MeetingSummary>('GET', `/meetings/${id}/summary`),
}

export function liveUrl(meetingId: number): string {
  const origin = BASE || location.origin
  const wsOrigin = origin.replace(/^http/, 'ws')
  return `${wsOrigin}/api/meetings/${meetingId}/live?token=${encodeURIComponent(token ?? '')}`
}
