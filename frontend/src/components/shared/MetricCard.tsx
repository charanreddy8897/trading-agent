import type { LucideIcon } from 'lucide-react'
import clsx from 'clsx'

interface Props {
  label:      string
  value:      string | number
  sub?:       string
  subColor?:  string
  icon?:      LucideIcon
  iconColor?: string
  trend?:     number | null
}

export default function MetricCard({ label, value, sub, subColor, icon: Icon, iconColor = 'text-blue-400', trend }: Props) {
  return (
    <div className="card p-5 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <p className="text-[10px] text-slate-500 uppercase tracking-widest font-mono">{label}</p>
        {Icon && (
          <div className={clsx('p-2 rounded-lg bg-slate-800/50', iconColor)}>
            <Icon size={14} />
          </div>
        )}
      </div>
      <div>
        <p className="text-2xl font-semibold font-mono text-slate-100 leading-none">{value ?? '—'}</p>
        {sub && <p className={clsx('text-sm font-mono mt-1.5', subColor ?? 'text-slate-500')}>{sub}</p>}
      </div>
      {trend != null && (
        <p className={clsx('text-xs font-mono', trend >= 0 ? 'text-emerald-400' : 'text-red-400')}>
          {trend >= 0 ? '▲' : '▼'} {Math.abs(trend).toFixed(2)}%
        </p>
      )}
    </div>
  )
}
