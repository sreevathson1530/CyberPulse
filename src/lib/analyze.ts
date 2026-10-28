import { buildIncidents, type CorrelatedIncident } from './correlate'
import { buildActions, buildStory } from './explain'
import { ORG } from './org'
import { evaluateRules } from './rules'
import type { Alert, ResponseAction, Story, TelemetryEvent } from './types'

export interface Analysis {
  alerts: Alert[]
  incidents: CorrelatedIncident[]
  incident: CorrelatedIncident | null
  story: Story | null
  actions: ResponseAction[]
}

export function analyze(events: TelemetryEvent[]): Analysis {
  const alerts = evaluateRules(events, ORG)
  const incidents = buildIncidents(alerts, ORG.officeIps, ORG.sharedDevices)
  const incident = incidents[0] ?? null
  return {
    alerts,
    incidents,
    incident,
    story: incident ? buildStory(incident) : null,
    actions: incident ? buildActions(incident) : [],
  }
}
