import type { Action, Severity, Sector } from '@/types'

export const SECTOR_COLORS: Record<string, string> = {
  AI_SOFTWARE:          '#8b5cf6',
  SEMICONDUCTORS:       '#06b6d4',
  MEMORY:               '#3b82f6',
  SPACE_DEFENSE:        '#10b981',
  PHYSICAL_AI_ROBOTICS: '#f59e0b',
}

export const SECTOR_LABELS: Record<string, string> = {
  AI_SOFTWARE:          'AI / Software',
  SEMICONDUCTORS:       'Semiconductors',
  MEMORY:               'Memory',
  SPACE_DEFENSE:        'Space & Defense',
  PHYSICAL_AI_ROBOTICS: 'Robotics / AI',
}

export const ALL_SECTORS: Sector[] = [
  'AI_SOFTWARE', 'SEMICONDUCTORS', 'MEMORY', 'SPACE_DEFENSE', 'PHYSICAL_AI_ROBOTICS',
]

interface BadgeStyle { bg: string; text: string; border: string }

export const ACTION_STYLES: Record<Action, BadgeStyle> = {
  BUY:   { bg: 'bg-emerald-500/20', text: 'text-emerald-400', border: 'border-emerald-500/30' },
  ADD:   { bg: 'bg-emerald-500/10', text: 'text-emerald-500', border: 'border-emerald-500/20' },
  HOLD:  { bg: 'bg-slate-500/20',   text: 'text-slate-400',   border: 'border-slate-500/30'   },
  TRIM:  { bg: 'bg-amber-500/20',   text: 'text-amber-400',   border: 'border-amber-500/30'   },
  SELL:  { bg: 'bg-red-500/20',     text: 'text-red-400',     border: 'border-red-500/30'     },
  WATCH: { bg: 'bg-cyan-500/20',    text: 'text-cyan-400',    border: 'border-cyan-500/30'    },
}

interface SeverityStyle extends BadgeStyle { icon: string }

export const SEVERITY_STYLES: Record<Severity, SeverityStyle> = {
  critical: { bg: 'bg-red-500/10',   text: 'text-red-400',   border: 'border-red-500/30',   icon: '🚨' },
  warning:  { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/30', icon: '⚠️' },
  info:     { bg: 'bg-cyan-500/10',  text: 'text-cyan-400',  border: 'border-cyan-500/30',  icon: 'ℹ️' },
}

export const STAGE_TEXT: Record<number, string> = {
  1: 'text-slate-400',
  2: 'text-emerald-400',
  3: 'text-amber-400',
  4: 'text-red-400',
}
