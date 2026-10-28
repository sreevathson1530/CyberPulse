import { BANDS, bandOf } from '../lib/correlate'
import type { CorrelatedIncident } from '../lib/correlate'
import { fmtGap, fmtNumber, fmtTime } from '../lib/format'
import type { Scenario } from '../lib/scenarios'
import { BAND_HEX } from './ui'

interface Props {
  score: number
  incident: CorrelatedIncident | null
  alertCount: number
  totalEvents: number
  scenario: Scenario
}

export function Verdict({ score, incident, alertCount, totalEvents, scenario }: Props) {
  const band = bandOf(score)
  const bandMeta = BANDS.find((b) => b.id === band)!
  const firstLikely = incident?.scoreResult.firstLikelyAt ?? null

  let subline: string
  if (!incident) {
    subline = `${fmtNumber(totalEvents)} events read. Ten rules armed. A normal evening stays quiet, and that is the point.`
  } else if (band === 'watch') {
    subline = `${alertCount} alert so far. One loose clue is not an attack, so the score stays in Watch.`
  } else if (band === 'suspicious') {
    subline = `${alertCount} alerts now linked across ${incident.stages.length} attack stages. The rules are agreeing with each other.`
  } else {
    const gap =
      scenario.impactAt && firstLikely ? fmtGap(scenario.impactAt - firstLikely) : null
    subline = gap
      ? `${alertCount} alerts, ${incident.stages.length} stages, one incident. Red at ${fmtTime(
          firstLikely!,
        )}, ${gap} before ${scenario.impactLabel.toLowerCase()}.`
      : `${alertCount} alerts across ${incident.stages.length} stages. One incident, explained below.`
  }

  return (
    <section className="panel overflow-hidden">
      <div className="px-4 py-4 lg:px-5">
        <div className="flex flex-wrap items-start justify-between gap-x-6 gap-y-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="label">Verdict</span>
              {incident && (
                <span className="num text-[10px] tracking-[0.08em] text-ink-3">{incident.id}</span>
              )}
            </div>
            <div className="mt-1.5 flex flex-wrap items-baseline gap-x-2.5 gap-y-1">
              <h1
                className="text-[27px] leading-none font-semibold tracking-[-0.025em] sm:text-[31px]"
                style={{ color: BAND_HEX[band] }}
              >
                {bandMeta.label}
              </h1>
              <span className="text-[11.5px] text-ink-3">{bandMeta.note}</span>
            </div>
            <p className="mt-2 max-w-[64ch] text-[12.5px] leading-relaxed text-ink-2">{subline}</p>
          </div>

          <div className="flex items-start gap-4">
            {scenario.impactAt && score >= 40 && (
              <div className="hidden border-l border-rule pl-3.5 lg:block">
                <div className="label">If nothing changes</div>
                <div className="num mt-1.5 text-[14px] leading-none">
                  {fmtTime(scenario.impactAt)}
                </div>
                <div className="mt-1 max-w-[16ch] text-[10.5px] leading-tight text-ink-3">
                  {scenario.impactLabel}
                </div>
              </div>
            )}
            <div className="text-right">
              <div className="num text-[38px] leading-[0.9] font-medium">{score}</div>
              <div className="label mt-2">of 100</div>
            </div>
          </div>
        </div>

        <Meter score={score} />
      </div>
    </section>
  )
}

function Meter({ score }: { score: number }) {
  return (
    <div className="mt-5">
      <div className="relative h-6">
        <div className="absolute inset-x-0 top-[9px] h-[5px] bg-paper-3" />
        <div
          className="absolute top-[9px] h-[5px]"
          style={{ left: 0, width: '40%', background: 'rgba(169,104,11,0.24)' }}
        />
        <div
          className="absolute top-[9px] h-[5px]"
          style={{ left: '40%', width: '35%', background: 'rgba(180,70,31,0.22)' }}
        />
        <div
          className="absolute top-[9px] h-[5px]"
          style={{ left: '75%', width: '25%', background: 'rgba(150,43,36,0.24)' }}
        />
        {Array.from({ length: 11 }, (_, i) => (
          <span
            key={i}
            className="absolute top-[6px] h-[11px] w-px bg-rule-2"
            style={{ left: `${i * 10}%` }}
          />
        ))}
        <div
          className="absolute top-[9px] h-[5px] bg-ink transition-[width] duration-500 ease-out"
          style={{ left: 0, width: `${score}%` }}
        />
        <div
          className="absolute top-0 h-[23px] w-[2px] bg-ink transition-[left] duration-500 ease-out"
          style={{ left: `calc(${score}% - 1px)` }}
        />
      </div>
      <div className="mt-1 flex">
        <div style={{ width: '40%' }}>
          <span className="label text-[9px]">Watch 1-39</span>
        </div>
        <div style={{ width: '35%' }}>
          <span className="label text-[9px]">Suspicious 40-74</span>
        </div>
        <div style={{ width: '25%' }} className="text-right">
          <span className="label text-[9px]">Likely 75+</span>
        </div>
      </div>
    </div>
  )
}
