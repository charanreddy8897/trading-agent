import clsx from 'clsx'
import type { Action, Severity } from '@/types'
import { ACTION_STYLES, SEVERITY_STYLES } from '@/utils/constants'

export function ActionBadge({ action }: { action: Action }) {
  const c = ACTION_STYLES[action] ?? ACTION_STYLES.HOLD
  return <span className={clsx('tag border', c.bg, c.text, c.border)}>{action}</span>
}

export function SeverityBadge({ severity, label }: { severity: Severity; label?: string }) {
  const c = SEVERITY_STYLES[severity] ?? SEVERITY_STYLES.info
  return <span className={clsx('tag border', c.bg, c.text, c.border)}>{c.icon} {label ?? severity}</span>
}

export function StageBadge({ stage }: { stage: number }) {
  const styles: Record<number, string> = {
    1: 'text-slate-400 bg-slate-500/10 border-slate-500/20',
    2: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    3: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    4: 'text-red-400 bg-red-500/10 border-red-500/20',
  }
  return <span className={clsx('tag border', styles[stage] ?? styles[1])}>S{stage}</span>
}
