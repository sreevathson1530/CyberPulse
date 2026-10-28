export const MINUTE = 60_000
export const HOUR = 60 * MINUTE

export function fmtTime(ts: number): string {
  const d = new Date(ts)
  return `${String(d.getUTCHours()).padStart(2, '0')}:${String(d.getUTCMinutes()).padStart(2, '0')}`
}

export function fmtClock(ts: number): string {
  const d = new Date(ts)
  return `${String(d.getUTCHours()).padStart(2, '0')}:${String(d.getUTCMinutes()).padStart(2, '0')}:${String(
    d.getUTCSeconds(),
  ).padStart(2, '0')}`
}

export function fmtDate(ts: number): string {
  return new Date(ts).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  })
}

export function fmtGap(ms: number): string {
  const mins = Math.round(ms / MINUTE)
  if (mins < 60) return `${mins} min`
  const h = Math.floor(mins / 60)
  const m = mins % 60
  return m === 0 ? `${h} h` : `${h} h ${m} m`
}

export function fmtNumber(n: number): string {
  return n.toLocaleString('en-IN')
}
