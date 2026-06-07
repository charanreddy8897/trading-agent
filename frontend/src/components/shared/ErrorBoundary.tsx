import { Component, ErrorInfo, ReactNode } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

interface Props {
  children:  ReactNode
  fallback?: ReactNode
}

interface State {
  hasError:  boolean
  error:     Error | null
  errorInfo: ErrorInfo | null
}

/**
 * Catches unhandled React render errors so a single component crash
 * doesn't take down the entire dashboard.
 *
 * Usage:
 *   <ErrorBoundary>
 *     <SomePage />
 *   </ErrorBoundary>
 */
export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ errorInfo })
    // In production this would go to an error tracking service (Sentry etc.)
    console.error('[ErrorBoundary]', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback

      return (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8 text-center">
          <div className="w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center mb-4">
            <AlertTriangle size={24} className="text-red-400" />
          </div>
          <h2 className="text-slate-200 font-semibold text-lg mb-2">Something went wrong</h2>
          <p className="text-slate-500 text-sm mb-6 max-w-md">
            {this.state.error?.message ?? 'An unexpected error occurred in this component.'}
          </p>
          <button
            onClick={this.handleReset}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600/20 text-blue-400
                       hover:bg-blue-600/30 transition-colors text-sm"
          >
            <RefreshCw size={14} />
            Try again
          </button>

          {import.meta.env.DEV && this.state.errorInfo && (
            <pre className="mt-6 text-left text-xs text-slate-600 bg-slate-900 p-4 rounded-lg
                            overflow-auto max-w-full max-h-48 w-full">
              {this.state.errorInfo.componentStack}
            </pre>
          )}
        </div>
      )
    }

    return this.props.children
  }
}
