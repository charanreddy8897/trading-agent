import { DollarSign, TrendingUp, Layers, Bell } from 'lucide-react'
import MetricCard    from '@/components/shared/MetricCard'
import PortfolioChart from '@/components/charts/PortfolioChart'
import SectorDonut   from '@/components/charts/SectorDonut'
import MoversTable   from '@/components/tables/MoversTable'
import { CardSkeleton } from '@/components/shared/LoadingSkeleton'
import { usePortfolioSummary, useSectorAllocation, useAlerts } from '@/hooks/usePortfolio'
import { useMovers } from '@/hooks/useMovers'
import { fmt } from '@/utils/formatters'
import { SEVERITY_STYLES } from '@/utils/constants'
import clsx from 'clsx'

export default function Dashboard() {
  const { data: summary, isLoading } = usePortfolioSummary()
  const { data: alloc }  = useSectorAllocation()
  const { data: movers } = useMovers(5)
  const { data: alerts, dismiss } = useAlerts()

  const activeAlerts = alerts?.filter(a => !a.dismissed) ?? []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-slate-200">Dashboard</h1>
        <p className="text-slate-500 text-sm mt-0.5">
          {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
        </p>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-4 gap-4">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} />)
        ) : (
          <>
            <MetricCard label="Total Value"    value={fmt.currency(summary?.total_value, 0)}
              sub={`P&L ${fmt.currency(summary?.total_pnl)}`}
              subColor={fmt.pnlColor(summary?.total_pnl)} icon={DollarSign} iconColor="text-blue-400" />
            <MetricCard label="Today's P&L"   value={fmt.currency(summary?.daily_change)}
              sub={fmt.pct(summary?.daily_pct)}
              subColor={fmt.pctColor(summary?.daily_pct)} icon={TrendingUp}
              iconColor={(summary?.daily_pct ?? 0) >= 0 ? 'text-emerald-400' : 'text-red-400'} />
            <MetricCard label="Positions"      value={summary?.position_count ?? 0}
              sub="Open holdings" icon={Layers} iconColor="text-violet-400" />
            <MetricCard label="Active Alerts"  value={activeAlerts.length}
              sub={`${activeAlerts.filter(a => a.severity === 'critical').length} critical`}
              subColor={activeAlerts.some(a => a.severity === 'critical') ? 'text-red-400' : 'text-slate-500'}
              icon={Bell} iconColor="text-amber-400" />
          </>
        )}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-3 gap-4 min-h-[320px]">
        <div className="col-span-2"><PortfolioChart /></div>
        <div><SectorDonut data={alloc} /></div>
      </div>

      {/* Movers + Alerts */}
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2 card overflow-hidden">
          <div className="px-5 py-3 border-b border-[#1e293b]">
            <h2 className="text-sm font-medium text-slate-300">Top Movers <span className="text-slate-600 text-xs">(your universe)</span></h2>
          </div>
          <MoversTable gainers={movers?.gainers ?? []} losers={movers?.losers ?? []} />
        </div>

        <div className="card overflow-hidden">
          <div className="px-5 py-3 border-b border-[#1e293b] flex items-center justify-between">
            <h2 className="text-sm font-medium text-slate-300">Alerts</h2>
            {activeAlerts.length > 0 && (
              <span className="tag bg-red-500/20 text-red-400 border border-red-500/30">{activeAlerts.length}</span>
            )}
          </div>
          <div className="max-h-80 overflow-y-auto divide-y divide-[#1e293b]/40">
            {activeAlerts.length === 0 ? (
              <p className="px-5 py-8 text-slate-500 text-sm text-center">No active alerts ✅</p>
            ) : (
              activeAlerts.map(a => {
                const c = SEVERITY_STYLES[a.severity] ?? SEVERITY_STYLES.info
                return (
                  <div key={a.id} className={clsx('px-4 py-3 flex items-start gap-3', c.bg)}>
                    <span className="text-sm mt-0.5 shrink-0">{c.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono text-xs font-semibold text-slate-300">{a.ticker}</span>
                        <span className={clsx('tag border text-[10px]', c.text, c.border)}>{a.alert_type}</span>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">{a.message}</p>
                    </div>
                    <button onClick={() => dismiss(a.id)} className="text-slate-700 hover:text-slate-400 text-xs shrink-0 mt-0.5">✕</button>
                  </div>
                )
              })
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
