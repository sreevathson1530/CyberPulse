import { HOUR, MINUTE } from './format'
import { ORG, person } from './org'
import type { EventKind, TelemetryEvent } from './types'

export type ScenarioId = 'normal' | 'takeover' | 'invoice' | 'ransomware'

export interface Scenario {
  id: ScenarioId
  name: string
  blurb: string
  expectation: string
  startedAt: number
  endAt: number
  impactAt: number | null
  impactLabel: string
  events: TelemetryEvent[]
}

const BASE = Date.UTC(2026, 9, 27, 0, 0, 0)

function at(h: number, m: number, s = 0, day = 0): number {
  return BASE + day * 24 * HOUR + h * HOUR + m * MINUTE + s * 1000
}

interface Draft {
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

function compile(drafts: Draft[]): TelemetryEvent[] {
  return drafts
    .slice()
    .sort((a, b) => a.ts - b.ts)
    .map((d, i) => ({ ...d, id: `e-${String(i + 1).padStart(3, '0')}` }))
}

function seeded(seed: number): () => number {
  let s = seed >>> 0
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0
    return s / 4294967296
  }
}

const OFFICE = ORG.officeIps
const HOME = '192.0.2.5'
const BUYERS = ['accounts@northwind.example', 'purchase@bluekite.example', 'ops@aranya.example']
const FILES = [
  'ledger-oct.xlsx',
  'buyer-list-q4.xlsx',
  'gst-returns-fy26.zip',
  'payroll-oct.pdf',
  'design-pack-v7.zip',
]

const AMBIENT_USERS = [
  'divya',
  'priya',
  'arjun',
  'karthik',
  'meera',
  'rahim',
  'nithya',
  'sowmya',
  'anitha',
  'joseph',
  'ganesh',
  'vikram',
]

function normalDay(day: number): Draft[] {
  const rand = seeded(20261027)
  const drafts: Draft[] = []
  let ts = at(20, 58, 0, day)
  let failures = 0

  while (ts < at(22, 30, 0, day)) {
    ts += Math.round(40 + rand() * 110) * 1000
    const user = AMBIENT_USERS[Math.floor(rand() * AMBIENT_USERS.length)]
    const p = person(user)
    const device = p.devices[Math.floor(rand() * p.devices.length)]
    const ip = rand() < 0.14 ? HOME : OFFICE[Math.floor(rand() * OFFICE.length)]
    const roll = rand()

    if (roll < 0.46) {
      drafts.push({
        ts,
        kind: 'auth.success',
        user,
        ip,
        device,
        country: 'IN',
        city: 'Tiruppur',
        outcome: 'success',
      })
    } else if (roll < 0.64) {
      drafts.push({
        ts,
        kind: 'file.download',
        user,
        ip,
        device,
        country: 'IN',
        city: 'Tiruppur',
        count: 1 + Math.floor(rand() * 3),
        target: FILES[Math.floor(rand() * FILES.length)],
      })
    } else if (roll < 0.79) {
      drafts.push({
        ts,
        kind: 'mail.sent_external',
        user,
        ip,
        device,
        country: 'IN',
        city: 'Tiruppur',
        target: BUYERS[Math.floor(rand() * BUYERS.length)],
      })
    } else if (roll < 0.9) {
      drafts.push({
        ts,
        kind: 'endpoint.process',
        user,
        ip,
        device,
        country: 'IN',
        city: 'Tiruppur',
        target: 'EXCEL.EXE',
      })
    } else if (failures < 2) {
      failures++
      drafts.push({
        ts,
        kind: 'auth.failure',
        user,
        ip: OFFICE[0],
        device,
        country: 'IN',
        city: 'Tiruppur',
        outcome: 'failure',
        note: 'wrong password',
      })
    } else {
      drafts.push({
        ts,
        kind: 'file.share_external',
        user,
        ip,
        device,
        country: 'IN',
        city: 'Tiruppur',
        target: `dispatch@${BUYERS[0].split('@')[1]}`,
      })
    }
  }
  return drafts
}

