import { Treemap, ResponsiveContainer, Tooltip } from 'recharts'
import { useSectorAllocation } from '@/hooks/usePortfolio'
import { useScreener } from '@/hooks/useScreener'
import HeatmapGrid from '@/components/charts/HeatmapGrid'
import { SECTOR_COLORS, SECTOR_LABELS } from '@/utils/constants'
import type { SectorStat } from '@/types'
import clsx from 'clsx'

interface TreeNode { name: string; size: number; sector: string; change: number }

const MOCK_TREE: TreeNode[] = [
  { name: 'NVDA', size: 350, sector: 'SEMICONDUCTORS', change: 1.2  },
  { name: 'PLTR', size: 200, sector: 'AI_SOFTWARE',    change: 5.1  },
  { name: 'AMD',  size: 180, sector: 'SEMICONDUCTORS', change: -0.3 },
  { name: 'ARM',  size: 160, sector: 'SEMICONDUCTORS', change: 3.7  },
  { name: 'RKLB', size: 120, sector: 'SPACE_DEFENSE',  change: 8.4  },
  { name: 'MSFT', size: 300, sector: 'AI_SOFTWARE',    change: 0.8  },
  { name: 'MU',   size: 140, sector: 'MEMORY',         change: -1.2 },
  { name: 'TER',  size: 100, sector: 'SEMICONDUCTORS', change: 2.1  },
]

interface CellProps {
  x?: number; y?: number; width?: number; height?: number
  name?: string; change?: number; sector?: string
}

function TreeCell({ x = 0, y = 0, width = 0, height = 0, name, change = 0, sector }: CellProps) {
  const fill    = SECTOR_COLORS[sector ?? ''] ?? '#475569'
  const opacity = Math.max(0.3, Math.min(1, 0.5 + Math.abs(change) * 0.1))
  return (
    <g>
      <rect x={x} y={y} width={width} height={height} fill={fill} fillOpacity={opacity}
        stroke="#0a0e17" strokeWidth={2} rx={4} />
      {width > 50 && height > 30 && (
        <>
          <text x={x + width / 2} y={y + height / 2 - 7} textAnchor="middle"
            fill="white" fontSize={Math.min(13, width / 5)} fontFamily="JetBrains Mono" fontWeight="600">
            {name}
          </text>
          <text x={x + width / 2} y={y + height / 2 + 10} textAnchor="middle"
            fill="rgba(255,255,255,0.75)" fontSize={Math.min(11, width / 6)} fontFamily="JetBrains Mono">
            {change >= 0 ? '+' : ''}{change.toFixed(1)}%
          </text>
        </>
      )}
    </g>
  )
}

