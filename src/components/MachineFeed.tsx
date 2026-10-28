import { EVENT_LABEL, EVENT_TONE, eventDetail } from '../lib/labels'
import { fmtClock } from '../lib/format'
import { personName } from '../lib/org'
import type { Alert, TelemetryEvent } from '../lib/types'

interface Props {
  events: TelemetryEvent[]
  alerts: Alert[]
}

export function MachineFeed({ events, alerts }: Props) {
  const flagged = new Set(alerts.flatMap((a) => a.evidenceIds))
  const rows = [...events].slice(-44).reverse()

  return (
    <div className="flex min-h-[340px] flex-col bg-night">
      <div className="flex items-center justify-between border-b border-night-3 px-3 py-2">
        <span className="label text-[9px] text-paper-3/50">Machine feed, raw events</span>
        <span className="num text-[9.5px] text-paper-3/40">{events.length} received</span>
      </div>
      <div className="flex-1 overflow-x-auto px-3 py-2">
        <div className="space-y-[2px] font-mono text-[10.5px] leading-[1.45]">
          {rows.map((e) => {
            const hot = flagged.has(e.id)
            const tone = EVENT_TONE[e.kind]
            const color = hot ? '#eda07f' : tone === 'warm' ? '#d9b48a' : 'rgba(244,240,230,0.66)'
            return (
              <div key={e.id} className="flex items-baseline gap-2 whitespace-nowrap">
                <span className="shrink-0 text-paper-3/35">{fmtClock(e.ts)}</span>
                <span className="w-[118px] shrink-0 truncate" style={{ color }}>
                  {EVENT_LABEL[e.kind]}
                </span>
                <span className="w-[104px] shrink-0 truncate text-paper-3/60">
                  {personName(e.user)}
                </span>
                <span className="hidden w-[112px] shrink-0 truncate text-paper-3/45 sm:block">
                  {e.ip}
                </span>
                <span className="hidden flex-1 truncate text-paper-3/35 md:block">
                  {e.device} {eventDetail(e)}
                </span>
              </div>
            )
          })}
          {rows.length === 0 && (
            <div className="py-6 text-center text-[11px] text-paper-3/40">
              No events yet. Press play.
            </div>
          )}
        </div>
      </div>
      <div className="mt-auto flex items-center justify-between border-t border-night-3 px-3 py-2">
        <span className="text-[9.5px] text-paper-3/35">
          Synthetic data only. Documentation IP ranges, .example domains.
        </span>
        <span className="label text-[8.5px] text-paper-3/30">runs in this tab</span>
      </div>
    </div>
  )
}
