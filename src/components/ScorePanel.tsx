import type { CorrelatedIncident } from '../lib/correlate'
import { fmtTime } from '../lib/format'
import { SEVERITY_POINTS } from '../lib/types'
import type { Severity } from '../lib/types'
import { SEVERITY_HEX, SEVERITY_LABEL } from './ui'

interface Props {
  incident: CorrelatedIncident | null
}

export function ScorePanel({ incident }: Props) {
  const rows = incident?.scoreResult.rows ?? []
  const base = incident?.basePoints ?? 0
  const bonus = incident?.stageBonus ?? 0
  const raw = base + bonus
  const final = Math.min(100, raw)
  const extraStages = Math.max(0, (incident?.stages.length ?? 0) - 1)

  return (
    <div className="space-y-4 p-4">
      <div className="grid gap-3 sm:grid-cols-[1.15fr_1fr]">
        <div className="border border-rule bg-paper-3/40 p-3">
          <div className="label">The formula, printed</div>
          <div className="mt-2 space-y-1 font-mono text-[11.5px] leading-relaxed text-ink-2">
            <div>score = severity points</div>
            <div className="pl-4">+ 10 per extra attack stage</div>
            <div className="pl-4">capped at 100</div>
          </div>
          <p className="mt-2 text-[10.5px] leading-snug text-ink-3">
            No weighting, no hidden model. Change a rule and the arithmetic changes with it.
          </p>
        </div>

        <div className="border border-rule bg-paper-2 p-3">
          <div className="label">Severity points</div>
          <ul className="mt-2 space-y-1">
            {(Object.keys(SEVERITY_POINTS) as Severity[]).map((s) => (
              <li key={s} className="flex items-center justify-between text-[11px]">
                <span className="flex items-center gap-1.5">
                  <span
                    className="h-1.5 w-1.5 rounded-full"
                    style={{ background: SEVERITY_HEX[s] }}
                  />
                  {SEVERITY_LABEL[s]}
                </span>
                <span className="num text-ink-2">{SEVERITY_POINTS[s]}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {rows.length === 0 ? (
        <div className="border border-dashed border-rule-2 px-4 py-10 text-center">
          <p className="text-[12.5px] text-ink-3">
            No alert has fired yet, so there is nothing to add up. The score stays at zero until a
            rule has evidence.
          </p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto border border-rule">
            <table className="w-full border-collapse text-left">
              <thead>
                <tr className="border-b border-rule bg-paper-3/40">
                  <th className="label px-3 py-2 font-medium">Time</th>
                  <th className="label px-3 py-2 font-medium">Alert</th>
                  <th className="label px-3 py-2 font-medium">Stage</th>
                  <th className="label px-3 py-2 text-right font-medium">Points</th>
                  <th className="label px-3 py-2 text-right font-medium">Running</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.alertId} className="border-b border-rule/60">
                    <td className="num px-3 py-[6px] text-[10.5px] text-ink-3">
                      {fmtTime(
                        incident?.alerts.find((a) => a.id === r.alertId)?.ts ?? Date.now(),
                      )}
                    </td>
                    <td className="px-3 py-[6px] text-[11px]">{r.label}</td>
                    <td className="px-3 py-[6px] text-[10.5px] text-ink-3">{r.stage}</td>
                    <td className="num px-3 py-[6px] text-right text-[11px]">+{r.points}</td>
                    <td className="num px-3 py-[6px] text-right text-[11px] font-medium">
                      {r.running}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="ml-auto w-full max-w-[340px] border border-rule bg-paper-2 p-3">
            <div className="flex items-baseline justify-between py-[3px] text-[11.5px]">
              <span className="text-ink-3">Severity points</span>
              <span className="num">{base}</span>
            </div>
            <div className="flex items-baseline justify-between py-[3px] text-[11.5px]">
              <span className="text-ink-3">
                Stage bonus ({extraStages} extra {extraStages === 1 ? 'stage' : 'stages'} x 10)
              </span>
              <span className="num">+{bonus}</span>
            </div>
            <div className="mt-1 flex items-baseline justify-between border-t border-rule pt-2 text-[12px]">
              <span>Total before cap</span>
              <span className="num">{raw}</span>
            </div>
            <div className="mt-1 flex items-baseline justify-between text-[13px] font-medium">
              <span>Score</span>
              <span className="num">
                {final}
                {raw > 100 && <span className="ml-1 text-[10px] font-normal text-ink-3">capped</span>}
              </span>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
