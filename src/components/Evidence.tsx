import { EVENT_LABEL, eventDetail } from '../lib/labels'
import { fmtTime } from '../lib/format'
import { personName } from '../lib/org'
import type { Alert, TelemetryEvent } from '../lib/types'

interface Props {
  events: TelemetryEvent[]
  alerts: Alert[]
}

export function Evidence({ events, alerts }: Props) {
  const flagged = new Map<string, string>()
  for (const a of alerts) {
    for (const id of a.evidenceIds) flagged.set(id, a.ruleName)
  }

  const rows = [...events].reverse()

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-rule px-3 py-2">
        <span className="label">
          {events.length} events read, {flagged.size} used as evidence
        </span>
        <span className="label">JSONL, one schema</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left">
          <thead>
            <tr className="border-b border-rule bg-paper-3/40">
              <th className="label px-3 py-2 font-medium">Time</th>
              <th className="label px-3 py-2 font-medium">Event</th>
              <th className="label px-3 py-2 font-medium">Account</th>
              <th className="label px-3 py-2 font-medium">Source</th>
              <th className="label px-3 py-2 font-medium">Device</th>
              <th className="label px-3 py-2 font-medium">Detail</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((e) => {
              const rule = flagged.get(e.id)
              return (
                <tr
                  key={e.id}
                  className={`border-b border-rule/60 ${rule ? 'bg-rust-soft/45' : ''}`}
                >
                  <td className="num px-3 py-[5px] align-top text-[10.5px] whitespace-nowrap text-ink-2">
                    {fmtTime(e.ts)}
                  </td>
                  <td className="px-3 py-[5px] align-top text-[10.5px] whitespace-nowrap">
                    <span className={rule ? 'font-medium' : 'text-ink-2'}>
                      {EVENT_LABEL[e.kind]}
                    </span>
                    {rule && (
                      <span className="mt-[2px] block font-mono text-[8.5px] tracking-[0.06em] uppercase text-rust">
                        {rule}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-[5px] align-top text-[10.5px] whitespace-nowrap text-ink-2">
                    {personName(e.user)}
                  </td>
                  <td className="num px-3 py-[5px] align-top text-[10px] whitespace-nowrap text-ink-3">
                    {e.ip}
                  </td>
                  <td className="num px-3 py-[5px] align-top text-[10px] whitespace-nowrap text-ink-3">
                    {e.device}
                  </td>
                  <td className="max-w-[240px] truncate px-3 py-[5px] align-top text-[10px] text-ink-3">
                    {eventDetail(e)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      {events.length === 0 && (
        <p className="px-3 py-8 text-center text-[12px] text-ink-3">
          Waiting for the first event. Press play.
        </p>
      )}
    </div>
  )
}
