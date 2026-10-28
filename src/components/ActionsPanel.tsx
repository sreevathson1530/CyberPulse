import { Check } from '@phosphor-icons/react'
import type { CorrelatedIncident } from '../lib/correlate'
import { fmtGap } from '../lib/format'
import type { ResponseAction } from '../lib/types'

interface Props {
  actions: ResponseAction[]
  done: string[]
  onToggle: (id: string) => void
  incident: CorrelatedIncident | null
  clock: number
  score: number
}

const SIX_HOURS = 6 * 60 * 60 * 1000
const SEVENTY_TWO_HOURS = 72 * 60 * 60 * 1000

export function ActionsPanel({ actions, done, onToggle, incident, clock, score }: Props) {
  const completed = actions.filter((a) => done.includes(a.id)).length

  return (
    <section className="panel px-4 py-4">
      <div className="flex items-center justify-between">
        <span className="label">Do this now</span>
        <span className="num text-[10px] text-ink-3">
          {completed} of {actions.length || 0}
        </span>
      </div>

      {actions.length === 0 ? (
        <p className="mt-2 font-serif text-[12.5px] leading-relaxed text-ink-3">
          No response is needed while nothing is connected. When an incident appears, the actions
          below are written for a person, not for a security team.
        </p>
      ) : (
        <>
          <div className="mt-2 h-[3px] w-full bg-paper-3">
            <div
              className="h-full bg-rust transition-[width] duration-300"
              style={{ width: `${(completed / actions.length) * 100}%` }}
            />
          </div>

          <ul className="mt-3 space-y-3">
            {actions.map((a) => {
              const checked = done.includes(a.id)
              return (
                <li key={a.id}>
                  <button
                    type="button"
                    onClick={() => onToggle(a.id)}
                    className="flex w-full items-start gap-2 text-left"
                    aria-pressed={checked}
                  >
                    <span
                      className={`mt-[2px] grid h-[15px] w-[15px] shrink-0 place-items-center border transition-colors ${
                        checked
                          ? 'border-ink bg-ink text-paper-2'
                          : 'border-rule-2 bg-paper-2 hover:border-ink-4'
                      }`}
                    >
                      {checked && <Check size={9} weight="bold" />}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span
                        className={`block text-[12.5px] leading-tight ${
                          checked ? 'text-ink-3 line-through' : 'font-medium'
                        }`}
                      >
                        {a.label}
                      </span>
                      <span className="mt-0.5 block font-mono text-[9.5px] leading-tight break-all text-ink-4">
                        {a.target}
                      </span>
                      <span
                        className={`mt-1 block text-[10.5px] leading-snug ${
                          checked ? 'text-rust' : 'text-ink-3'
                        }`}
                      >
                        {checked ? a.effect : a.why}
                      </span>
                    </span>
                  </button>
                </li>
              )
            })}
          </ul>
        </>
      )}

      {incident && score >= 75 && (
        <div className="mt-3 border-t border-rule pt-2.5">
          <div className="label">Reporting clock</div>
          <div className="mt-1.5 space-y-1">
            <div className="flex items-baseline justify-between text-[10.5px]">
              <span className="text-ink-3">CERT-In, 6 hours</span>
              <span className="num">
                {clock - incident.startedAt < SIX_HOURS
                  ? `${fmtGap(SIX_HOURS - (clock - incident.startedAt))} left`
                  : 'overdue'}
              </span>
            </div>
            <div className="flex items-baseline justify-between text-[10.5px]">
              <span className="text-ink-3">DPDP, 72 hours</span>
              <span className="num">
                {clock - incident.startedAt < SEVENTY_TWO_HOURS
                  ? `${fmtGap(SEVENTY_TWO_HOURS - (clock - incident.startedAt))} left`
                  : 'overdue'}
              </span>
            </div>
          </div>
          <p className="mt-1.5 text-[9.5px] leading-snug text-ink-4">
            Counted from the first linked alert, not from the ransom note.
          </p>
        </div>
      )}

      <p className="mt-2.5 border-t border-rule pt-2 text-[9.5px] leading-snug text-ink-4">
        Every action here is simulated. Nothing outside this browser changes.
      </p>
    </section>
  )
}
