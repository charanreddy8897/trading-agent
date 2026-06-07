import { useState } from 'react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { fmt } from '@/utils/formatters'
import type { DataPoint } from '@/types'
import clsx from 'clsx'

const PERIODS = ['1W', '1M', '3M', '6M', '1Y'] as const
type Period = typeof PERIODS[number]

interface Props { data?: DataPoint[] }

export default function PortfolioChart({ data }: Props) {
  const [period, setPeriod] = useState<Period>('3M')

  // No fallback mock data — if no snapshots exist, show empty state
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[300px] text-slate-500 text-sm">
        No portfolio history yet. Add positions to start tracking.
      </div>
    )
  }

  const chartData = data

  const first = chartData[0]?.value ?? 0
  const last  = chartData.at(-1)?.value ?? 0
  const isUp  = last >= first

  const stroke = isUp ? '#10b981' : '#ef4444'

  return (
    <div className="card p-5 h-full">
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm font-medium text-slate-300">Equity Curve</p>
        <div className="flex gap-1">
          {PERIODS.map(p => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={clsx(
                'px-2.5 py-1 rounded text-xs font-mono transition-colors',
                period === p ? 'bg-blue-600/30 text-blue-400' : 'text-slate-500 hover:text-slate-300',
              )}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={chartData} margin={{ top: 4, right: 0, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor={stroke} stopOpacity={0.3} />
              <stop offset="95%" stopColor={stroke} stopOpacity={0}   />
            </linearGradient>
          </defs>
          <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#475569' }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
          <YAxis tick={{ fontSize: 10, fill: '#475569' }} axisLine={false} tickLine={false}
            tickFormatter={v => `$${(v / 1_000).toFixed(0)}k`} width={52} />
          <Tooltip
            contentStyle={{ background: '#1a2235', border: '1px solid #1e293b', borderRadius: 8, fontSize: 12 }}
            formatter={(v: number) => [fmt.currency(v), 'Value']}
            labelStyle={{ color: '#94a3b8' }}
          />
          <Area type="monotone" dataKey="value" stroke={stroke} strokeWidth={2} fill="url(#areaGrad)" dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
