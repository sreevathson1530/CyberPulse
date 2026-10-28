import { fmtClock } from '../lib/format'
import { ORG } from '../lib/org'
import { LiveDot, Logo } from './ui'

interface Props {
  clock: number
  running: boolean
  onOpenHow: () => void
}

export function Header({ clock, running, onOpenHow }: Props) {
  return (
    <header className="sticky top-0 z-30 border-b border-rule bg-paper/88 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-[1560px] items-center gap-3 px-3 lg:px-5">
        <div className="flex items-center gap-2.5">
          <Logo />
          <div className="leading-none">
            <div className="text-[13px] font-semibold tracking-[0.15em] uppercase">CyberPulse</div>
            <div className="label mt-1 hidden sm:block">Connect the clues</div>
          </div>
        </div>

        <div className="mx-1 hidden h-6 w-px bg-rule md:block" />

        <div className="hidden min-w-0 md:block">
          <div className="truncate text-[12.5px] font-medium">
            {ORG.name}
            <span className="ml-1.5 font-normal text-ink-3">
              {ORG.form}, {ORG.headcount} staff
            </span>
          </div>
          <div className="label mt-0.5 truncate">
            Microsoft 365 · Google Workspace · {ORG.city}
          </div>
        </div>

        <div className="ml-auto flex items-center gap-2">
          <div className="hidden items-center gap-2 border border-rule bg-paper-2 px-2 py-1.5 sm:flex">
            <LiveDot color={running ? '#962b24' : '#7d7463'} />
            <span className="num text-[11.5px] leading-none text-ink-2">{fmtClock(clock)}</span>
            <span className="label leading-none">{running ? 'live' : 'paused'}</span>
          </div>
          <button type="button" className="btn btn-ghost" onClick={onOpenHow}>
            How it works
          </button>
        </div>
      </div>
    </header>
  )
}