function takeover(day: number): Draft[] {
  const ip = '198.51.100.77'
  const device = 'DESKTOP-9F2A'
  const geo = { country: 'IN', city: 'Mumbai' }
  const attackers = ['divya', 'priya', 'arjun', 'karthik', 'meera', 'rahim']

  const drafts: Draft[] = [
    { ts: at(21, 44, 12, day), kind: 'auth.success', user: 'divya', ip: OFFICE[0], device: 'LAPTOP-FIN-04', country: 'IN', city: 'Tiruppur' },
    { ts: at(21, 47, 3, day), kind: 'file.download', user: 'sowmya', ip: OFFICE[1], device: 'DESKTOP-ACC-02', country: 'IN', city: 'Tiruppur', count: 3, target: 'ledger-oct.xlsx' },
    { ts: at(21, 50, 41, day), kind: 'auth.success', user: 'arjun', ip: OFFICE[0], device: 'LAPTOP-SALES-11', country: 'IN', city: 'Tiruppur' },
  ]

  const times = [
    [21, 52, 10],
    [21, 52, 31],
    [21, 52, 54],
    [21, 53, 12],
    [21, 53, 38],
    [21, 53, 51],
    [21, 54, 9],
    [21, 54, 27],
    [21, 54, 48],
  ]
  times.forEach(([h, m, s], i) => {
    drafts.push({
      ts: at(h, m, s, day),
      kind: 'auth.failure',
      user: attackers[i % attackers.length],
      ip,
      device: 'unregistered-device',
      country: 'NL',
      city: 'Amsterdam',
      outcome: 'failure',
      note: 'wrong password',
    })
  })

  drafts.push(
    {
      ts: at(22, 7, 12, day),
      kind: 'auth.success',
      user: 'divya',
      ip,
      device,
      ...geo,
      outcome: 'success',
      note: 'VPN exit',
    },
    {
      ts: at(22, 15, 30, day),
      kind: 'mail.forwarding_created',
      user: 'divya',
      ip,
      device,
      ...geo,
      target: 'finance.archive@mailbox.example',
    },
    {
      ts: at(22, 31, 5, day),
      kind: 'admin.role_assigned',
      user: 'divya',
      ip,
      device,
      ...geo,
      target: 'Global Admin',
    },
    {
      ts: at(22, 38, 44, day),
      kind: 'mail.sent_external',
      user: 'divya',
      ip,
      device,
      ...geo,
      target: 'accounts@northwind.example',
      note: 'reply-to rewritten',
    },
    {
      ts: at(22, 52, 10, day),
      kind: 'file.download',
      user: 'divya',
      ip,
      device,
      ...geo,
      count: 140,
      target: 'finance-drive',
    },
    {
      ts: at(23, 4, 20, day),
      kind: 'auth.success',
      user: 'priya',
      ip: OFFICE[0],
      device: 'MACBOOK-MD-01',
      country: 'IN',
      city: 'Tiruppur',
    },
  )

  return drafts
}

function invoiceFraud(day: number): Draft[] {
  const ip = OFFICE[1]
  const device = 'DESKTOP-ACC-02'
  const geo = { country: 'IN', city: 'Tiruppur' }

  return [
    { ts: at(14, 40, 8, day), kind: 'auth.success', user: 'sowmya', ip, device, ...geo, outcome: 'success' },
    { ts: at(14, 44, 51, day), kind: 'mail.sent_external', user: 'sowmya', ip, device, ...geo, target: 'accounts@northwind.example' },
    {
      ts: at(14, 48, 20, day),
      kind: 'oauth.grant',
      user: 'sowmya',
      ip,
      device,
      ...geo,
      app: 'DocuSign Verify',
      scopes: ['mail.read', 'offline_access'],
    },
    {
      ts: at(14, 56, 5, day),
      kind: 'mail.forwarding_created',
      user: 'sowmya',
      ip,
      device,
      ...geo,
      target: 'billing@mailbox.example',
    },
    {
      ts: at(15, 2, 40, day),
      kind: 'mail.reply_to_changed',
      user: 'sowmya',
      ip,
      device,
      ...geo,
      target: 'billing@mailbox.example',
    },
    {
      ts: at(15, 12, 18, day),
      kind: 'file.share_external',
      user: 'sowmya',
      ip,
      device,
      ...geo,
      target: 'vanavil.invoices@gmail.example',
    },
    {
      ts: at(15, 20, 55, day),
      kind: 'mail.sent_external',
      user: 'sowmya',
      ip,
      device,
      ...geo,
      target: 'accounts@northwind.example',
      note: 'attachment: invoice-8841.pdf',
    },
    { ts: at(15, 26, 2, day), kind: 'auth.success', user: 'rahim', ip: OFFICE[0], device: 'DESKTOP-PUR-01', country: 'IN', city: 'Tiruppur' },
  ]
}

