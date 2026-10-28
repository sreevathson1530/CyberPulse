import type { CorrelatedIncident } from '../lib/correlate'
import { fmtTime } from '../lib/format'
import { ORG, personName } from '../lib/org'

interface Props {
  incident: CorrelatedIncident | null
}

export function ScopePanel({ incident }: Props) {
  return (
    <section className="panel px-4 py-4">
      <div className="flex items-center justify-between">
        <span className="label">Scope</span>
        <span className="label">{incident ? 'this incident' : 'monitored'}</span>
      </div>

      {incident ? (
        <>
          <dl className="mt-2.5 space-y-2">
            <Row
              term="Accounts"
              value={incident.users.map(personName).join(', ')}
              mono={false}
            />
            <Row term="Addresses" value={incident.ips.join(', ') || 'office egress only'} />
            <Row term="Devices" value={incident.devices.join(', ') || 'shared machines only'} />
            <Row
              term="Window"
              value={`${fmtTime(incident.startedAt)} to ${fmtTime(incident.updatedAt)}`}
            />
            <Row term="Stages" value={`${incident.stages.length} of 7`} />
          </dl>
          <div className="mt-2.5 flex flex-wrap gap-1 border-t border-rule pt-2">
            {incident.stages.map((s) => (
              <span
                key={s}
                className="border border-rule px-1.5 py-[2px] font-mono text-[8.5px] tracking-[0.06em] uppercase text-ink-3"
              >
                {s}
              </span>
            ))}
          </div>
        </>
      ) : (
        <>
          <dl className="mt-2.5 space-y-2">
            <Row term="Staff" value={`${ORG.headcount} people, 12 named accounts`} mono={false} />
            <Row term="Log sources" value="Microsoft 365, Google Workspace, endpoint" mono={false} />
            <Row term="Ignored" value="2 office addresses, 2 shared devices" mono={false} />
            <Row term="Connected" value="nothing" />
          </dl>
          <p className="mt-2.5 border-t border-rule pt-2 text-[10px] leading-snug text-ink-3">
            Shared addresses and kiosk machines are excluded on purpose, so a whole floor never
            becomes one suspect.
          </p>
        </>
      )}
    </section>
  )
}

function Row({ term, value, mono = true }: { term: string; value: string; mono?: boolean }) {
  return (
    <div className="grid grid-cols-[68px_minmax(0,1fr)] gap-2">
      <dt className="label pt-[2px] text-[9px]">{term}</dt>
      <dd className={`text-[11px] leading-snug text-ink-2 ${mono ? 'num' : ''}`}>{value}</dd>
    </div>
  )
}
