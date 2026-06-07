import { useParams, useNavigate } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { RefreshCw, ArrowLeft, AlertTriangle } from 'lucide-react'
import { useAnalysis, useRefreshAnalysis } from '@/hooks/useAnalysis'
import { ActionBadge, StageBadge } from '@/components/shared/Badge'
import { ScoreCircle } from '@/components/charts/ConvictionBar'
import { EmptyState, Skeleton } from '@/components/shared/LoadingSkeleton'
import { fmt } from '@/utils/formatters'
import clsx from 'clsx'

interface ScoreBarProps { label: string; value: number; max: number; color: string }

function ScoreBar({ label, value, max, color }: ScoreBarProps) {
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-xs">
        <span className="text-slate-400">{label}</span>
        <span className={clsx('font-mono font-semibold', color)}>{value}<span className="text-slate-600">/{max}</span></span>
      </div>
      <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
        <div className={clsx('h-full rounded-full transition-all', color.replace('text-', 'bg-'))}
          style={{ width: `${(value / max) * 100}%` }} />
      </div>
    </div>
  )
}

interface KvProps { label: string; value: string | null; highlight?: string }

function Kv({ label, value, highlight }: KvProps) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-[#1e293b]/50 last:border-0">
      <span className="text-xs text-slate-500">{label}</span>
      <span className={clsx('font-mono text-xs font-medium', highlight ?? 'text-slate-300')}>{value ?? '—'}</span>
    </div>
  )
}

