import { RefreshCw, Bell } from 'lucide-react'
import { usePortfolioSummary, useAlerts } from '@/hooks/usePortfolio'
import { fmt } from '@/utils/formatters'
import clsx from 'clsx'

export default function Header() {
  const { data: summary } = usePortfolioSummary()
  const { data: alerts }  = useAlerts()
  const alertCount = alerts?.filter(a => !a.dismissed).length ?? 0
  const dailyPct   = summary?.daily_pct ?? 0

  return (
    <header className="fixed top-0 left-52 right-0 h-16 z-30 flex items-center justify-between px-6 border-b border-[#1e293b] bg-[#0d1321]/90 backdrop-blur-sm">
      <div className="flex items-center gap-6">
        <div>
          <p className="text-[9px] text-slate-600 uppercase tracking-widest font-mono">Portfolio Value</p>
          <div className="flex items-baseline gap-2 mt-0.5">
            <span className="text-xl font-semibold font-mono text-slate-100">
              {fmt.currency(summary?.total_value, 0)}
            </span>
            <span className={clsx('text-sm font-mono', fmt.pctColor(dailyPct))}>
              {fmt.pct(dailyPct)}
            </span>
          </div>
        </div>
        <div className="h-8 w-px bg-[#1e293b]" />
        <div className="flex items-center gap-5 text-xs">
          <Stat label="Today P&L"  value={fmt.currency(summary?.daily_change)} positive={(summary?.daily_change ?? 0) >= 0} />
          <Stat label="Positions"  value={String(summary?.position_count ?? '—')} />
          <Stat label="Total P&L"  value={fmt.currency(summary?.total_pnl)} positive={(summary?.total_pnl ?? 0) >= 0} />
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button className="relative p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-[#1a2235] transition-colors">
          <Bell size={16} />
          {alertCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 rounded-full text-[9px] font-bold text-white flex items-center justify-center">
              {alertCount}
            </span>
          )}
        </button>
        <button className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-[#1a2235] transition-colors">
          <RefreshCw size={15} />
        </button>
        <div className="h-8 w-px bg-[#1e293b] mx-1" />
        <div className="w-8 h-8 rounded-full bg-blue-600/30 flex items-center justify-center text-blue-400 text-xs font-bold select-none">
          CR
        </div>
      </div>
    </header>
  )
}

interface StatProps { label: string; value: string; positive?: boolean }

function Stat({ label, value, positive }: StatProps) {
  return (
    <div>
      <p className="text-[9px] text-slate-600 uppercase tracking-wider">{label}</p>
      <p className={clsx(
        'font-mono font-medium mt-0.5',
        positive === true  ? 'text-emerald-400' :
        positive === false ? 'text-red-400'     : 'text-slate-300',
      )}>
        {value}
      </p>
    </div>
  )
}
