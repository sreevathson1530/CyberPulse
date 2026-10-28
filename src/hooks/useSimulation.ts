import { useEffect, useMemo, useState } from 'react'
import type { Scenario } from '../lib/scenarios'
import type { TelemetryEvent } from '../lib/types'

const TICK_MS = 250
const SIM_SECONDS_PER_TICK = 40

export type Speed = 1 | 2 | 4

export interface Simulation {
  clock: number
  running: boolean
  finished: boolean
  speed: Speed
  progress: number
  events: TelemetryEvent[]
  play: () => void
  pause: () => void
  reset: () => void
  skipToEnd: () => void
  setSpeed: (s: Speed) => void
}

export function useSimulation(scenario: Scenario): Simulation {
  const [clock, setClock] = useState(scenario.startedAt)
  const [running, setRunning] = useState(true)
  const [speed, setSpeed] = useState<Speed>(1)

  useEffect(() => {
    setClock(scenario.startedAt)
    setRunning(true)
  }, [scenario.id, scenario.startedAt])

  useEffect(() => {
    if (!running) return
    const id = window.setInterval(() => {
      setClock((c) => Math.min(scenario.endAt, c + SIM_SECONDS_PER_TICK * 1000 * speed))
    }, TICK_MS)
    return () => window.clearInterval(id)
  }, [running, speed, scenario.endAt])

  useEffect(() => {
    if (running && clock >= scenario.endAt) setRunning(false)
  }, [clock, scenario.endAt, running])

  const events = useMemo(
    () => scenario.events.filter((e) => e.ts <= clock),
    [scenario.events, clock],
  )

  const span = scenario.endAt - scenario.startedAt
  const progress = span <= 0 ? 1 : Math.min(1, (clock - scenario.startedAt) / span)

  return {
    clock,
    running,
    finished: clock >= scenario.endAt,
    speed,
    progress,
    events,
    play: () => {
      if (clock >= scenario.endAt) setClock(scenario.startedAt)
      setRunning(true)
    },
    pause: () => setRunning(false),
    reset: () => {
      setClock(scenario.startedAt)
      setRunning(false)
    },
    skipToEnd: () => {
      setClock(scenario.endAt)
      setRunning(false)
    },
    setSpeed,
  }
}
