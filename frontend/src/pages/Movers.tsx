import { useMovers, useUnusualVolume, useNewsFeed } from '@/hooks/useMovers'
import HeatmapGrid from '@/components/charts/HeatmapGrid'
import { EmptyState } from '@/components/shared/LoadingSkeleton'
import { fmt } from '@/utils/formatters'
import { useNavigate } from 'react-router-dom'
import type { Mover } from '@/types'
import clsx from 'clsx'

function MoverCard({ item, type }: { item: Mover; type: 'gainer' | 'loser' }) {
  const navigate = useNavigate()
  const isGain   = type === 'gainer'
  const pct      = item.change_pct ?? 0

  return (
    <div
      onClick={() => navigate(`/analysis/${item.ticker}`)}
      className="flex items-center gap-3 px-4 py-3 hover:bg-[#1a2235] cursor-pointer transition-colors"
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1.5">
          <span className="font-mono font-bold text-slate-200">{item.ticker}</span>
          <span className={clsx('font-mono text-xs', isGain ? 'text-emerald-400' : 'text-red-400')}>
            {fmt.pct(pct)}
          </span>
        </div>
        <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
          <div className={clsx('h-full rounded-full', isGain ? 'bg-emerald-500' : 'bg-red-500')}
            style={{ width: `${Math.min(Math.abs(pct) * 10, 100)}%` }} />
        </div>
      </div>
      <div className="text-right shrink-0">
        <p className="font-mono text-xs text-slate-300">{fmt.currency(item.price)}</p>
        {item.rvol && <p className="text-[10px] text-slate-500">RVol {item.rvol.toFixed(1)}x</p>}
      </div>
    </div>
  )
}

export default function Movers() {
  const { data: movers  } = useMovers(10)
  const { data: unusual = [] } = useUnusualVolume()
  const { data: news = [] } = useNewsFeed()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-slate-200">Movers & Volume</h1>
        <p className="text-slate-500 text-sm mt-0.5">Your universe — today</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="card overflow-hidden">
          <div className="px-5 py-3 border-b border-[#1e293b]">
            <h2 className="text-sm font-medium text-emerald-400">🔥 Top Gainers</h2>
          </div>
          <div className="divide-y divide-[#1e293b]/40">
            {(movers?.gainers ?? []).length === 0
              ? <EmptyState title="No data yet" subtitle="Run the morning pipeline first" />
              : movers!.gainers.map(g => <MoverCard key={g.ticker} item={g} type="gainer" />)
            }
          </div>
        </div>
        <div className="card overflow-hidden">
          <div className="px-5 py-3 border-b border-[#1e293b]">
            <h2 className="text-sm font-medium text-red-400">📉 Top Losers</h2>
          </div>
          <div className="divide-y divide-[#1e293b]/40">
            {(movers?.losers ?? []).length === 0
              ? <EmptyState title="No data yet" subtitle="Run the morning pipeline first" />
              : movers!.losers.map(g => <MoverCard key={g.ticker} item={g} type="loser" />)
            }
          </div>
        </div>
      </div>

      <div className="card p-5">
        <h2 className="text-sm font-medium text-slate-300 mb-4">Sector Performance</h2>
        <HeatmapGrid />
      </div>

      {/* Unusual volume */}
      <div className="card overflow-hidden">
        <div className="px-5 py-3 border-b border-[#1e293b]">
          <h2 className="text-sm font-medium text-slate-300">📊 Unusual Volume (RVol &gt; 2×)</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-[#1e293b]">
              <tr>
                {['Ticker', 'Price', 'Change', 'Volume', 'Avg Vol', 'RVol'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-[10px] font-semibold text-slate-500 uppercase tracking-widest">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e293b]/40">
              {unusual.map(u => (
                <tr key={u.ticker} className="hover:bg-[#1a2235] transition-colors">
                  <td className="px-4 py-3 font-mono font-bold text-slate-200">{u.ticker}</td>
                  <td className="px-4 py-3 font-mono text-slate-300">{fmt.currency(u.price)}</td>
                  <td className={clsx('px-4 py-3 font-mono', (u.change_pct ?? 0) >= 0 ? 'text-emerald-400' : 'text-red-400')}>
                    {fmt.pct(u.change_pct ?? null)}
                  </td>
                  <td className="px-4 py-3 font-mono text-slate-400">{fmt.bigNum(u.volume ?? null)}</td>
                  <td className="px-4 py-3 font-mono text-slate-500">{fmt.bigNum(u.avg_volume ?? null)}</td>
                  <td className="px-4 py-3"><span className="font-mono text-cyan-400 font-semibold">{u.rvol?.toFixed(1)}x</span></td>
                </tr>
              ))}
              {unusual.length === 0 && (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-slate-500">No unusual volume today</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* News */}
      {news.length > 0 && (
        <div className="card overflow-hidden">
          <div className="px-5 py-3 border-b border-[#1e293b]">
            <h2 className="text-sm font-medium text-slate-300">📰 Latest News</h2>
          </div>
          <div className="divide-y divide-[#1e293b]/40 max-h-80 overflow-y-auto">
            {news.slice(0, 20).map((n, i) => (
              <div key={i} className="px-5 py-3 flex items-start gap-3">
                <span className="font-mono text-xs font-bold text-slate-500 shrink-0 pt-0.5 w-12">{n.ticker}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-300 line-clamp-2">{n.headline}</p>
                  <p className="text-[10px] text-slate-600 mt-1">{n.source} · {fmt.shortDate(n.published_at)}</p>
                </div>
                {n.sentiment != null && (
                  <span className={clsx('shrink-0 font-mono text-xs pt-0.5',
                    n.sentiment > 0 ? 'text-emerald-400' : n.sentiment < 0 ? 'text-red-400' : 'text-slate-500')}>
                    {n.sentiment > 0 ? '▲' : n.sentiment < 0 ? '▼' : '─'}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