export default function SectorView() {
  const { data: alloc }    = useSectorAllocation()
  const { data: ranked = [] } = useScreener()

  const sectorMap: Record<string, { scores: number[]; stage2: number; pegs: number }> = {}
  ranked.forEach(r => {
    if (!sectorMap[r.sector]) sectorMap[r.sector] = { scores: [], stage2: 0, pegs: 0 }
    sectorMap[r.sector].scores.push(r.total)
    if (r.stage === 2)  sectorMap[r.sector].stage2++
    if (r.peg_active)   sectorMap[r.sector].pegs++
  })

  const sectorRows: SectorStat[] = Object.entries(sectorMap)
    .map(([sector, v]) => ({
      sector,
      avgScore:  Math.round(v.scores.reduce((a, b) => a + b, 0) / v.scores.length),
      stage2Pct: Math.round((v.stage2 / v.scores.length) * 100),
      pegCount:  v.pegs,
      count:     v.scores.length,
    }))
    .sort((a, b) => b.avgScore - a.avgScore)

  const exposureRows = alloc?.sector_pcts
    ? Object.entries(alloc.sector_pcts).map(([s, pct]) => ({ sector: s, pct }))
    : []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-slate-200">Sector Rotation</h1>
        <p className="text-slate-500 text-sm mt-0.5">Market heatmap and sector leadership</p>
      </div>

      {/* Treemap */}
      <div className="card p-5">
        <p className="text-sm font-medium text-slate-300 mb-4">Market Heatmap</p>
        <ResponsiveContainer width="100%" height={320}>
          <Treemap data={MOCK_TREE} dataKey="size" content={<TreeCell />}>
            <Tooltip
              contentStyle={{ background: '#1a2235', border: '1px solid #1e293b', borderRadius: 8, fontSize: 12 }}
              formatter={(_v: unknown, _n: string, props: { payload?: TreeNode }) =>
                [`${(props.payload?.change ?? 0) >= 0 ? '+' : ''}${props.payload?.change?.toFixed(1)}%`, props.payload?.name ?? '']
              }
            />
          </Treemap>
        </ResponsiveContainer>
        <div className="flex flex-wrap gap-4 mt-4">
          {Object.entries(SECTOR_COLORS).map(([k, color]) => (
            <div key={k} className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-sm" style={{ background: color }} />
              <span className="text-xs text-slate-500">{SECTOR_LABELS[k]}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Daily change heatmap */}
      <div className="card p-5">
        <p className="text-sm font-medium text-slate-300 mb-4">Today's Sector Performance</p>
        <HeatmapGrid />
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Sector leadership */}
        <div className="card overflow-hidden">
          <div className="px-5 py-3 border-b border-[#1e293b]">
            <h2 className="text-sm font-medium text-slate-300">Sector Leadership</h2>
          </div>
          <table className="w-full text-sm">
            <thead className="border-b border-[#1e293b]">
              <tr>
                {['Sector', 'Avg Score', 'Stage 2%', 'PEGs'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-[10px] font-semibold text-slate-500 uppercase tracking-widest">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e293b]/40">
              {sectorRows.map(r => (
                <tr key={r.sector} className="hover:bg-[#1a2235] transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full shrink-0" style={{ background: SECTOR_COLORS[r.sector] ?? '#475569' }} />
                      <span className="text-xs text-slate-300">{SECTOR_LABELS[r.sector] ?? r.sector}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={clsx('font-mono font-bold',
                      r.avgScore >= 70 ? 'text-emerald-400' : r.avgScore >= 50 ? 'text-amber-400' : 'text-slate-400')}>
                      {r.avgScore}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-300">{r.stage2Pct}%</td>
                  <td className="px-4 py-3 font-mono text-xs">
                    {r.pegCount > 0 ? <span className="text-amber-400">⚡{r.pegCount}</span> : <span className="text-slate-700">—</span>}
                  </td>
                </tr>
              ))}
              {sectorRows.length === 0 && (
                <tr><td colSpan={4} className="px-4 py-8 text-center text-slate-500">Run screener first</td></tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Exposure bars */}
        <div className="card p-5">
          <h2 className="text-sm font-medium text-slate-300 mb-4">Exposure vs 40% Limit</h2>
          <div className="space-y-4">
            {exposureRows.length === 0 ? (
              <p className="text-slate-500 text-sm">Sync portfolio to see exposure</p>
            ) : exposureRows.map(r => (
              <div key={r.sector}>
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="text-slate-400">{SECTOR_LABELS[r.sector] ?? r.sector}</span>
                  <span className={clsx('font-mono', r.pct > 40 ? 'text-red-400' : r.pct > 30 ? 'text-amber-400' : 'text-slate-300')}>
                    {r.pct}% / 40%
                  </span>
                </div>
                <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div className={clsx('h-full rounded-full transition-all',
                    r.pct > 40 ? 'bg-red-500' : r.pct > 30 ? 'bg-amber-500' : 'bg-blue-500')}
                    style={{ width: `${Math.min((r.pct / 40) * 100, 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
          {(alloc?.warnings ?? []).length > 0 && (
            <div className="mt-4 space-y-2 pt-4 border-t border-[#1e293b]">
              {alloc!.warnings.map((w, i) => (
                <p key={i} className="text-xs text-amber-400 flex items-start gap-2">
                  <span className="shrink-0">⚠️</span>{w}
                </p>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
