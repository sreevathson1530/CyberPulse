import type { EventKind, TelemetryEvent } from './types'

export const EVENT_LABEL: Record<EventKind, string> = {
  'auth.success': 'sign-in ok',
  'auth.failure': 'sign-in failed',
  'auth.mfa_denied': 'MFA denied',
  'auth.mfa_success': 'MFA approved',
  'mail.forwarding_created': 'forwarding rule',
  'mail.sent_external': 'mail out',
  'mail.reply_to_changed': 'reply-to changed',
  'oauth.grant': 'app consent',
  'file.download': 'download',
  'file.share_external': 'external share',
  'admin.role_assigned': 'role assigned',
  'endpoint.shadow_copy_deleted': 'shadow copies deleted',
  'endpoint.mass_rename': 'mass rename',
  'endpoint.process': 'process start',
}

export const EVENT_TONE: Partial<Record<EventKind, 'warm' | 'hot'>> = {
  'auth.failure': 'warm',
  'auth.mfa_denied': 'warm',
  'auth.mfa_success': 'warm',
  'mail.forwarding_created': 'hot',
  'mail.reply_to_changed': 'hot',
  'oauth.grant': 'warm',
  'file.share_external': 'hot',
  'admin.role_assigned': 'hot',
  'endpoint.shadow_copy_deleted': 'hot',
  'endpoint.mass_rename': 'hot',
}

export function eventDetail(e: TelemetryEvent): string {
  if (e.target) return e.target
  if (e.app) return e.app
  if (e.scopes) return e.scopes.join(', ')
  if (typeof e.count === 'number') return `${e.count} files`
  return e.note ?? ''
}
