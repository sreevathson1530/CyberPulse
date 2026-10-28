import type { CorrelatedIncident } from './correlate'
import { fmtTime } from './format'
import { personName } from './org'
import type { Alert, ResponseAction, Stage, Story } from './types'
import { STAGE_ORDER } from './types'

const IMPACT: Record<Stage, string> = {
  'Initial access': 'Someone outside the company now has a working way in.',
  'Credential access': 'The password for a real account is in someone else\'s hands.',
  Persistence: 'The attacker can return even after the password is changed.',
  'Privilege escalation': 'The account can now change settings for the whole company.',
  Collection: 'Company files are being gathered up for theft.',
  Exfiltration: 'Data is already leaving the building.',
  Impact: 'Files are being encrypted. Recovery is now measured in days, not hours.',
}

function beatFor(a: Alert): string {
  switch (a.ruleId) {
    case 'spray':
      return `One address tried a short list of common passwords against ${a.users.length} accounts.`
    case 'new-device':
      return `One of those accounts then signed in from ${a.device}, a device it had never used.`
    case 'new-country':
      return `The sign-in came from a country this account has never worked from.`
    case 'mfa-fatigue':
      return `${personName(a.user)} denied several sign-in prompts, then one was approved.`
    case 'oauth-grant':
      return `An outside app was allowed to read this mailbox and stay signed in.`
    case 'forwarding':
      return `A silent rule started copying every incoming message to an address outside the company.`
    case 'priv-esc':
      return `The same account was then handed the highest admin role in the tenant.`
    case 'mass-download':
      return `${a.metric} left the account in one sitting, far above its normal day.`
    case 'external-share':
      return `A company file was shared with a personal mail address.`
    case 'canary':
      return a.metric.includes('renamed')
        ? `${a.metric}. That is encryption, not editing.`
        : `Recovery snapshots were deleted on ${a.device}, minutes before encryption.`
    default:
      return a.metric
  }
}


export function buildStory(incident: CorrelatedIncident): Story {
  const first = incident.alerts[0]
  const last = incident.alerts[incident.alerts.length - 1]
  const accounts = incident.users.map(personName)
  const accountText =
    accounts.length === 1 ? accounts[0] : `${accounts.length} accounts, starting with ${accounts[0]}`

  const orderedStages = [...incident.stages].sort(
    (a, b) => STAGE_ORDER.indexOf(a) - STAGE_ORDER.indexOf(b),
  )
  const why =
    orderedStages.length > 1
      ? `${IMPACT[orderedStages[0]]} ${IMPACT[orderedStages[orderedStages.length - 1]]}`
      : IMPACT[orderedStages[0]]

  return {
    title: incident.title,
    dek: `Between ${fmtTime(first.ts)} and ${fmtTime(last.ts)}, ${incident.alerts.length} ${
      incident.alerts.length === 1 ? 'alert' : 'alerts'
    } touched ${accountText}. Read in order, they are one attack.`,
    beats: incident.alerts.map((a) => ({ ts: a.ts, text: beatFor(a) })),
    why,
    next: 'Work down the list beside this panel. Every action is reversible and simulated here, so nothing outside this demo changes.',
    confidence: `Score is ${incident.basePoints} severity points plus ${incident.stageBonus} for linked stages. Every link below prints its own reason.`,
  }
}

interface ActionSeed {
  key: string
  label: string
  why: string
  effect: string
  urgency: 'now' | 'next'
  target: string
}

function seedFor(ruleId: string, incident: CorrelatedIncident): ActionSeed | null {
  const alert = incident.alerts.find((a) => a.ruleId === ruleId)
  if (!alert) return null

  switch (ruleId) {
    case 'spray':
      return {
        key: 'block-ip',
        label: 'Block the source address',
        why: `${alert.ip} was used to guess passwords across several accounts.`,
        effect: `Simulated: ${alert.subject ?? alert.ip} dropped at the firewall. 6 accounts stop receiving attempts.`,
        urgency: 'now',
        target: alert.subject ?? alert.ip,
      }
    case 'new-device':
    case 'new-country':
      return {
        key: 'sessions',
        label: 'Sign out every session',
        why: 'The attacker is holding a live session, which a password change alone does not end.',
        effect: 'Simulated: 3 sessions closed. The new device is signed out.',
        urgency: 'now',
        target: personName(alert.user),
      }
    case 'mfa-fatigue':
      return {
        key: 'mfa-reset',
        label: 'Reset password, re-register MFA',
        why: 'Repeated push prompts were approved once. The password must be treated as known.',
        effect: 'Simulated: old password revoked, MFA reset on the next sign-in.',
        urgency: 'now',
        target: personName(alert.user),
      }
    case 'forwarding':
      return {
        key: 'forwarding',
        label: 'Delete the forwarding rule',
        why: 'Until it is removed, every new message is copied outside the company.',
        effect: 'Simulated: rule removed. No mail leaves the tenant.',
        urgency: 'now',
        target: alert.subject ?? 'the forwarding address',
      }
    case 'oauth-grant':
      return {
        key: 'oauth',
        label: 'Revoke the app grant',
        why: 'A token keeps working after a password reset, so the app must be removed.',
        effect: 'Simulated: token revoked. The app loses mail access.',
        urgency: 'now',
        target: alert.subject ?? 'the app',
      }
    case 'priv-esc':
      return {
        key: 'admin',
        label: 'Remove the admin role',
        why: 'Admin rights let the attacker add accounts and switch off logging.',
        effect: 'Simulated: role removed. The account is back to standard access.',
        urgency: 'now',
        target: alert.subject ?? 'admin role',
      }
    case 'mass-download':
      return {
        key: 'downloads',
        label: 'Suspend downloads and snapshot',
        why: 'A copy of the mailbox and drive is needed before anything is deleted.',
        effect: 'Simulated: downloads paused, read-only snapshot taken at this minute.',
        urgency: 'next',
        target: personName(alert.user),
      }
    case 'external-share':
      return {
        key: 'share',
        label: 'Revoke the external share',
        why: 'The link works without a sign-in and can be forwarded onward.',
        effect: 'Simulated: link revoked. Recipient access ends immediately.',
        urgency: 'now',
        target: alert.subject ?? 'the shared link',
      }
    case 'canary':
      return {
        key: 'isolate',
        label: 'Isolate the machine and restore backups',
        why: 'Encryption has started. Pulling the machine off the network stops the spread.',
        effect: 'Simulated: network cut on the device, clean snapshot marked for restore.',
        urgency: 'now',
        target: alert.subject ?? alert.device,
      }
    default:
      return null
  }
}

const URGENCY_RANK = { now: 0, next: 1 }

export function buildActions(incident: CorrelatedIncident): ResponseAction[] {
  const seen = new Set<string>()
  const actions: ResponseAction[] = []
  for (const alert of incident.alerts) {
    const seed = seedFor(alert.ruleId, incident)
    if (!seed || seen.has(seed.key)) continue
    seen.add(seed.key)
    actions.push({
      id: seed.key,
      label: seed.label,
      why: seed.why,
      effect: seed.effect,
      urgency: seed.urgency,
      target: seed.target,
    })
  }
  return actions.sort((a, b) => URGENCY_RANK[a.urgency] - URGENCY_RANK[b.urgency])
}
