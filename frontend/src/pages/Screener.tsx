import { useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import ScreenerTable from '@/components/tables/ScreenerTable'
import { TableSkeleton } from '@/components/shared/LoadingSkeleton'
import { useScreener } from '@/hooks/useScreener'
import { SECTOR_LABELS, ALL_SECTORS } from '@/utils/constants'
import type { ScreenerRow } from '@/types'

interface Bucket { range: string; count: number; color: string }

function buildHistogram(data: ScreenerRow[]): Bucket[] {
  const buckets: Bucket[] = [
    { range: '0–29',  count: 0, color: '#ef4444' },
    { range: '30–49', count: 0, color: '#f59e0b' },
    { range: '50–69', count: 0, color: '#94a3b8' },
    { range: '70–84', count: 0, color: '#10b981' },
    { range: '85+',   count: 0, color: '#06b6d4' },
  ]
  data.forEach(d => {
    if      (d.total < 30) buckets[0].count++
    else if (d.total < 50) buckets[1].count++
    else if (d.total < 70) buckets[2].count++
    else if (d.total < 85) buckets[3].count++
    else                   buckets[4].count++
  })
  return buckets
}

export default function Screener() {
  const [sector,   setSector]   = useState('all')
  const [minScore, setMinScore] = useState(0)

  const { data = [], isLoading } = useScreener(sector, minScore)
  const histogram = buildHistogram(data)

  return (
    <div className="space-y-6">
      {/* Header + filters */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-lg font-semibold text-slate-200">Conviction Screener</h1>
          <p className="text-slate-500 text-sm mt-0.5">{data.length} stocks ranked</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={sector} onChange={e => setSector(e.target.value)}
            className="bg-[#111827] border border-[#1e293b] text-slate-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-blue-500 cursor-pointer"
          >
            <option value="all">All Sectors</option>
            {ALL_SECTORS.map(s => <option key={s} value={s}>{SECTOR_LABELS[s]}</option>)}
          </select>
          <select
            value={minScore} onChange={e => setMinScore(Number(e.target.value))}
            className="bg-[#111827] border border-[#1e293b] text-slate-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-blue-500 cursor-pointer"
          >
            <option value={0}>All Scores</option>
            <option value={50}>50+</option>
            <option value={70}>70+</option>
            <option value={85}>85+</option>
          </select>
        </div>
      </div>

      {/* Score distribution */}
      <div className="card p-5">
        <p className="text-xs text-slate-500 uppercase tracking-widest mb-3 font-mono">Score Distribution</p>
        <ResponsiveContainer width="100%" height={80}>
          <BarChart data={histogram} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
            <XAxis dataKey="range" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
            <YAxis hide />
            <Tooltip
              contentStyle={{ background: '#1a2235', border: '1px solid #1e293b', borderRadius: 8, fontSize: 12 }}
              formatter={(v: number) => [v, 'Stocks']}
            />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {histogram.map(b => <Cell key={b.range} fill={b.color} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {isLoading ? <TableSkeleton /> : <ScreenerTable data={data} />}
      </div>
    </div>
  )
}