export default function Analysis() {
  const { ticker = '' }  = useParams<{ ticker: string }>()
  const navigate         = useNavigate()
  const { data, isLoading, error } = useAnalysis(ticker)
  const refresh          = useRefreshAnalysis(ticker)

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-40" />)}
        </div>
        <Skeleton className="h-80 w-full" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="space-y-4">
        <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-slate-400 hover:text-slate-200 text-sm transition-colors">
          <ArrowLeft size={16} /> Back
        </button>
        <EmptyState icon="🔍" title={`No analysis found for ${ticker}`}
          subtitle="Run the pipeline or click Refresh Analysis to generate one" />
        <div className="flex justify-center">
          <button onClick={() => refresh.mutate()} disabled={refresh.isPending}
            className="btn-primary flex items-center gap-2">
            <RefreshCw size={14} className={refresh.isPending ? 'animate-spin' : ''} />
            Generate Analysis
          </button>
        </div>
      </div>
    )
  }

  const raw = data.raw_json as Record<string, unknown>
  const technicals = raw?.technicals as Record<string, number> | undefined
  const priceHistory = raw?.price_history as { date: string; close: number }[] | undefined

  const conviction  = data.conviction  ?? 0
  const technical   = Math.round(conviction * 0.4 * 10)
  const setup       = Math.round(conviction * 0.3 * 10)
  const fundamental = Math.round(conviction * 0.3 * 10)

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <button onClick={() => navigate(-1)} className="flex items-center gap-1.5 text-slate-500 hover:text-slate-300 text-sm mb-2 transition-colors">
            <ArrowLeft size={14} /> Back
          </button>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-3xl font-mono font-bold text-slate-100">{ticker}</h1>
            {data.action && <ActionBadge action={data.action} />}
            {data.stage && <StageBadge stage={parseInt(data.stage.replace('Stage ', '')) || 2} />}
          </div>
          <p className="text-slate-500 text-sm mt-1">
            Analyzed {fmt.date(data.analyzed_at)} · Conviction {data.conviction}/10
          </p>
        </div>
        <div className="flex items-center gap-3">
          <ScoreCircle score={conviction * 10} size="lg" />
          <button onClick={() => refresh.mutate()} disabled={refresh.isPending}
            className="btn-ghost flex items-center gap-2 text-sm">
            <RefreshCw size={14} className={refresh.isPending ? 'animate-spin' : ''} />
            {refresh.isPending ? 'Analyzing…' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Price chart */}
      {priceHistory && priceHistory.length > 0 && (
        <div className="card p-5">
          <p className="text-sm font-medium text-slate-300 mb-4">Price History (90 days)</p>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={priceHistory} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#475569' }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
              <YAxis tick={{ fontSize: 10, fill: '#475569' }} axisLine={false} tickLine={false}
                tickFormatter={v => `$${v}`} width={52} domain={['auto', 'auto']} />
              <Tooltip
                contentStyle={{ background: '#1a2235', border: '1px solid #1e293b', borderRadius: 8, fontSize: 12 }}
                formatter={(v: number) => [fmt.currency(v), 'Price']}
                labelStyle={{ color: '#94a3b8' }}
              />
              {data.stop_loss && (
                <ReferenceLine y={data.stop_loss} stroke="#ef4444" strokeDasharray="4 4" label={{ value: 'Stop', fill: '#ef4444', fontSize: 10 }} />
              )}
              <Line type="monotone" dataKey="close" stroke="#3b82f6" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="grid grid-cols-3 gap-4">
        {/* Score breakdown */}
        <div className="card p-5 space-y-5">
          <p className="text-sm font-medium text-slate-300">Score Breakdown</p>
          <ScoreBar label="Technical"   value={technical}   max={40} color="text-blue-400"   />
          <ScoreBar label="Setup"       value={setup}       max={30} color="text-violet-400" />
          <ScoreBar label="Fundamental" value={fundamental} max={30} color="text-cyan-400"   />
          <div className="pt-2 border-t border-[#1e293b]">
            <div className="flex justify-between text-sm">
              <span className="text-slate-400 font-medium">Total</span>
              <span className={clsx('font-mono font-bold',
                conviction * 10 >= 70 ? 'text-emerald-400' : conviction * 10 >= 50 ? 'text-amber-400' : 'text-red-400')}>
                {conviction * 10}/100
              </span>
            </div>
          </div>
        </div>

        {/* Key metrics */}
        <div className="card p-5">
          <p className="text-sm font-medium text-slate-300 mb-3">Key Metrics</p>
          <Kv label="Stage"       value={data.stage} highlight={data.stage?.includes('2') ? 'text-emerald-400' : undefined} />
          <Kv label="Base #"      value={data.base_number ? `Base ${data.base_number}` : null}
            highlight={data.base_number && data.base_number >= 3 ? 'text-amber-400' : undefined} />
          <Kv label="Entry Zone"  value={data.entry_zone} />
          <Kv label="Stop Loss"   value={fmt.currency(data.stop_loss)} highlight="text-red-400" />
          <Kv label="Risk/Reward" value={data.risk_reward} />
          {technicals && (
            <>
              <Kv label="ADR%"       value={technicals.adr_pct ? `${technicals.adr_pct.toFixed(1)}%` : null}
                highlight={technicals.adr_pct >= 3 && technicals.adr_pct <= 10 ? 'text-emerald-400' : 'text-amber-400'} />
              <Kv label="ATR Ext"    value={technicals.atr_extension ? `${technicals.atr_extension.toFixed(1)}x` : null}
                highlight={technicals.atr_extension >= 3 ? 'text-amber-400' : undefined} />
              <Kv label="RVol"       value={technicals.rvol ? `${technicals.rvol.toFixed(1)}x` : null} />
            </>
          )}
        </div>

        {/* Claude analysis */}
        <div className="card p-5 flex flex-col">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-violet-400 text-lg">🤖</span>
            <p className="text-sm font-medium text-slate-300">Claude Analysis</p>
          </div>
          <p className="text-sm text-slate-300 leading-relaxed flex-1">{data.reasoning}</p>
          {data.warnings && data.warnings.length > 0 && (
            <div className="mt-4 space-y-2 pt-4 border-t border-[#1e293b]">
              {data.warnings.map((w, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-amber-400">
                  <AlertTriangle size={12} className="shrink-0 mt-0.5" />
                  <span>{w}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
