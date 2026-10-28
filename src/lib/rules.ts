import { MINUTE } from './format'
import { ORG, person, type OrgProfile } from './org'
import type { Alert, Severity, Stage, TelemetryEvent } from './types'

export interface RuleDef {
  id: string
  name: string
  detects: string
  severity: Severity
  stage: Stage
  mitre: string
  tactic: string
}

export const RULES: RuleDef[] = [
  {
    id: 'spray',
    name: 'Password spray',
    detects: 'Many accounts tried from one address',
    severity: 'medium',
    stage: 'Credential access',
    mitre: 'T1110.003',
    tactic: 'Credential Access',
  },
  {
    id: 'new-country',
    name: 'New country sign-in',
    detects: 'A country this account never used',
    severity: 'high',
    stage: 'Initial access',
    mitre: 'T1078',
    tactic: 'Initial Access',
  },
  {
    id: 'new-device',
    name: 'New device sign-in',
    detects: 'A device this account never used',
    severity: 'medium',
    stage: 'Initial access',
    mitre: 'T1078',
    tactic: 'Initial Access',
  },
  {
    id: 'mfa-fatigue',
    name: 'MFA fatigue',
    detects: 'Repeated push denials, then one approval',
    severity: 'high',
    stage: 'Credential access',
    mitre: 'T1621',
    tactic: 'Credential Access',
  },
  {
    id: 'oauth-grant',
    name: 'Risky app consent',
    detects: 'A new app granted mail access',
    severity: 'high',
    stage: 'Persistence',
    mitre: 'T1528',
    tactic: 'Persistence',
  },
  {
    id: 'forwarding',
    name: 'Hidden mail forwarding',
    detects: 'Inbox silently copying mail outside',
    severity: 'critical',
    stage: 'Collection',
    mitre: 'T1114.003',
    tactic: 'Collection',
  },
  {
    id: 'priv-esc',
    name: 'Admin rights granted',
    detects: 'A normal account made an admin',
    severity: 'critical',
    stage: 'Privilege escalation',
    mitre: 'T1098.003',
    tactic: 'Privilege Escalation',
  },
  {
    id: 'mass-download',
    name: 'Mass file download',
    detects: 'Downloads far above the account norm',
    severity: 'high',
    stage: 'Collection',
    mitre: 'T1039',
    tactic: 'Collection',
  },
  {
    id: 'external-share',
    name: 'File shared to free mail',
    detects: 'A company file sent to personal mail',
    severity: 'high',
    stage: 'Exfiltration',
    mitre: 'T1567.002',
    tactic: 'Exfiltration',
  },
  {
    id: 'canary',
    name: 'Ransomware marker',
    detects: 'Backups deleted or files mass renamed',
    severity: 'critical',
    stage: 'Impact',
    mitre: 'T1486',
    tactic: 'Impact',
  },
]

const RULE_BY_ID = new Map(RULES.map((r) => [r.id, r]))

function baseAlert(
  ruleId: string,
  evidence: TelemetryEvent[],
  fields: {
    user: string
    users: string[]
    ip: string
    device: string
    metric: string
    detail: string
    subject?: string
    baseline?: string
  },
): Alert {
  const rule = RULE_BY_ID.get(ruleId)!
  const ts = evidence.reduce((max, e) => Math.max(max, e.ts), evidence[0].ts)
  return {
    id: `${ruleId}:${evidence[0].id}`,
    ruleId,
    ruleName: rule.name,
    severity: rule.severity,
    stage: rule.stage,
    ts,
    evidenceIds: evidence.map((e) => e.id),
    mitre: rule.mitre,
    ...fields,
  }
}

function uniqueUsers(events: TelemetryEvent[]): string[] {
  return [...new Set(events.map((e) => e.user))]
}

function passwordSpray(events: TelemetryEvent[]): Alert[] {
  const fails = events.filter((e) => e.kind === 'auth.failure')
  const byIp = new Map<string, TelemetryEvent[]>()
  for (const e of fails) {
    const list = byIp.get(e.ip) ?? []
    list.push(e)
    byIp.set(e.ip, list)
  }

  const out: Alert[] = []
  for (const [ip, list] of byIp) {
    let window = list.filter((e) => e.ts - list[0].ts <= 10 * MINUTE)
    if (window.length < 5 || uniqueUsers(window).length < 3) {
      let left = 0
      window = []
      for (let right = 0; right < list.length; right++) {
        while (list[right].ts - list[left].ts > 10 * MINUTE) left++
        const candidate = list.slice(left, right + 1)
        if (candidate.length >= 5 && uniqueUsers(candidate).length >= 3) {
          window = candidate
          break
        }
      }
    }
    if (window.length === 0) continue

    const users = uniqueUsers(window)
    const place = window[0].city ?? 'an unknown location'
    out.push(
      baseAlert('spray', window, {
        user: users[0],
        users,
        ip,
        device:
          window.find((e) => e.device && e.device !== 'unregistered-device')?.device ?? 'unregistered-device',
        subject: ip,
        metric: `${window.length} failed sign-ins, ${users.length} accounts, ${Math.round(
          (window[window.length - 1].ts - window[0].ts) / MINUTE,
        )} min`,
        detail: `${ip} (${place}) tried a short list of common passwords against ${users.length} different accounts. One address, many names, which is what a spray looks like.`,
        baseline: 'Normal: at most 2 failed sign-ins a day, each from an office address.',
      }),
    )
  }
  return out
}

