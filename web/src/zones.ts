import type { Activity, Effort } from './types'

export const ZONE_LABEL: Record<number, string> = {
  1: 'Easy',
  2: 'Zone 2',
  3: 'Tempo',
  4: 'Hard',
  5: 'Max',
}

/** Coaching line shown to the rider for their own zone. */
export const ZONE_COACHING: Record<number, string> = {
  1: 'Nice and easy. Push a little if you want Zone 2.',
  2: 'Perfect. Keep talking at this pace.',
  3: 'A bit high. Ease off until full sentences feel easy.',
  4: 'Too hard for a meeting. Slow down.',
  5: 'Way over. Slow right down.',
}

export const EFFORTS: { level: Effort; label: string; hint: string }[] = [
  { level: 'easy', label: 'Easy', hint: 'I could sing' },
  { level: 'conversational', label: 'Talkable', hint: 'Full sentences, no singing' },
  { level: 'short_sentences', label: 'Short phrases', hint: 'Talking takes effort' },
  { level: 'breathless', label: 'Breathless', hint: "Can't really talk" },
]

export const ACTIVITY_LABEL: Record<Activity, string> = {
  bike: '🚴 Bike',
  treadmill: '🏃 Treadmill',
  walk: '🚶 Walk',
  run: '🏃 Run',
  any: '✨ Any',
}
