// ── Portfolio ────────────────────────────────────────────────────
export interface PortfolioSummary {
  total_value:     number
  total_pnl:       number
  daily_change:    number
  daily_pct:       number
  position_count:  number
  cash?:           number
}

export interface Position {
  ticker:          string
  shares:          number
  avg_cost:        number
  current_price:   number
  market_value:    number
  unrealized_pnl:  number
  unrealized_pct:  number
  sector:          string
  entry_date?:     string
  stop_loss?:      number
  tranche1_filled: boolean
  tranche2_filled: boolean
}

export interface SectorAllocation {
  sector_pcts: Record<string, number>
  correlated:  Record<string, number>
  warnings:    string[]
}

// ── Screener ─────────────────────────────────────────────────────
export interface ScreenerRow {
  ticker:        string
  sector:        string
  technical:     number
  setup:         number
  fundamental:   number
  total:         number
  action:        Action | null
  stage:         number | null
  base_number:   number | null
  adr_pct:       number | null
  atr_extension: number | null
  rvol:          number | null
  peg_active:    boolean
}

// ── Analysis ─────────────────────────────────────────────────────
export interface Analysis {
  id:          number
  ticker:      string
  analyzed_at: string
  conviction:  number
  action:      Action
  entry_zone:  string
  stop_loss:   number
  risk_reward: string
  stage:       string
  base_number: number | null
  reasoning:   string
  warnings:    string[]
  raw_json:    Record<string, unknown>
}

// ── PEG ──────────────────────────────────────────────────────────
export interface PegSetup {
  id:              number
  ticker:          string
  peg_date:        string
  peg_low:         number
  gap_pct:         number
  volume_multiple: number
  gap_filled:      boolean
  created_at:      string
  sector?:         string
  current_price?:  number
  entry_zone?:     string
}

// ── Movers ───────────────────────────────────────────────────────
export interface Mover {
  ticker:     string
  price:      number
  change_pct: number
  volume?:    number
  avg_volume?: number
  rvol?:      number
  sector?:    string
}

export interface MoversResponse {
  gainers: Mover[]
  losers:  Mover[]
}

// ── News ─────────────────────────────────────────────────────────
export interface NewsItem {
  id:           number
  ticker:       string
  published_at: string
  headline:     string
  summary:      string
  sentiment:    number | null
  source:       string
  category:     string
  url:          string
}

// ── Alerts ───────────────────────────────────────────────────────
export interface Alert {
  id:         number
  ticker:     string
  alert_type: string
  message:    string
  severity:   Severity
  dismissed:  boolean
  created_at: string
}

// ── Enums / Literals ─────────────────────────────────────────────
export type Action   = 'BUY' | 'ADD' | 'HOLD' | 'TRIM' | 'SELL' | 'WATCH'
export type Severity = 'critical' | 'warning' | 'info'
export type Sector   = 'AI_SOFTWARE' | 'SEMICONDUCTORS' | 'MEMORY' | 'SPACE_DEFENSE' | 'PHYSICAL_AI_ROBOTICS'

// ── Chart helpers ────────────────────────────────────────────────
export interface DataPoint {
  date:  string
  value: number
}

export interface SectorStat {
  sector:    string
  avgScore:  number
  stage2Pct: number
  pegCount:  number
  count:     number
}
