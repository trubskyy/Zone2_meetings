export type Activity = 'bike' | 'treadmill' | 'walk' | 'run' | 'any'
export type Visibility = 'public' | 'private'
export type Effort = 'easy' | 'conversational' | 'short_sentences' | 'breathless'

export interface ZoneBound {
  zone: number
  low: number
  high: number
}

export interface UserPublic {
  id: number
  display_name: string
  username: string | null
  photo_url: string | null
}

export interface User extends UserPublic {
  birth_year: number | null
  resting_hr: number | null
  max_hr: number | null
  zone2_low: number | null
  zone2_high: number | null
  share_bpm: boolean
  zones: { resting_hr: number; max_hr: number; estimated: boolean; zones: ZoneBound[] }
}

export interface Meeting {
  id: number
  title: string
  topic: string
  host: UserPublic
  starts_at: string
  duration_min: number
  activity: Activity
  visibility: Visibility
  voice_link: string | null
  attendee_count: number
  joined: boolean
  invite_code: string | null
}

export interface MeetingCreate {
  title: string
  topic: string
  starts_at: string
  duration_min: number
  activity: Activity
  visibility: Visibility
  voice_link: string | null
}

export interface Attendance {
  user: UserPublic
  joined_at: string
  left_at: string | null
  avg_hr: number | null
  tracked_seconds: number
  zone2_seconds: number
}

export interface MeetingSummary {
  meeting: Meeting
  attendees: Attendance[]
  total_zone2_minutes: number
}

export interface LiveParticipant {
  user_id: number
  name: string
  zone: number | null
  bpm: number | null
  source: 'hr' | 'effort' | null
  zone2_pct: number | null
}
