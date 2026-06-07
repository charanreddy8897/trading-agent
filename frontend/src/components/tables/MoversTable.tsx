import { useNavigate } from 'react-router-dom'
import { fmt } from '@/utils/formatters'
import { SECTOR_LABELS } from '@/utils/constants'
import type { Mover } from '@/types'
import clsx from 'clsx'

interface RowProps { item: Mover; type: 'gainer' | 'loser' }

function MoverRow({ item, type }: RowProps) {
  const navigate = useNavigate()
  const isGain   = type === 'gainer'
  const pct      = item.change_pct ?? 0
  const barWidth = Math.min(Math.abs(pct) * 8, 100)

  return (
    <div
      onClick={() => navigate(`/analysis/${item.ticker}`)}
      className="flex items-center gap-3 px-4 py-3 hover:bg-[#1a2235] cursor-pointer transition-colors"
    >
      <div className="w-14 shrink-0">
        <p className="font-mono text-sm font-semibold text-slate-200">{item.ticker}</p>
        {item.sector && <p className="text-[10px] text-slate-500 truncate">{SECTOR_LABELS[item.sector] ?? item.sector}</p>}
      </div>
      <div className="flex-1 flex items-center gap-2 min-w-0">
        <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
          <div className={clsx('h-full rounded-full', isGain ? 'bg-emerald-500' : 'bg-red-500')} style={{ width: `${barWidth}%` }} />
        </div>
        <span className={clsx('font-mono text-xs w-14 text-right shrink-0', isGain ? 'text-emerald-400' : 'text-red-400')}>
          {fmt.pct(pct)}
        </span>
      </div>
      <div className="text-right shrink-0 w-20">
        <p className="font-mono text-xs text-slate-300">{fmt.currency(item.price)}</p>
        {item.rvol && <p className="text-[10px] text-slate-500">RVol {item.rvol.toFixed(1)}x</p>}
      </div>
    </div>
  )
}

interface Props { gainers: Mover[]; losers: Mover[] }

export default function MoversTable({ gainers, losers }: Props) {
  return (
    <div className="grid grid-cols-2 divide-x divide-[#1e293b]">
      <div>
        <p className="px-4 py-2 text-xs font-semibold text-emerald-400 uppercase tracking-widest border-b border-[#1e293b]">
          🔥 Gainers
        </p>
        <div className="divide-y divide-[#1e293b]/40">
          {gainers.slice(0, 5).map(g => <MoverRow key={g.ticker} item={g} type="gainer" />)}
          {gainers.length === 0 && <p className="px-4 py-6 text-slate-500 text-sm">No data yet</p>}
        </div>
      </div>
      <div>
        <p className="px-4 py-2 text-xs font-semibold text-red-400 uppercase tracking-widest border-b border-[#1e293b]">
          📉 Losers
        </p>
        <div className="divide-y divide-[#1e293b]/40">
          {losers.slice(0, 5).map(g => <MoverRow key={g.ticker} item={g} type="loser" />)}
          {losers.length === 0 && <p className="px-4 py-6 text-slate-500 text-sm">No data yet</p>}
        </div>
      </div>
    </div>
  )
}
