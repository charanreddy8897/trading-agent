import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Briefcase, ScanLine, Zap, TrendingUp, Map, BarChart2, BookOpen } from 'lucide-react'
import clsx from 'clsx'

const NAV_MAIN = [
  { to: '/',          icon: LayoutDashboard, label: 'Dashboard'  },
  { to: '/portfolio', icon: Briefcase,       label: 'Portfolio'  },
  { to: '/screener',  icon: ScanLine,        label: 'Screener'   },
  { to: '/peg',       icon: Zap,             label: 'PEG Setups' },
  { to: '/movers',    icon: TrendingUp,      label: 'Movers'     },
  { to: '/sectors',   icon: Map,             label: 'Sectors'    },
] as const

const NAV_LEARN = [
  { to: '/playbook',  icon: BookOpen,        label: "Trader's Playbook" },
] as const

export default function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 h-screen w-52 flex flex-col border-r border-[#1e293b] bg-[#0d1321] z-40">
      {/* Logo */}
      <div className="h-16 flex items-center px-5 border-b border-[#1e293b]">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center">
            <BarChart2 size={15} className="text-white" />
          </div>
          <div>
            <p className="text-slate-200 font-semibold text-sm leading-tight">TradingAgent</p>
            <p className="text-slate-500 text-[10px] font-mono">PAPER MODE</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-2 space-y-0.5 overflow-y-auto">
        <p className="px-3 py-2 text-[10px] font-semibold text-slate-600 uppercase tracking-widest">Main</p>
        {NAV_MAIN.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all',
                isActive
                  ? 'bg-blue-600/20 text-blue-400 font-medium'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-[#1a2235]',
              )
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}

        <p className="px-3 pt-4 pb-2 text-[10px] font-semibold text-slate-600 uppercase tracking-widest">Learn</p>
        {NAV_LEARN.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all',
                isActive
                  ? 'bg-violet-600/20 text-violet-400 font-medium'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-[#1a2235]',
              )
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Status footer */}
      <div className="px-4 py-4 border-t border-[#1e293b]">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse block" />
          <span className="text-xs text-slate-500">Market open</span>
        </div>
      </div>
    </aside>
  )
}
