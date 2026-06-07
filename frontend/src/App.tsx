import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import ErrorBoundary from '@/components/shared/ErrorBoundary'
import Layout    from '@/components/layout/Layout'
import Dashboard  from '@/pages/Dashboard'
import Portfolio  from '@/pages/Portfolio'
import Screener   from '@/pages/Screener'
import PegSetups  from '@/pages/PegSetups'
import Movers     from '@/pages/Movers'
import SectorView from '@/pages/SectorView'
import Analysis   from '@/pages/Analysis'
import Playbook   from '@/pages/Playbook'

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index          element={<ErrorBoundary><Dashboard /></ErrorBoundary>} />
            <Route path="portfolio" element={<ErrorBoundary><Portfolio /></ErrorBoundary>} />
            <Route path="screener"  element={<ErrorBoundary><Screener /></ErrorBoundary>} />
            <Route path="peg"       element={<ErrorBoundary><PegSetups /></ErrorBoundary>} />
            <Route path="movers"    element={<ErrorBoundary><Movers /></ErrorBoundary>} />
            <Route path="sectors"   element={<ErrorBoundary><SectorView /></ErrorBoundary>} />
            <Route path="analysis/:ticker" element={<ErrorBoundary><Analysis /></ErrorBoundary>} />
            <Route path="playbook"          element={<ErrorBoundary><Playbook /></ErrorBoundary>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  )
}
