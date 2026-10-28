import { ArrowCounterClockwise, FastForward, Pause, Play } from '@phosphor-icons/react'
import { fmtTime } from '../lib/format'
import { RULES } from '../lib/rules'
import { SCENARIOS, type Scenario, type ScenarioId } from '../lib/scenarios'
import type { Simulation } from '../hooks/useSimulation'
import { SEVERITY_HEX } from './ui'

interface Props {
  scenarioId: ScenarioId
  scenario: Scenario
  sim: Simulation
  onSelect: (id: ScenarioId) => void
}

export function ScenarioRail({ scenarioId, scenario, sim, onSelect }: Props) {
  return (
    <aside className="flex flex-col gap-3">
      <section className="panel p-3">
        <div className="flex items-center justify-between">
          <span className="label">Scenario</span>
          <span className="num text-[10px] text-ink-3">{scenario.events.length} events</span>
        </div>

        <div className="mt-2 space-y-1">
          {SCENARIOS.map((s) => {
            const active = s.id === scenarioId
            return (
              <button
                key={s.id}
                type="button"
                onClick={() => onSelect(s.id)}
                className={`w-full border px-2.5 py-2 text-left transition-colors ${
                  active
                    ? 'border-ink bg-paper-3'
                    : 'border-transparent hover:border-rule-2 hover:bg-paper-3/60'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[12.5px] font-medium">{s.name}</span>
                  <span
                    className="shrink-0 font-mono text-[9px] tracking-[0.06em] uppercase"
                    style={{ color: s.id === 'normal' ? '#7d7463' : '#962b24' }}
                  >
                    {s.expectation}
                  </span>
                </div>
                <div className="mt-0.5 text-[10.5px] leading-snug text-ink-3">{s.blurb}</div>
              </button>
            )
          })}
        </div>

        <div className="mt-3 border-t border-rule pt-3">
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              className="btn btn-primary flex-1"
              onClick={sim.running ? sim.pause : sim.play}
            >
              {sim.running ? <Pause size={12} weight="bold" /> : <Play size={12} weight="bold" />}
              {sim.running ? 'Pause' : sim.finished ? 'Replay' : 'Play'}
            </button>
            <button
              type="button"
              className="btn px-2"
              onClick={sim.reset}
              aria-label="Reset scenario"
              title="Reset scenario"
            >
              <ArrowCounterClockwise size={13} weight="bold" />
            </button>
            <button
              type="button"
              className="btn px-2"
              onClick={sim.skipToEnd}
              aria-label="Skip to the end"
              title="Skip to the end"
            >
              <FastForward size={13} weight="bold" />
            </button>
          </div>

          <div className="mt-2 flex items-center gap-1">
            {([1, 2, 4] as const).map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => sim.setSpeed(s)}
                className={`num border px-1.5 py-[3px] text-[9.5px] ${
                  sim.speed === s
                    ? 'border-ink bg-ink text-paper-2'
                    : 'border-rule text-ink-3 hover:border-ink-4'
                }`}
              >
                {s}x
              </button>
            ))}
            <span className="num ml-auto text-[10px] text-ink-3">{fmtTime(sim.clock)}</span>
          </div>

          <div className="mt-2 h-[3px] w-full bg-paper-3">
            <div
              className="h-full bg-ink transition-[width] duration-200"
              style={{ width: `${sim.progress * 100}%` }}
            />
          </div>
          <div className="mt-1.5 flex justify-between">
            <span className="label text-[9px]">Simulated clock</span>
            <span className="label text-[9px]">
              {sim.finished ? 'finished' : 'playing'}
            </span>
          </div>
        </div>
      </section>

      <section className="panel p-3">
        <div className="flex items-center justify-between">
          <span className="label">Rules armed</span>
          <span className="num text-[10px] text-ink-3">10 active</span>
        </div>
        <ul className="mt-2.5 space-y-[7px]">
          {RULES.map((r) => (
            <li key={r.id} className="flex items-start gap-2">
              <span
                className="mt-[5px] h-1.5 w-1.5 shrink-0 rounded-full"
                style={{ background: SEVERITY_HEX[r.severity] }}
              />
              <div className="min-w-0">
                <div className="text-[11.5px] leading-tight">{r.name}</div>
                <div className="mt-[1px] text-[9.5px] leading-tight text-ink-4">
                  {r.stage} · {r.mitre}
                </div>
              </div>
            </li>
          ))}
        </ul>
        <p className="mt-3 border-t border-rule pt-2 text-[10px] leading-snug text-ink-3">
          Rules decide. A language model may reword the explanation. It never sets the score.
        </p>
      </section>
    </aside>
  )
}