function newCountry(events: TelemetryEvent[]): Alert[] {
  const out: Alert[] = []
  const seen = new Set<string>()
  for (const e of events) {
    if (e.kind !== 'auth.success' || !e.country) continue
    const p = person(e.user)
    if (p.countries.includes(e.country)) continue
    const key = `${e.user}:${e.country}`
    if (seen.has(key)) continue
    seen.add(key)
    const place = e.city && e.city !== e.country ? `${e.city}, ${e.country}` : e.country
    out.push(
      baseAlert('new-country', [e], {
        user: e.user,
        users: [e.user],
        ip: e.ip,
        device: e.device,
        subject: place,
        metric: `${place} is not a country this account has used`,
        detail: `${p.name} signed in from ${place}. This account has only ever signed in from ${p.countries.join(
          ' and ',
        )}.`,
        baseline: `Normal: ${p.countries.join(', ')} only.`,
      }),
    )
  }
  return out
}

function newDevice(events: TelemetryEvent[], org: OrgProfile): Alert[] {
  const out: Alert[] = []
  const seen = new Set<string>()
  for (const e of events) {
    if (e.kind !== 'auth.success') continue
    if (org.sharedDevices.includes(e.device)) continue
    const p = person(e.user)
    if (p.devices.includes(e.device)) continue
    const key = `${e.user}:${e.device}`
    if (seen.has(key)) continue
    seen.add(key)
    out.push(
      baseAlert('new-device', [e], {
        user: e.user,
        users: [e.user],
        ip: e.ip,
        device: e.device,
        subject: e.device,
        metric: `Unrecognised device ${e.device}`,
        detail: `${p.name} signed in from ${e.device}, a device that has never been used on this account.`,
        baseline: `Normal devices: ${p.devices.join(', ')}.`,
      }),
    )
  }
  return out
}

function mfaFatigue(events: TelemetryEvent[]): Alert[] {
  const out: Alert[] = []
  const byUser = new Map<string, TelemetryEvent[]>()
  for (const e of events) {
    if (e.kind !== 'auth.mfa_denied' && e.kind !== 'auth.mfa_success') continue
    const list = byUser.get(e.user) ?? []
    list.push(e)
    byUser.set(e.user, list)
  }

  for (const [user, list] of byUser) {
    for (let i = 0; i < list.length; i++) {
      const e = list[i]
      if (e.kind !== 'auth.mfa_success') continue
      const denials = list.filter(
        (d) => d.kind === 'auth.mfa_denied' && d.ts <= e.ts && e.ts - d.ts <= 15 * MINUTE,
      )
      if (denials.length < 3) continue
      out.push(
        baseAlert('mfa-fatigue', [...denials, e], {
          user,
          users: [user],
          ip: e.ip,
          device: e.device,
          subject: personNameSafe(user),
          metric: `${denials.length} push denials, then one approval`,
          detail: `${personNameSafe(user)} denied ${denials.length} sign-in prompts in a row, then one was approved. Someone was knocking until it worked.`,
          baseline: 'Normal: MFA prompts are approved on the first try.',
        }),
      )
      break
    }
  }
  return out
}

function personNameSafe(id: string): string {
  return person(id).name
}

function forwarding(events: TelemetryEvent[], org: OrgProfile): Alert[] {
  const out: Alert[] = []
  for (const e of events) {
    if (e.kind !== 'mail.forwarding_created' || !e.target) continue
    const domain = e.target.split('@')[1] ?? ''
    if (org.allowedForwardDomains.includes(domain)) continue
    out.push(
      baseAlert('forwarding', [e], {
        user: e.user,
        users: [e.user],
        ip: e.ip,
        device: e.device,
        subject: e.target,
        metric: `Mail copied to ${domain}`,
        detail: `${personNameSafe(e.user)}'s mailbox now forwards a copy of incoming mail to ${e.target}, a domain the company does not own. This rule never sends a confirmation to the user.`,
        baseline: 'Normal: no forwarding rules are active on this mailbox.',
      }),
    )
  }
  return out
}

function oauthGrant(events: TelemetryEvent[], org: OrgProfile): Alert[] {
  const out: Alert[] = []
  for (const e of events) {
    if (e.kind !== 'oauth.grant' || !e.app) continue
    if (org.approvedApps.includes(e.app)) continue
    const scopes = e.scopes ?? []
    if (!scopes.includes('mail.read') && !scopes.includes('offline_access')) continue
    out.push(
      baseAlert('oauth-grant', [e], {
        user: e.user,
        users: [e.user],
        ip: e.ip,
        device: e.device,
        subject: e.app,
        metric: `${e.app} granted ${scopes.join(', ')}`,
        detail: `${personNameSafe(e.user)} approved "${e.app}", which asked to read mail and stay signed in. A password reset does not remove this kind of access.`,
        baseline: 'Normal: three approved apps are connected to this tenant.',
      }),
    )
  }
  return out
}

