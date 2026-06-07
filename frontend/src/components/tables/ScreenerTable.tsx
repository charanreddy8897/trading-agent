import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react'
import { ActionBadge, StageBadge } from '@/components/shared/Badge'
import ConvictionBar from '@/components/charts/ConvictionBar'
import { fmt } from '@/utils/formatters'
import { SECTOR_LABELS } from '@/utils/constants'
import type { ScreenerRow } from '@/types'
import clsx from 'clsx'

type SortField = keyof ScreenerRow
interface Sort { field: SortField; dir: 'asc' | 'desc' }

interface ThProps { label: string; field: SortField; sort: Sort; onSort: (f: SortField) => void }

function Th({ label, field, sort, onSort }: ThProps) {
  const active = sort.field === field
  return (
    <th onClick={() => onSort(field)}
      className="px-4 py-3 text-left text-[10px] font-semibold text-slate-500 uppercase tracking-widest cursor-pointer hover:text-slate-300 select-none whitespace-nowrap">
      <div className="flex items-center gap-1">
        {label}
        {active
          ? sort.dir === 'desc' ? <ChevronDown size={11} className="text-blue-400" /> : <ChevronUp size={11} className="text-blue-400" />
          : <ChevronsUpDown size={11} className="text-slate-700" />}
      </div>
    </th>
  )
}

export default function ScreenerTable({ data = [] }: { data: ScreenerRow[] }) {
  const navigate = useNavigate()
  const [sort, setSort] = useState<Sort>({ field: 'total', dir: 'desc' })

  const onSort = (field: SortField) =>
    setSort(s => ({ field, dir: s.field === field && s.dir === 'desc' ? 'asc' : 'desc' }))

  const sorted = [...data].sort((a, b) => {
    const av = a[sort.field] as number ?? 0
    const bv = b[sort.field] as number ?? 0
    return sort.dir === 'desc' ? bv - av : av - bv
  })

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="border-b border-[#1e293b] bg-[#111827] sticky top-0 z-10">
          <tr>
            <th className="px-4 py-3 text-left text-[10px] font-semibold text-slate-600 uppercase w-8">#</th>
            <Th label="Ticker"  field="ticker"        sort={sort} onSort={onSort} />
            <Th label="Score"   field="total"         sort={sort} onSort={onSort} />
            <th className="px-4 py-3 text-left text-[10px] font-semibold text-slate-500 uppercase tracking-widest min-w-[140px]">Breakdown</th>
            <Th label="Action"  field="action"        sort={sort} onSort={onSort} />
            <Th label="Stage"   field="stage"         sort={sort} onSort={onSort} />
            <Th label="ADR%"    field="adr_pct"       sort={sort} onSort={onSort} />
            <Th label="ATR Ext" field="atr_extension" sort={sort} onSort={onSort} />
            <Th label="RVol"    field="rvol"          sort={sort} onSort={onSort} />
            <th className="px-4 py-3 text-left text-[10px] font-semibold text-slate-500 uppercase tracking-widest">PEG</th>
            <Th label="Sector"  field="sector"        sort={sort} onSort={onSort} />
          </tr>
        </thead>
        <tbody className="divide-y divide-[#1e293b]/40">
          {sorted.map((row, i) => (
            <tr key={row.ticker}
              onClick={() => navigate(`/analysis/${row.ticker}`)}
              className="hover:bg-[#1a2235] cursor-pointer transition-colors group">
              <td className="px-4 py-3 text-slate-600 font-mono text-xs">{i + 1}</td>
              <td className="px-4 py-3">
                <span className="font-mono font-semibold text-slate-200 group-hover:text-blue-400 transition-colors">
                  {row.ticker}
                </span>
              </td>
              <td className="px-4 py-3">
                <span className={clsx('font-mono font-bold text-base',
                  row.total >= 70 ? 'text-emerald-400' : row.total >= 50 ? 'text-amber-400' : 'text-red-400')}>
                  {row.total}
                </span>
              </td>
              <td className="px-4 py-3 min-w-[140px]">
                <ConvictionBar technical={row.technical} setup={row.setup} fundamental={row.fundamental} />
              </td>
              <td className="px-4 py-3">
                {row.action ? <ActionBadge action={row.action} /> : <span className="text-slate-700">—</span>}
              </td>
              <td className="px-4 py-3">
                {row.stage ? <StageBadge stage={row.stage} /> : <span className="text-slate-700">—</span>}
              </td>
              <td className="px-4 py-3 font-mono text-xs text-slate-300">{fmt.num(row.adr_pct)}%</td>
              <td className="px-4 py-3 font-mono text-xs">
                <span className={clsx((row.atr_extension ?? 0) >= 3 ? 'text-amber-400' : 'text-slate-300')}>
                  {fmt.num(row.atr_extension)}x
                </span>
              </td>
              <td className="px-4 py-3 font-mono text-xs text-slate-300">{fmt.num(row.rvol)}x</td>
              <td className="px-4 py-3">
                {row.peg_active ? <span className="text-amber-400 text-xs font-mono">⚡ Yes</span> : <span className="text-slate-700">—</span>}
              </td>
              <td className="px-4 py-3 text-xs text-slate-500">{SECTOR_LABELS[row.sector] ?? row.sector}</td>
            </tr>
          ))}
          {sorted.length === 0 && (
            <tr><td colSpan={11} className="px-4 py-12 text-center text-slate-500">No data — run the screener pipeline first</td></tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
