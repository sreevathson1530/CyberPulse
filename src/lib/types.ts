export type Severity = 'low' | 'medium' | 'high' | 'critical'

export const SEVERITY_POINTS: Record<Severity, number> = {
  low: 5,
  medium: 15,
  high: 25,
  critical: 40,
}

export const SEVERITY_ORDER: Record<Severity, number> = {
  low: 0,
  medium: 1,
  high: 2,
  critical: 3,
}

export type Stage =
  | 'Initial access'
  | 'Credential access'
  | 'Persistence'
  | 'Privilege escalation'
  | 'Collection'
  | 'Exfiltration'
  | 'Impact'

export const STAGE_ORDER: Stage[] = [
  'Initial access',
  'Credential access',
  'Persistence',
  'Privilege escalation',
  'Collection',
  'Exfiltration',
  'Impact',
]

export type EventKind =
  | 'auth.success'
  | 'auth.failure'
  | 'auth.mfa_denied'
  | 'auth.mfa_success'
  | 'mail.forwarding_created'
  | 'mail.sent_external'
  | 'mail.reply_to_changed'
  | 'oauth.grant'
  | 'file.download'
  | 'file.share_external'
  | 'admin.role_assigned'
  | 'endpoint.shadow_copy_deleted'
  | 'endpoint.mass_rename'
  | 'endpoint.process'

export interface TelemetryEvent {
  id: string
  ts: number
  kind: EventKind
  user: string
  ip: string
  device: string
  country?: string
  city?: string
  outcome?: 'success' | 'failure'
  target?: string
  app?: string
  scopes?: string[]
  count?: number
  bytes?: number
  note?: string
}

export interface Alert {
  id: string
  ruleId: string
  ruleName: string
  severity: Severity
  stage: Stage
  ts: number
  user: string
  users: string[]
  ip: string
  device: string
  evidenceIds: string[]
  metric: string
  detail: string
  subject?: string
  baseline?: string
  mitre: string
}

export interface LinkRef {
  toId: string
  reason: string
}

export interface Incident {
  id: string
  alerts: Alert[]
  score: number
  basePoints: number
  stageBonus: number
  stages: Stage[]
  startedAt: number
  updatedAt: number
  users: string[]
  ips: string[]
  devices: string[]
  links: Record<string, LinkRef[]>
  title: string
}

export type Band = 'clear' | 'watch' | 'suspicious' | 'likely'

export interface ResponseAction {
  id: string
  label: string
  why: string
  effect: string
  urgency: 'now' | 'next'
  target: string
}

export interface Story {
  title: string
  dek: string
  beats: { ts: number; text: string }[]
  why: string
  next: string
  confidence: string
}
