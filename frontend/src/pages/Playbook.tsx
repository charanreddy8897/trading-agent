import { useState } from 'react'
import { ExternalLink, BookOpen, ChevronDown, ChevronUp } from 'lucide-react'

const SECTIONS = [
  { id: 'start',    label: 'Read this first'       },
  { id: 'basics',   label: 'The absolute basics'   },
  { id: 'ma',       label: 'Moving averages'        },
  { id: 'toolkit',  label: 'The toolkit'            },
  { id: 'screen',   label: 'Screening for stocks'  },
  { id: 'vocab',    label: 'Key vocabulary'         },
  { id: 'mentors',  label: "O'Neil & Weinstein"    },
  { id: 'peg',      label: 'Power Earnings Gap'     },
  { id: 'build',    label: 'Building a position'   },
  { id: 'sell',     label: 'Selling & managing'     },
  { id: 'examples', label: 'Real worked examples'  },
  { id: 'setup',    label: 'Indicator setup'        },
  { id: 'reality',  label: 'Reality & risk check'  },
]

export default function Playbook() {
  const [expanded, setExpanded] = useState(true)

  const openFullscreen = () => window.open('/playbook.html', '_blank', 'noopener')

  const jumpTo = (id: string) => {
    const iframe = document.getElementById('playbook-frame') as HTMLIFrameElement
    if (iframe?.contentWindow) {
      iframe.contentWindow.location.hash = id
    }
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <BookOpen size={18} className="text-violet-400" />
            <h1 className="text-lg font-semibold text-slate-200">Trader's Playbook</h1>
          </div>
          <p className="text-slate-500 text-sm">
            The Beginner's Trading Playbook — O'Neil, Weinstein, PEG setups, and more
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setExpanded(e => !e)}
            className="btn-ghost flex items-center gap-2 text-sm"
          >
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            {expanded ? 'Collapse nav' : 'Show nav'}
          </button>
          <button
            onClick={openFullscreen}
            className="btn-ghost flex items-center gap-2 text-sm"
          >
            <ExternalLink size={14} />
            Full screen
          </button>
        </div>
      </div>

      {/* Quick-jump nav */}
      {expanded && (
        <div className="card p-4">
          <p className="text-xs text-slate-500 uppercase tracking-widest font-mono mb-3">Jump to section</p>
          <div className="flex flex-wrap gap-2">
            {SECTIONS.map((s, i) => (
              <button
                key={s.id}
                onClick={() => jumpTo(s.id)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-slate-200 hover:bg-[#1a2235] border border-[#1e293b] transition-colors"
              >
                <span className="font-mono text-[10px] text-slate-600">{String(i).padStart(2, '0')}</span>
                {s.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Embedded playbook */}
      <div className="card overflow-hidden" style={{ height: 'calc(100vh - 200px)' }}>
        <iframe
          id="playbook-frame"
          src="/playbook.html"
          className="w-full h-full border-0"
          title="Trader's Playbook"
          sandbox="allow-scripts allow-same-origin"
        />
      </div>
    </div>
  )
}
