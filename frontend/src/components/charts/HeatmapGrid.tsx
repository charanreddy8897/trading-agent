import { SECTOR_LABELS } from '@/utils/constants'
import clsx from 'clsx'

interface SectorChange { name: string; change: number }

const MOCK: SectorChange[] = [
  { name: 'SEMICONDUCTORS',       change: 2.1  },
  { name: 'AI_SOFTWARE',          change: 1.8  },
  { name: 'SPACE_DEFENSE',        change: 3.4  },
  { name: 'MEMORY',               change: -0.3 },
  { name: 'PHYSICAL_AI_ROBOTICS', change: 0.9  },
]

function colorClass(pct: number) {
  if (pct >=  3) return 'bg-emerald-500  text-white'
  if (pct >=  1) return 'bg-emerald-700/70 text-emerald-100'
  if (pct >=  0) return 'bg-emerald-900/40 text-emerald-300'
  if (pct >= -1) return 'bg-red-900/40 text-red-300'
  if (pct >= -3) return 'bg-red-700/70 text-red-100'
  return 'bg-red-500 text-white'
}

interface Props { data?: SectorChange[] }

export default function HeatmapGrid({ data }: Props) {
  const items = data ?? MOCK
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
      {items.map(item => (
        <div key={item.name} className={clsx('rounded-xl p-4 text-center cursor-default transition-all', colorClass(item.change))}>
          <p className="text-xs font-medium opacity-80">{SECTOR_LABELS[item.name] ?? item.name}</p>
          <p className="text-2xl font-mono font-semibold mt-1">
            {item.change >= 0 ? '+' : ''}{item.change.toFixed(1)}%
          </p>
        </div>
      ))}
    </div>
  )
}