function ransomware(nextDay: number): Draft[] {
  const ip = '192.0.2.44'
  const device = 'DESKTOP-Q7'
  const geo = { country: 'SG', city: 'Singapore' }
  const targets = ['meera', 'karthik', 'anitha', 'ganesh', 'meera', 'karthik']

  const drafts: Draft[] = [
    { ts: at(2, 2, 30, nextDay), kind: 'auth.success', user: 'karthik', ip: OFFICE[0], device: 'LAPTOP-OPS-07', country: 'IN', city: 'Tiruppur' },
    { ts: at(2, 4, 12, nextDay), kind: 'file.download', user: 'meera', ip: OFFICE[1], device: 'LAPTOP-HR-02', country: 'IN', city: 'Tiruppur', count: 2, target: 'payroll-oct.pdf' },
  ]

  const failTimes = [
    [2, 8, 12],
    [2, 8, 40],
    [2, 9, 5],
    [2, 9, 33],
    [2, 10, 2],
    [2, 10, 49],
  ]
  failTimes.forEach(([h, m, s], i) => {
    drafts.push({
      ts: at(h, m, s, nextDay),
      kind: 'auth.failure',
      user: targets[i],
      ip,
      device: 'unregistered-device',
      ...geo,
      outcome: 'failure',
      note: 'wrong password',
    })
  })

  ;[
    [2, 14, 30],
    [2, 15, 2],
    [2, 15, 40],
  ].forEach(([h, m, s]) => {
    drafts.push({
      ts: at(h, m, s, nextDay),
      kind: 'auth.mfa_denied',
      user: 'meera',
      ip,
      device,
      ...geo,
      note: 'push denied by user',
    })
  })

  drafts.push(
    { ts: at(2, 16, 5, nextDay), kind: 'auth.mfa_success', user: 'meera', ip, device, ...geo, note: 'push approved' },
    { ts: at(2, 22, 18, nextDay), kind: 'auth.success', user: 'meera', ip, device, ...geo, outcome: 'success' },
    { ts: at(2, 30, 44, nextDay), kind: 'admin.role_assigned', user: 'meera', ip, device, ...geo, target: 'Global Admin' },
    { ts: at(2, 41, 10, nextDay), kind: 'file.download', user: 'meera', ip, device, ...geo, count: 380, target: 'hr-drive' },
    {
      ts: at(2, 52, 33, nextDay),
      kind: 'endpoint.shadow_copy_deleted',
      user: 'meera',
      ip: '10.20.4.18',
      device: 'FILESERVER-01',
      ...geo,
      note: 'vssadmin delete shadows',
    },
    {
      ts: at(3, 4, 12, nextDay),
      kind: 'endpoint.mass_rename',
      user: 'meera',
      ip: '10.20.4.18',
      device: 'FILESERVER-01',
      ...geo,
      count: 1840,
    },
  )

  return drafts
}

const normalEvents = compile(normalDay(0))
const takeoverEvents = compile(takeover(0))
const invoiceEvents = compile(invoiceFraud(0))
const ransomwareEvents = compile(ransomware(1))

export const SCENARIOS: Scenario[] = [
  {
    id: 'normal',
    name: 'A normal Tuesday',
    blurb: 'Ninety minutes of ordinary work. Ten rules armed, nothing connects.',
    expectation: 'No incident',
    startedAt: normalEvents[0].ts,
    endAt: at(22, 32, 0, 0),
    impactAt: null,
    impactLabel: 'No impact',
    events: normalEvents,
  },
  {
    id: 'takeover',
    name: 'Account takeover',
    blurb: 'A spray at 21:52 becomes full control of a finance account by 22:31.',
    expectation: 'Likely attack',
    startedAt: at(21, 42, 0, 0),
    endAt: at(23, 8, 0, 0),
    impactAt: at(1, 30, 30, 1),
    impactLabel: 'Finance share encrypted',
    events: takeoverEvents,
  },
  {
    id: 'invoice',
    name: 'Invoice fraud',
    blurb: 'A quiet mail rule sends every invoice to a lookalike domain.',
    expectation: 'Likely attack',
    startedAt: at(14, 36, 0, 0),
    endAt: at(15, 30, 0, 0),
    impactAt: at(16, 40, 0, 0),
    impactLabel: 'Customer pays the altered invoice',
    events: invoiceEvents,
  },
  {
    id: 'ransomware',
    name: 'Ransomware staging',
    blurb: 'A 02:08 break-in ends with 1,840 files renamed at 03:04.',
    expectation: 'Likely attack',
    startedAt: at(2, 0, 0, 1),
    endAt: at(3, 8, 0, 1),
    impactAt: at(3, 4, 12, 1),
    impactLabel: 'FILESERVER-01 encrypted',
    events: ransomwareEvents,
  },
]

export function getScenario(id: ScenarioId): Scenario {
  return SCENARIOS.find((s) => s.id === id) ?? SCENARIOS[0]
}