function massDownload(events: TelemetryEvent[]): Alert[] {
  const out: Alert[] = []
  const byUser = new Map<string, TelemetryEvent[]>()
  for (const e of events) {
    if (e.kind !== 'file.download') continue
    const list = byUser.get(e.user) ?? []
    list.push(e)
    byUser.set(e.user, list)
  }

  for (const [user, list] of byUser) {
    const p = person(user)
    const threshold = Math.max(20, p.filesPerTenMinutes * 4)
    const ordered = [...list].sort((a, b) => a.ts - b.ts)
    let window: TelemetryEvent[] = []
    let left = 0
    for (let right = 0; right < ordered.length; right++) {
      while (ordered[right].ts - ordered[left].ts > 10 * MINUTE) left++
      const candidate = ordered.slice(left, right + 1)
      const total = candidate.reduce((s, e) => s + (e.count ?? 1), 0)
      if (total >= threshold) {
        window = candidate
        break
      }
    }
    if (window.length === 0) continue

    const total = window.reduce((s, e) => s + (e.count ?? 1), 0)
    const first = window[0]
    out.push(
      baseAlert('mass-download', window, {
        user,
        users: [user],
        ip: first.ip,
        device: first.device,
        subject: personNameSafe(user),
        metric: `${total} files downloaded in ${Math.max(
          1,
          Math.round((window[window.length - 1].ts - first.ts) / MINUTE),
        )} min`,
        detail: `${personNameSafe(user)} downloaded ${total} files in one sitting. The account normally opens about ${p.filesPerTenMinutes} files every ten minutes.`,
        baseline: `Normal: about ${p.filesPerTenMinutes} files every 10 minutes.`,
      }),
    )
  }
  return out
}

function privEsc(events: TelemetryEvent[], org: OrgProfile): Alert[] {
  const out: Alert[] = []
  for (const e of events) {
    if (e.kind !== 'admin.role_assigned' || !e.target) continue
    if (!org.adminRoles.includes(e.target)) continue
    const p = person(e.user)
    if (p.admin) continue
    out.push(
      baseAlert('priv-esc', [e], {
        user: e.user,
        users: [e.user],
        ip: e.ip,
        device: e.device,
        subject: e.target,
        metric: `${e.target} added to a ${p.dept} account`,
        detail: `${p.name} was given ${e.target}, the highest role in the tenant. This account had no admin rights a minute ago.`,
        baseline: 'Normal: two accounts hold admin roles, both in IT and leadership.',
      }),
    )
  }
  return out
}

function externalShare(events: TelemetryEvent[], org: OrgProfile): Alert[] {
  const out: Alert[] = []
  for (const e of events) {
    if (e.kind !== 'file.share_external' || !e.target) continue
    const domain = e.target.split('@')[1]?.split('/')[0] ?? ''
    if (!org.personalMailDomains.includes(domain)) continue
    out.push(
      baseAlert('external-share', [e], {
        user: e.user,
        users: [e.user],
        ip: e.ip,
        device: e.device,
        subject: e.target,
        metric: `Shared to ${domain}`,
        detail: `A company file was shared with ${e.target}. Free mail domains are how stolen documents usually leave a small business.`,
        baseline: 'Normal: shares go to customer domains, never personal mail.',
      }),
    )
  }
  return out
}

function canary(events: TelemetryEvent[]): Alert[] {
  const out: Alert[] = []
  for (const e of events) {
    if (e.kind === 'endpoint.shadow_copy_deleted') {
      out.push(
        baseAlert('canary', [e], {
          user: e.user,
          users: [e.user],
          ip: e.ip,
          device: e.device,
          subject: e.device,
          metric: 'Volume shadow copies deleted',
          detail: `Backup snapshots were deleted on ${e.device}. Ransomware removes recovery points before it encrypts, so this is often the last quiet warning.`,
          baseline: 'Normal: backup snapshots are never deleted during business hours.',
        }),
      )
    }
    if (e.kind === 'endpoint.mass_rename' && (e.count ?? 0) >= 40) {
      out.push(
        baseAlert('canary', [e], {
          user: e.user,
          users: [e.user],
          ip: e.ip,
          device: e.device,
          subject: e.device,
          metric: `${e.count} files renamed with one extension`,
          detail: `${e.count} files on ${e.device} were renamed to a single extension in under a minute. That is encryption, not editing.`,
          baseline: 'Normal: file renames stay under 20 a day.',
        }),
      )
    }
  }
  return out
}

export function evaluateRules(events: TelemetryEvent[], org: OrgProfile = ORG): Alert[] {
  return [
    ...passwordSpray(events),
    ...newCountry(events),
    ...newDevice(events, org),
    ...mfaFatigue(events),
    ...forwarding(events, org),
    ...oauthGrant(events, org),
    ...massDownload(events),
    ...privEsc(events, org),
    ...externalShare(events, org),
    ...canary(events),
  ].sort((a, b) => a.ts - b.ts)
}
