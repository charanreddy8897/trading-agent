import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header  from './Header'

export default function Layout() {
  return (
    <div className="flex min-h-screen bg-[#0a0e17]">
      <Sidebar />
      <div className="flex-1 flex flex-col ml-52">
        <Header />
        <main className="flex-1 pt-16 overflow-auto">
          <div className="p-6 max-w-screen-2xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
