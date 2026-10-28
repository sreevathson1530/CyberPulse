import type { CorrelatedIncident } from '../lib/correlate'
import { fmtTime } from '../lib/format'
import type { Story } from '../lib/types'

interface Props {
  story: Story | null
  incident: CorrelatedIncident | null
}

export function StoryPanel({ story, incident }: Props) {
  return (
    <section className="panel px-4 py-4">
      <div className="flex items-center justify-between">
        <span className="label">The short version</span>
        <span className="label">plain words</span>
      </div>

      {story && incident ? (
        <>
          <h2 className="mt-2.5 font-serif text-[21px] leading-[1.18] tracking-[-0.005em]">
            {story.title}
          </h2>
          <p className="mt-2 font-serif text-[13.5px] leading-[1.6] text-ink-2">{story.dek}</p>

          <div className="mt-3 space-y-2.5 border-t border-rule pt-3">
            {story.beats.map((b, i) => (
              <div key={`${b.ts}-${i}`} className="grid grid-cols-[36px_minmax(0,1fr)] gap-2">
                <span className="num pt-[3px] text-[9.5px] text-ink-3">{fmtTime(b.ts)}</span>
                <p className="font-serif text-[13px] leading-[1.5] text-ink-2">{b.text}</p>
              </div>
            ))}
          </div>

          <div className="mt-3 border-l-2 border-rust bg-rust-soft/35 px-2.5 py-2">
            <div className="label">Why it matters</div>
            <p className="mt-1 font-serif text-[13px] leading-[1.5] text-ink-2">{story.why}</p>
          </div>

          <p className="mt-2.5 text-[10.5px] leading-snug text-ink-3">{story.next}</p>

          <p className="mt-2.5 border-t border-rule pt-2 text-[9.5px] leading-snug text-ink-4">
            {story.confidence}
          </p>
        </>
      ) : (
        <>
          <h2 className="mt-2.5 font-serif text-[19px] leading-[1.25] text-ink-2">
            Quiet, and that is the product.
          </h2>
          <p className="mt-2 font-serif text-[13px] leading-[1.6] text-ink-3">
            CyberPulse stays silent while events stay unrelated. When two rules agree on an account,
            an address or a device, the incident appears here in plain words.
          </p>
          <div className="mt-3 border-t border-rule pt-2.5">
            <div className="label">What you would get</div>
            <ul className="mt-1.5 space-y-1 font-serif text-[12.5px] leading-snug text-ink-3">
              <li>One story instead of ten warnings</li>
              <li>The evidence behind every link</li>
              <li>Actions in the order they should happen</li>
            </ul>
          </div>
        </>
      )}
    </section>
  )
}
