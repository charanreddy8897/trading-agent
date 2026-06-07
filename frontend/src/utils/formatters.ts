export const fmt = {
  currency: (v: number | null | undefined, decimals = 2): string =>
    v == null
      ? '—'
      : new Intl.NumberFormat('en-US', {
          style: 'currency', currency: 'USD',
          minimumFractionDigits: decimals, maximumFractionDigits: decimals,
        }).format(v),

  pct: (v: number | null | undefined, decimals = 2): string =>
    v == null ? '—' : `${v >= 0 ? '+' : ''}${Number(v).toFixed(decimals)}%`,

  num: (v: number | null | undefined, decimals = 2): string =>
    v == null ? '—' : Number(v).toFixed(decimals),

  bigNum: (v: number | null | undefined): string => {
    if (v == null) return '—'
    if (Math.abs(v) >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`
    if (Math.abs(v) >= 1_000)     return `${(v / 1_000).toFixed(1)}K`
    return String(v)
  },

  date: (v: string | null | undefined): string =>
    v == null ? '—' : new Date(v).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),

  shortDate: (v: string | Date | null | undefined): string =>
    v == null ? '—' : new Date(v).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),

  pnlColor: (v: number | null | undefined): string =>
    (v ?? 0) >= 0 ? 'text-emerald-400' : 'text-red-400',

  pctColor: (v: number | null | undefined): string =>
    (v ?? 0) >= 0 ? 'text-emerald-400' : 'text-red-400',
}
