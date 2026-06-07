import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronRight, ChevronDown } from 'lucide-react'
import { fmt } from '@/utils/formatters'
import type { Position } from '@/types'
import clsx from 'clsx'

function ExpandedRow({ pos }: { pos: Position }) {
  const distPct = pos.stop_loss && pos.current_price
    ? ((pos.current_price - pos.stop_loss) / pos.current_price) * 100
    : null

  return (
    <div className="grid grid-cols-3 gap-6 px-6 py-4 bg-[#0d1321] border-t border-[#1e293b] text-xs">
      <div className="space-y-2.5">
        <Kv label="Entry Date"  value={fmt.date(pos.entry_date ?? null)} />
        <Kv label="Stop Loss"   value={fmt.currency(pos.stop_loss ?? null)} />
        <Kv label="Sector"      value={pos.sector} />
      </div>
      <div className="space-y-2.5">
        <Kv label="Tranche 1" value={pos.tranche1_filled ? '✅ Filled' : '⬜ Pending'} />
        <Kv label="Tranche 2" value={pos.tranche2_filled ? '✅ Filled' : '⬜ Pending'} />
      </div>
      <div className="space-y-2.5">
        {distPct != null && (
          <Kv
            label="Distance to Stop"
            value={fmt.pct(distPct)}
            valueClass={distPct < 3 ? 'text-red-400' : distPct < 7 ? 'text-amber-400' : 'text-slate-300'}
          />
        )}
      </div>
    </div>
  )
}

interface KvProps { label: string; value: string | null; valueClass?: string }

function Kv({ label, value, valueClass = 'text-slate-300' }: KvProps) {
  return (
    <div>
      <p className="text-[9px] text-slate-600 uppercase tracking-wider">{label}</p>
      <p className={clsx('font-mono mt-0.5', valueClass)}>{value ?? '—'}</p>
    </div>
  )
}

const HEADERS = ['Ticker', 'Shares', 'Avg Cost', 'Price', 'Mkt Value', 'P&L ($)', 'P&L (%)', 'Sector', '']

export default function HoldingsTable({ data = [] }: { data: Position[] }) {
  const navigate  = useNavigate()
  const [exp, setExp] = useState<string | null>(null)

  const toggle = (ticker: string) => setExp(e => e === ticker ? null : ticker)

  const nearStop = (pos: Position) =>
    pos.stop_loss != null && pos.current_price != null &&
    ((pos.current_price - pos.stop_loss) / pos.current_price) < 0.03

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="border-b border-[#1e293b]">
          <tr>
            {HEADERS.map(h => (
              <th key={h} className="px-4 py-3 text-left text-[10px] font-semibold text-slate-500 uppercase tracking-widest whitespace-nowrap">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map(pos => (
            <>
              <tr key={pos.ticker}
                onClick={() => toggle(pos.ticker)}
                className={clsx(
                  'border-b border-[#1e293b]/50 hover:bg-[#1a2235] cursor-pointer transition-colors',
                  nearStop(pos) && 'border-l-2 border-l-red-500/70',
                )}>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    {nearStop(pos) && <span className="text-xs">🛑</span>}
                    <span
                      onClick={e => { e.stopPropagation(); navigate(`/analysis/${pos.ticker}`) }}
                      className="font-mono font-semibold text-slate-200 hover:text-blue-400 cursor-pointer transition-colors"
                    >
                      {pos.ticker}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3 font-mono text-slate-400">{pos.shares}</td>
                <td className="px-4 py-3 font-mono text-slate-400">{fmt.currency(pos.avg_cost)}</td>
                <td className="px-4 py-3 font-mono text-slate-200">{fmt.currency(pos.current_price)}</td>
                <td className="px-4 py-3 font-mono text-slate-200">{fmt.currency(pos.market_value, 0)}</td>
                <td className={clsx('px-4 py-3 font-mono', fmt.pnlColor(pos.unrealized_pnl))}>{fmt.currency(pos.unrealized_pnl)}</td>
                <td className={clsx('px-4 py-3 font-mono', fmt.pctColor(pos.unrealized_pct))}>{fmt.pct(pos.unrealized_pct)}</td>
                <td className="px-4 py-3 text-xs text-slate-500">{pos.sector}</td>
                <td className="px-4 py-3 text-slate-600">
                  {exp === pos.ticker ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                </td>
              </tr>
              {exp === pos.ticker && (
                <tr key={`${pos.ticker}-exp`}>
                  <td colSpan={9} className="p-0"><ExpandedRow pos={pos} /></td>
                </tr>
              )}
            </>
          ))}
          {data.length === 0 && (
            <tr><td colSpan={9} className="px-4 py-12 text-center text-slate-500">No positions · sync your portfolio first</td></tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
