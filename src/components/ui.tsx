import type { Band, Severity } from '../lib/types'

export const SEVERITY_HEX: Record<Severity, string> = {
  low: '#7d7463',
  medium: '#a9680b',
  high: '#b4461f',
  critical: '#962b24',
}

export const SEVERITY_LABEL: Record<Severity, string> = {
  low: 'Low',
  medium: 'Medium',
  high: 'High',
  critical: 'Critical',
}

export const BAND_HEX: Record<Band, string> = {
  clear: '#7d7463',
  watch: '#a9680b',
  suspicious: '#b4461f',
  likely: '#962b24',
}

export function SeverityTag({ severity }: { severity: Severity }) {
  return (
    <span
      className="inline-flex shrink-0 items-center gap-1.5 border border-rule px-1.5 py-[3px] font-mono text-[9.5px] leading-none tracking-[0.1em] uppercase"
      style={{ color: SEVERITY_HEX[severity] }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: SEVERITY_HEX[severity] }} />
      {SEVERITY_LABEL[severity]}
    </span>
  )
}

export function LiveDot({ color = '#962b24' }: { color?: string }) {
  return (
    <span className="relative inline-flex h-1.5 w-1.5 shrink-0">
      <span
        className="absolute inset-0 rounded-full"
        style={{ background: color, animation: 'pulse-dot 2.4s ease-in-out infinite' }}
      />
    </span>
  )
}

export function Logo({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 22 22" aria-hidden="true" className="shrink-0">
      <rect x="0.5" y="0.5" width="21" height="21" rx="2" fill="#191712" />
      <path
        d="M3.6 11.4h3.1l1.7-4.4 2.7 8.8 1.7-4.4h4.6"
        stroke="#f4f0e6"
        strokeWidth="1.35"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export function RuleGlyph({ className = '' }: { className?: string }) {
  return (
    <svg viewBox="0 0 12 12" className={className} aria-hidden="true">
      <path
        d="M2 6h2.1l1.1-2.8 1.7 5.6 1.1-2.8H10"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.1"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
