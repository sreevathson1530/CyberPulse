import { personName } from './org'
import type { Alert, Band, Incident, LinkRef, Stage } from './types'
import { SEVERITY_POINTS, STAGE_ORDER } from './types'

const MINUTE_LOCAL = 60_000

export const BANDS: { id: Band; label: string; from: number; to: number; note: string }[] = [
  { id: 'clear', label: 'Clear', from: 0, to: 0, note: 'Nothing is connected' },
  { id: 'watch', label: 'Watch', from: 1, to: 39, note: 'One loose clue' },
  { id: 'suspicious', label: 'Suspicious', from: 40, to: 74, note: 'Clues are linking up' },
  { id: 'likely', label: 'Likely attack', from: 75, to: 100, note: 'Act now' },
]

export function bandOf(score: number): Band {
  if (score >= 75) return 'likely'
  if (score >= 40) return 'suspicious'
  if (score > 0) return 'watch'
  return 'clear'
}

export function bandLabel(score: number): string {
  return BANDS.find((b) => b.id === bandOf(score))?.label ?? 'Clear'
}

export interface ScoreRow {
  alertId: string
  label: string
  stage: Stage
  points: number
  running: number
}

export interface ScoreResult {
  score: number
  basePoints: number
  stageBonus: number
  stages: Stage[]
  rows: ScoreRow[]
  firstLikelyAt: number | null
}

export function scoreAlerts(alerts: Alert[]): ScoreResult {
  const sorted = [...alerts].sort((a, b) => a.ts - b.ts)
  let basePoints = 0
  let stages: Stage[] = []
  let firstLikelyAt: number | null = null
  const rows: ScoreRow[] = sorted.map((a) => {
    basePoints += SEVERITY_POINTS[a.severity]
    if (!stages.includes(a.stage)) stages = [...stages, a.stage]
    const bonus = Math.max(0, stages.length - 1) * 10
    const running = Math.min(100, basePoints + bonus)
    if (firstLikelyAt === null && running >= 75) firstLikelyAt = a.ts
    return {
      alertId: a.id,
      label: a.ruleName,
      stage: a.stage,
      points: SEVERITY_POINTS[a.severity],
      running,
    }
  })

  const stageBonus = Math.max(0, stages.length - 1) * 10
  return {
    score: Math.min(100, basePoints + stageBonus),
    basePoints,
    stageBonus,
    stages,
    rows,
    firstLikelyAt,
  }
}

const INCIDENT_TITLES: Record<Stage, string> = {
  'Initial access': 'An account has been entered',
  'Credential access': 'Credentials are being worked on',
  Persistence: 'A way back in has been built',
  'Privilege escalation': 'The account now holds company-wide control',
  Collection: 'Company files are being gathered',
  Exfiltration: 'Company data is leaving',
  Impact: 'Files are being encrypted',
}

export function incidentTitle(stages: Stage[]): string {
  let best = -1
  let stage: Stage = 'Initial access'
  for (const s of stages) {
    const idx = STAGE_ORDER.indexOf(s)
    if (idx > best) {
      best = idx
      stage = s
    }
  }
  return INCIDENT_TITLES[stage]
}

function hash(s: string): number {
  let h = 0
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 10000
  return h
}

function sharedReason(a: Alert, b: Alert, officeIps: string[], sharedDevices: string[]): string | null {
  const sharedUser = a.users.find((u) => b.users.includes(u))
  if (sharedUser) return `same account (${personName(sharedUser)})`

  if (a.ip === b.ip && !officeIps.includes(a.ip)) {
    return `same source IP ${a.ip}`
  }

  const ignoredDevice = (d: string) => sharedDevices.includes(d) || d === 'unregistered-device'
  if (a.device === b.device && !ignoredDevice(a.device)) {
    return `same device ${a.device}`
  }

  return null
}

export interface CorrelatedIncident extends Incident {
  scoreResult: ScoreResult
}

export function buildIncidents(
  alerts: Alert[],
  officeIps: string[] = [],
  sharedDevices: string[] = [],
): CorrelatedIncident[] {
  if (alerts.length === 0) return []
  const sorted = [...alerts].sort((a, b) => a.ts - b.ts)
  const parent = new Map<string, string>()
  for (const a of sorted) parent.set(a.id, a.id)

  const find = (x: string): string => {
    let root = x
    while (parent.get(root) !== root) root = parent.get(root)!
    let cur = x
    while (parent.get(cur) !== root) {
      const next = parent.get(cur)!
      parent.set(cur, root)
      cur = next
    }
    return root
  }
  const union = (a: string, b: string) => {
    const ra = find(a)
    const rb = find(b)
    if (ra !== rb) parent.set(rb, ra)
  }

  const links: Record<string, LinkRef[]> = {}

  for (let j = 0; j < sorted.length; j++) {
    for (let i = j - 1; i >= 0; i--) {
      const a = sorted[i]
      const b = sorted[j]
      if (b.ts - a.ts > 6 * 60 * MINUTE_LOCAL) continue
      const reason = sharedReason(a, b, officeIps, sharedDevices)
      if (!reason) continue
      union(a.id, b.id)
      const list = links[b.id] ?? []
      if (!list.some((l) => l.reason.startsWith(`${reason},`))) {
        const gap = Math.round((b.ts - a.ts) / MINUTE_LOCAL)
        list.push({
          toId: a.id,
          reason: `${reason}, ${gap === 0 ? 'same minute' : `${gap} min earlier`}`,
        })
      }
      links[b.id] = list
    }
  }

  const groups = new Map<string, Alert[]>()
  for (const a of sorted) {
    const root = find(a.id)
    const list = groups.get(root) ?? []
    list.push(a)
    groups.set(root, list)
  }

  const incidents: CorrelatedIncident[] = []
  for (const list of groups.values()) {
    const ordered = [...list].sort((a, b) => a.ts - b.ts)
    const scoreResult = scoreAlerts(ordered)
    const users = [...new Set(ordered.flatMap((a) => a.users))].filter(
      (u) => !u.startsWith('unregistered'),
    )
    const ips = [...new Set(ordered.map((a) => a.ip))].filter((ip) => !officeIps.includes(ip))
    const devices = [...new Set(ordered.map((a) => a.device))].filter(
      (d) => d !== 'unregistered-device' && !sharedDevices.includes(d),
    )

    const clusterLinks: Record<string, LinkRef[]> = {}
    for (const a of ordered) {
      if (links[a.id]) clusterLinks[a.id] = links[a.id]
    }

    incidents.push({
      id: `INC-${String(hash(ordered[0].id)).padStart(4, '0')}`,
      alerts: ordered,
      score: scoreResult.score,
      basePoints: scoreResult.basePoints,
      stageBonus: scoreResult.stageBonus,
      stages: scoreResult.stages,
      startedAt: ordered[0].ts,
      updatedAt: ordered[ordered.length - 1].ts,
      users,
      ips,
      devices,
      links: clusterLinks,
      title: incidentTitle(scoreResult.stages),
      scoreResult,
    })
  }

  return incidents.sort((a, b) => b.score - a.score || b.updatedAt - a.updatedAt)
}
