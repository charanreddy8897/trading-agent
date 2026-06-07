import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import HoldingsTable from '@/components/tables/HoldingsTable'
import { TableSkeleton } from '@/components/shared/LoadingSkeleton'
import { useHoldings, usePortfolioSummary } from '@/hooks/usePortfolio'
import { fmt } from '@/utils/formatters'
import clsx from 'clsx'

export default function Portfolio() {
  const { data: holdings = [], isLoading } = useHoldings()
  const { data: summary } = usePortfolioSummary()

  const waterfallData = [...holdings]
    .sort((a, b) => (b.unrealized_pnl ?? 0) - (a.unrealized_pnl ?? 0))
    .map(h => ({ ticker: h.ticker, pnl: h.unrealized_pnl ?? 0 }))

  const sellSignals = holdings.filter(h =>
    h.stop_loss != null && h.current_price != null &&
    ((h.current_price - h.stop_loss) / h.current_price) < 0.05
  )

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-slate-200">Portfolio</h1>
        <p className="text-slate-500 text-sm mt-0.5">
          {holdings.length} positions · {fmt.currency(summary?.total_value, 0)} total value
        </p>
      </div>

      {/* P&L Waterfall */}
      {waterfallData.length > 0 && (
        <div className="card p-5">
          <p className="text-sm font-medium text-slate-300 mb-4">P&L Breakdown</p>
          <ResponsiveContainer width="100%" height={Math.max(waterfallData.length * 36, 120)}>
            <BarChart data={waterfallData} layout="vertical" margin={{ left: 0, right: 24 }}>
              <XAxis type="number" tick={{ fontSize: 10, fill: '#475569' }}
                tickFormatter={v => `$${(v / 1_000).toFixed(0)}k`} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="ticker" width={52}
                tick={{ fontSize: 11, fill: '#94a3b8', fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: '#1a2235', border: '1px solid #1e293b', borderRadius: 8, fontSize: 12 }}
                formatter={(v: number) => [fmt.currency(v), 'Unrealized P&L']}
              />
              <Bar dataKey="pnl" radius={[0, 4, 4, 0]}>
                {waterfallData.map(d => (
                  <Cell key={d.ticker} fill={d.pnl >= 0 ? '#10b981' : '#ef4444'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Holdings */}
      <div className="card overflow-hidden">
        <div className="px-5 py-3 border-b border-[#1e293b]">
          <h2 className="text-sm font-medium text-slate-300">Holdings</h2>
        </div>
        {isLoading ? <TableSkeleton /> : <HoldingsTable data={holdings} />}
      </div>

      {/* Sell signals */}
      {sellSignals.length > 0 && (
        <div className="card overflow-hidden border-red-500/20">
          <div className="px-5 py-3 border-b border-[#1e293b] bg-red-500/5">
            <h2 className="text-sm font-medium text-red-400">⚠️ Positions Near Stop Loss ({sellSignals.length})</h2>
          </div>
          <div className="divide-y divide-[#1e293b]/40">
            {sellSignals.map(pos => {
              const dist = pos.stop_loss && pos.current_price
                ? ((pos.current_price - pos.stop_loss) / pos.current_price) * 100
                : null
              return (
                <div key={pos.ticker} className="px-5 py-3 flex items-center justify-between">
                  <div>
                    <span className="font-mono font-semibold text-slate-200">{pos.ticker}</span>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Price {fmt.currency(pos.current_price)} → Stop {fmt.currency(pos.stop_loss ?? null)}
                    </p>
                  </div>
                  {dist != null && (
                    <span className={clsx('font-mono text-sm', dist < 3 ? 'text-red-400' : 'text-amber-400')}>
                      {fmt.pct(dist)} to stop
                    </span>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
