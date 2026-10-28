import { LinkSimple } from '@phosphor-icons/react'
import type { CorrelatedIncident } from '../lib/correlate'
import { fmtTime } from '../lib/format'
import { SEVERITY_HEX, SeverityTag } from './ui'

interface Props {
  incident: CorrelatedIncident | null
  totalEvents: number
  progress: number
}

export function Timeline({ incident, totalEvents, progress }: Props) {
  if (!incident) {
    return (
      <div className="flex min-h-[340px] flex-col items-center justify-center px-6 py-14 text-center">
        <div className="grid h-11 w-11 place-items-center rounded-full border border-rule bg-paper-3/60">
          <span className="relative flex h-2 w-2">
            <span className="absolute inset-0 rounded-full bg-ink-4" />
          </span>
        </div>
        <h3 className="mt-3 text-[14px] font-medium">Nothing is connected</h3>
        <p className="mt-1 max-w-[42ch] text-[12px] leading-relaxed text-ink-3">
          {totalEvents} events read so far and no rule has fired twice on the same account. A single
          alert stays at Watch. Only linked stages pull the score up.
        </p>
        <div className="mt-4 flex items-center gap-2">
          <div className="h-[3px] w-24 bg-paper-3">
            <div className="h-full bg-ink-4 transition-[width]" style={{ width: `${progress * 100}%` }} />
          </div>
          <span className="label text-[9px]">Reading</span>
        </div>
      </div>
    )
  }

  return (
    <ol className="p-4">
      {incident.alerts.map((a, i) => {
        const links = incident.links[a.id] ?? []
        const isLast = i === incident.alerts.length - 1
        const color = SEVERITY_HEX[a.severity]
        return (
          <li key={a.id} className="grid grid-cols-[46px_14px_minmax(0,1fr)] stagger-in">
            <div className="num pr-2 pt-[6px] text-right text-[11px] text-ink-2">
              {fmtTime(a.ts)}
            </div>
            <div className="relative">
              <span
                className="absolute top-[8px] left-1/2 h-[8px] w-[8px] -translate-x-1/2 rounded-full"
                style={{ background: color }}
              />
              {!isLast && (
                <span className="absolute top-[19px] bottom-[-6px] left-1/2 w-px -translate-x-1/2 bg-rule-2" />
              )}
            </div>
            <div className="pb-4 pl-1">
              <article
                className="border border-rule bg-paper-2 px-3 py-2.5"
                style={{ borderLeft: `2px solid ${color}` }}
              >
                <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                  <h3 className="text-[13px] leading-none font-medium">{a.ruleName}</h3>
                  <SeverityTag severity={a.severity} />
                  <span className="num ml-auto text-[9.5px] text-ink-4">{a.mitre}</span>
                </div>
                <div className="mt-1.5 text-[11.5px] font-medium text-ink-2">{a.metric}</div>
                <p className="mt-1 text-[12px] leading-relaxed text-ink-2">{a.detail}</p>
                <p className="mt-1.5 text-[10.5px] leading-snug text-ink-3">
                  <span className="font-mono text-[9px] tracking-[0.1em] uppercase">baseline</span>{' '}
                  {a.baseline}
                </p>
                <div className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-[10px] text-ink-4">
                  <span>{a.evidenceIds.length} evidence events</span>
                  <span className="text-rule-2">|</span>
                  <span>{a.stage}</span>
                </div>
              </article>

              {links.length > 0 && (
                <div className="mt-1.5 flex items-start gap-1.5 pl-0.5 text-[10.5px] leading-snug text-ink-3">
                  <LinkSimple size={11} className="mt-[2px] shrink-0" />
                  <span>{links.map((l) => l.reason).join(' · ')}</span>
                </div>
              )}
            </div>
          </li>
        )
      })}
    </ol>
  )
}
