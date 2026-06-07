import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import { SECTOR_COLORS, SECTOR_LABELS } from '@/utils/constants'
import type { SectorAllocation } from '@/types'

interface ChartItem { name: string; value: number }

const MOCK: ChartItem[] = [
  { name: 'SEMICONDUCTORS',       value: 35 },
  { name: 'AI_SOFTWARE',          value: 28 },
  { name: 'SPACE_DEFENSE',        value: 15 },
  { name: 'PHYSICAL_AI_ROBOTICS', value: 12 },
  { name: 'MEMORY',               value: 10 },
]

interface Props { data?: SectorAllocation }

export default function SectorDonut({ data }: Props) {
  const chartData: ChartItem[] = data?.sector_pcts
    ? Object.entries(data.sector_pcts)
        .map(([name, value]) => ({ name, value }))
        .filter(d => d.value > 0)
    : MOCK

  return (
    <div className="card p-5 h-full flex flex-col">
      <p className="text-sm font-medium text-slate-300 mb-4">Sector Allocation</p>
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie data={chartData} cx="50%" cy="50%" innerRadius={55} outerRadius={82} paddingAngle={3} dataKey="value">
            {chartData.map(entry => (
              <Cell key={entry.name} fill={SECTOR_COLORS[entry.name] ?? '#475569'} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ background: '#1a2235', border: '1px solid #1e293b', borderRadius: 8, fontSize: 12 }}
            formatter={(v: number, name: string) => [`${v}%`, SECTOR_LABELS[name] ?? name]}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="space-y-1.5 mt-auto">
        {chartData.map(d => (
          <div key={d.name} className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: SECTOR_COLORS[d.name] ?? '#475569' }} />
              <span className="text-slate-400">{SECTOR_LABELS[d.name] ?? d.name}</span>
            </div>
            <span className="font-mono text-slate-300">{d.value}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}
