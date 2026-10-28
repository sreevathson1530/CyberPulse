import { useEffect, useMemo, useRef, useState } from 'react'
import { ActionsPanel } from './components/ActionsPanel'
import { Evidence } from './components/Evidence'
import { Header } from './components/Header'
import { HowItWorks } from './components/HowItWorks'
import { MachineFeed } from './components/MachineFeed'
import { ScenarioRail } from './components/ScenarioRail'
import { ScorePanel } from './components/ScorePanel'
import { ScopePanel } from './components/ScopePanel'
import { StoryPanel } from './components/StoryPanel'
import { Timeline } from './components/Timeline'
import { Verdict } from './components/Verdict'
import { useSimulation } from './hooks/useSimulation'
import { analyze } from './lib/analyze'
import { fmtNumber } from './lib/format'
import { getScenario, type ScenarioId } from './lib/scenarios'

type Tab = 'timeline' | 'evidence' | 'machine' | 'score'

const IDS: ScenarioId[] = ['normal', 'takeover', 'invoice', 'ransomware']

export default function App() {
  const params = useMemo(() => new URLSearchParams(window.location.search), [])
  const linkedScenario = params.get('scenario')
  const jumpToEnd = params.get('t') === 'end'

  const [scenarioId, setScenarioId] = useState<ScenarioId>(() =>
    IDS.includes(linkedScenario as ScenarioId) ? (linkedScenario as ScenarioId) : 'normal',
  )
  const [tab, setTab] = useState<Tab>(() => {
    const t = params.get('tab')
    return t === 'evidence' || t === 'machine' || t === 'score' ? t : 'timeline'
  })
  const [done, setDone] = useState<string[]>([])
  const [howOpen, setHowOpen] = useState(false)
  const jumped = useRef(false)
  const firstRun = useRef(true)

  const scenario = getScenario(scenarioId)
  const sim = useSimulation(scenario)
  const analysis = useMemo(() => analyze(sim.events), [sim.events])
  const incident = analysis.incident
  const score = incident?.score ?? 0

  useEffect(() => {
    setDone([])
    if (firstRun.current) {
      firstRun.current = false
      return
    }
    setTab('timeline')
  }, [scenarioId])

  useEffect(() => {
    if (jumpToEnd && !jumped.current) {
      jumped.current = true
      sim.skipToEnd()
    }
  }, [jumpToEnd, sim])

  const selectScenario = (id: ScenarioId) => setScenarioId(id)

  const toggleAction = (id: string) =>
    setDone((prev) => (prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]))

  const tabs: { id: Tab; label: string; count: string }[] = [
    { id: 'timeline', label: 'Timeline', count: String(analysis.alerts.length) },
    { id: 'evidence', label: 'Evidence', count: fmtNumber(sim.events.length) },
    { id: 'machine', label: 'Machine feed', count: fmtNumber(sim.events.length) },
    { id: 'score', label: 'Scoring', count: score ? String(score) : '0' },
  ]

  return (
    <div className="relative z-[1] flex min-h-[100dvh] flex-col">
      <Header clock={sim.clock} running={sim.running} onOpenHow={() => setHowOpen(true)} />

      <main className="mx-auto w-full max-w-[1560px] flex-1 px-3 pt-3 pb-8 lg:px-5">
        <div className="grid grid-cols-1 gap-3 xl:grid-cols-[252px_minmax(0,1fr)_368px] xl:items-start">
          <ScenarioRail
            scenarioId={scenarioId}
            scenario={scenario}
            sim={sim}
            onSelect={selectScenario}
          />

          <section className="flex min-w-0 flex-col gap-3">
            <Verdict
              score={score}
              incident={incident}
              alertCount={analysis.alerts.length}
              totalEvents={sim.events.length}
              scenario={scenario}
            />

            <div className="panel overflow-hidden">
              <div className="flex items-center gap-0 overflow-x-auto border-b border-rule bg-paper-2 px-2">
                {tabs.map((t) => {
                  const active = tab === t.id
                  return (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => setTab(t.id)}
                      aria-selected={active}
                      role="tab"
                      className={`-mb-px border-b-2 px-2.5 py-2.5 text-[11.5px] font-medium whitespace-nowrap transition-colors ${
                        active
                          ? 'border-ink text-ink'
                          : 'border-transparent text-ink-3 hover:text-ink-2'
                      }`}
                    >
                      {t.label}
                      <span className="num ml-1.5 text-[9.5px] font-normal text-ink-4">
                        {t.count}
                      </span>
                    </button>
                  )
                })}
                <span className="label ml-auto hidden pr-2 whitespace-nowrap md:block">
                  {scenario.name}
                </span>
              </div>

              <div className="max-h-[calc(100dvh-336px)] min-h-[340px] overflow-y-auto">
                {tab === 'timeline' && (
                  <Timeline
                    incident={incident}
                    totalEvents={sim.events.length}
                    progress={sim.progress}
                  />
                )}
                {tab === 'evidence' && (
                  <Evidence events={sim.events} alerts={analysis.alerts} />
                )}
                {tab === 'machine' && <MachineFeed events={sim.events} alerts={analysis.alerts} />}
                {tab === 'score' && <ScorePanel incident={incident} />}
              </div>
            </div>
          </section>

          <aside className="flex flex-col gap-3">
            <StoryPanel story={analysis.story} incident={incident} />
            <ActionsPanel
              actions={analysis.actions}
              done={done}
              onToggle={toggleAction}
              incident={incident}
              clock={sim.clock}
              score={score}
            />
            <ScopePanel incident={incident} />
          </aside>
        </div>
      </main>

      <footer className="mt-auto border-t border-rule">
        <div className="mx-auto flex max-w-[1560px] flex-wrap items-center justify-between gap-2 px-3 py-3 lg:px-5">
          <span className="text-[10px] text-ink-3">
            Synthetic data only. Documentation IP ranges and .example domains.
          </span>
          <span className="text-[10px] text-ink-3">
            Team QUADRAX · DEXATHON 2026 · DEX26335
          </span>
        </div>
      </footer>

      <HowItWorks open={howOpen} onClose={() => setHowOpen(false)} />
    </div>
  )
}
