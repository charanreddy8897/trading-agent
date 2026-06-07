import clsx from 'clsx'

interface Props { technical?: number; setup?: number; fundamental?: number }

export default function ConvictionBar({ technical = 0, setup = 0, fundamental = 0 }: Props) {
  return (
    <div className="space-y-1 w-full">
      <div className="flex items-center gap-0.5 h-2 rounded overflow-hidden">
        <div className="h-full bg-blue-500"   style={{ width: `${technical}%` }}   title={`Tech: ${technical}`} />
        <div className="h-full bg-violet-500" style={{ width: `${setup}%` }}       title={`Setup: ${setup}`} />
        <div className="h-full bg-cyan-500"   style={{ width: `${fundamental}%` }} title={`Fund: ${fundamental}`} />
        <div className="h-full flex-1 bg-slate-800" />
      </div>
      <div className="flex justify-between text-[9px] font-mono text-slate-600">
        <span>T:{technical}</span><span>S:{setup}</span><span>F:{fundamental}</span>
      </div>
    </div>
  )
}

interface ScoreCircleProps { score: number; size?: 'sm' | 'md' | 'lg' }

export function ScoreCircle({ score, size = 'md' }: ScoreCircleProps) {
  const color = score >= 70 ? '#10b981' : score >= 50 ? '#f59e0b' : '#ef4444'
  const sz    = { sm: 'w-9 h-9 text-xs', md: 'w-12 h-12 text-sm', lg: 'w-16 h-16 text-base' }[size]
  return (
    <div className={clsx('rounded-full flex items-center justify-center font-mono font-semibold border-2', sz)}
      style={{ borderColor: color, color }}>
      {score}
    </div>
  )
}
