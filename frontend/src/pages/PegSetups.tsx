import { useNavigate } from 'react-router-dom'
import { usePegSetups, usePegHistory } from '@/hooks/useMovers'
import { EmptyState } from '@/components/shared/LoadingSkeleton'
import { SECTOR_LABELS, SECTOR_COLORS } from '@/utils/constants'
import { fmt } from '@/utils/formatters'
import type { PegSetup } from '@/types'
import clsx from 'clsx'

interface StatProps { label: string; value: string | null; color?: string }

function Stat({ label, value, color = 'text-slate-300' }: StatProps) {
  return (
    <div>
      <p className="text-[10px] text-slate-600 uppercase tracking-wider">{label}</p>
      <p className={clsx('font-mono text-sm font-semibold mt-0.5', color)}>{value ?? '—'}</p>
    </div>
  )
}

function PegCard({ peg }: { peg: PegSetup }) {
  const navigate = useNavigate()
  const color    = SECTOR_COLORS[peg.sector ?? ''] ?? '#3b82f6'
  const distPct  = peg.current_price && peg.peg_low
    ? ((peg.current_price - peg.peg_low) / peg.peg_low) * 100
    : null

  return (
    <div
      onClick={() => navigate(`/analysis/${peg.ticker}`)}
      className="card p-5 cursor-pointer hover:border-blue-500/50 hover:shadow-xl transition-all group"
    >
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono font-bold text-xl text-slate-100 group-hover:text-blue-400 transition-colors">
              {peg.ticker}
            </span>
            {peg.sector && (
              <span className="tag text-[10px]" style={{ background: `${color}20`, color }}>
                {SECTOR_LABELS[peg.sector] ?? peg.sector}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-1">PEG date: {fmt.date(peg.peg_date)}</p>
        </div>
        <span className="text-2xl">⚡</span>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <Stat label="Gap %"        value={`+${peg.gap_pct?.toFixed(1)}%`}        color="text-emerald-400" />
        <Stat label="Vol Multiple" value={`${peg.volume_multiple?.toFixed(1)}x`} color="text-cyan-400"    />
        <Stat label="PEG Low"      value={fmt.currency(peg.peg_low)} />
        <Stat label="Current"      value={fmt.currency(peg.current_price ?? null)} />
      </div>

      {distPct != null && (
        <div className="mb-3 space-y-1">
          <div className="flex justify-between text-[10px]">
            <span className="text-slate-600">PEG Low (support)</span>
            <span className="text-emerald-400 font-mono">+{distPct.toFixed(1)}% above</span>
          </div>
          <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div className="h-full bg-emerald-500 rounded-full transition-all"
              style={{ width: `${Math.min(distPct * 4, 100)}%` }} />
          </div>
        </div>
      )}

      {peg.entry_zone && (
        <div className="px-3 py-2 rounded-lg bg-blue-500/10 border border-blue-500/20">
          <p className="text-xs text-blue-400">
            <span className="font-semibold">Entry zone:</span> {peg.entry_zone}
          </p>
        </div>
      )}
    </div>
  )
}

export default function PegSetups() {
  const { data: pegs    = [], isLoading: loadPegs    } = usePegSetups()
  const { data: history = [], isLoading: loadHistory } = usePegHistory()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-slate-200">⚡ Power Earnings Gaps</h1>
        <p className="text-slate-500 text-sm mt-0.5">{pegs.length} active setups</p>
      </div>

      {pegs.length === 0 && !loadPegs ? (
        <EmptyState icon="⚡" title="No active PEG setups"
          subtitle="PEGs appear after gap-ups on earnings with 2x+ volume" />
      ) : (
        <div className="grid grid-cols-3 gap-4">
          {pegs.map(p => <PegCard key={`${p.ticker}-${p.peg_date}`} peg={p} />)}
        </div>
      )}

      {/* History table */}
      <div className="card overflow-hidden">
        <div className="px-5 py-3 border-b border-[#1e293b]">
          <h2 className="text-sm font-medium text-slate-300">PEG History</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-[#1e293b]">
              <tr>
                {['Ticker', 'PEG Date', 'Gap %', 'Vol Multiple', 'Status'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-[10px] font-semibold text-slate-500 uppercase tracking-widest">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e293b]/40">
              {history.map((h, i) => (
                <tr key={i} className="hover:bg-[#1a2235] transition-colors">
                  <td className="px-4 py-3 font-mono font-semibold text-slate-200">{h.ticker}</td>
                  <td className="px-4 py-3 font-mono text-slate-400">{fmt.date(h.peg_date)}</td>
                  <td className="px-4 py-3 font-mono text-emerald-400">+{h.gap_pct?.toFixed(1)}%</td>
                  <td className="px-4 py-3 font-mono text-cyan-400">{h.volume_multiple?.toFixed(1)}x</td>
                  <td className="px-4 py-3">
                    <span className={clsx('tag border', h.gap_filled
                      ? 'bg-red-500/20 text-red-400 border-red-500/30'
                      : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30')}>
                      {h.gap_filled ? 'Gap Filled' : 'Intact ✅'}
                    </span>
                  </td>
                </tr>
              ))}
              {history.length === 0 && !loadHistory && (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-slate-500">No PEG history yet</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
