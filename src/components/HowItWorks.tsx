import { X } from '@phosphor-icons/react'
import { AnimatePresence, motion } from 'motion/react'
import { useEffect } from 'react'
import { Logo } from './ui'

interface Props {
  open: boolean
  onClose: () => void
}

const STEPS = [
  {
    verb: 'Detect',
    body: 'Ten written rules read the logs the business already has. Each rule is a sentence a person can check, and each one names the stage of an attack it belongs to.',
  },
  {
    verb: 'Connect',
    body: 'Alerts that share an account, an address or a device inside six hours become one incident. Shared office addresses and kiosk machines are ignored so unrelated people never get joined up.',
  },
  {
    verb: 'Score',
    body: 'Severity points are added, plus ten for each extra attack stage, capped at 100. Watch is 1 to 39. Suspicious is 40 to 74. Likely attack is 75 and above.',
  },
  {
    verb: 'Explain',
    body: 'A template turns the evidence into ordinary sentences. A language model may reword them, but it never sees the decision and it never sets the score.',
  },
  {
    verb: 'Respond',
    body: 'The response list is ordered by what stops the damage first. Each step says what it does and what would change once it is done.',
  },
]

const IGNORED = [
  'Shared office addresses, so a whole floor is never one suspect.',
  'Reception and warehouse kiosks, where many people sign in.',
  'A single alert with nothing linked to it. It stays at Watch.',
  'Any real network. Every address is from documentation ranges.',
]

export function HowItWorks({ open, onClose }: Props) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            className="fixed inset-0 z-40 bg-ink/25"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
            onClick={onClose}
          />
          <motion.aside
            className="fixed top-0 right-0 z-50 h-[100dvh] w-full max-w-[452px] overflow-y-auto border-l border-rule bg-paper-2"
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', stiffness: 300, damping: 34 }}
            role="dialog"
            aria-modal="true"
            aria-label="How CyberPulse works"
          >
            <div className="sticky top-0 z-10 flex items-center justify-between border-b border-rule bg-paper-2/95 px-4 py-3 backdrop-blur">
              <div className="flex items-center gap-2">
                <Logo size={18} />
                <span className="text-[12px] font-semibold tracking-[0.14em] uppercase">
                  How it works
                </span>
              </div>
              <button
                type="button"
                className="btn btn-ghost px-2"
                onClick={onClose}
                aria-label="Close"
              >
                <X size={14} weight="bold" />
              </button>
            </div>

            <div className="px-4 py-4">
              <p className="font-serif text-[16px] leading-[1.4] text-ink">
                Every security product shows alerts. Almost none of them answer the only question a
                small business owner asks: what is actually happening?
              </p>

              <div className="mt-4 space-y-3.5">
                {STEPS.map((s) => (
                  <div key={s.verb} className="border-t border-rule pt-3">
                    <h3 className="text-[13px] font-semibold tracking-[0.02em]">{s.verb}</h3>
                    <p className="mt-1 text-[12px] leading-relaxed text-ink-3">{s.body}</p>
                  </div>
                ))}
              </div>

              <div className="mt-5 border border-rule bg-paper-3/40 p-3">
                <div className="label">What the score is made of</div>
                <div className="mt-2 font-mono text-[11.5px] leading-relaxed text-ink-2">
                  severity points: 5 / 15 / 25 / 40
                  <br />
                  + 10 for every extra attack stage
                  <br />= capped at 100
                </div>
              </div>

              <div className="mt-5">
                <div className="label">Deliberately ignored</div>
                <ul className="mt-2 space-y-1.5">
                  {IGNORED.map((i) => (
                    <li key={i} className="flex gap-2 text-[11.5px] leading-snug text-ink-3">
                      <span className="mt-[6px] h-1 w-1 shrink-0 rounded-full bg-ink-4" />
                      {i}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="mt-5 grid grid-cols-3 gap-2 border-t border-rule pt-4">
                <Stat value="96%" label="of ransomware victims are small or midsize" />
                <Stat value="43%" label="of Indian SMBs have no security team" />
                <Stat value="3 h 15 m" label="of warning before encryption here" />
              </div>
              <p className="mt-2 text-[9.5px] leading-snug text-ink-4">
                Sources: Verizon DBIR 2026, ESET SMB study 2024. The warning figure comes from the
                simulated attack in this demo.
              </p>

              <div className="mt-5 border-t border-rule pt-3">
                <p className="text-[10.5px] leading-relaxed text-ink-3">
                  Team QUADRAX, DEXATHON 2026, team DEX26335. Theme: cybersecurity. Prototype runs
                  entirely in the browser on synthetic logs.
                </p>
              </div>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  )
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <div className="num text-[17px] leading-none">{value}</div>
      <div className="mt-1 text-[9.5px] leading-snug text-ink-3">{label}</div>
    </div>
  )
}
