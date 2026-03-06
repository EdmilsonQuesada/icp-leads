import { BrowserRouter, Routes, Route, Link, NavLink } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Dashboard } from "./pages/Dashboard";
import { LeadList } from "./pages/LeadList";
import { LeadProfile } from "./pages/LeadProfile";
import { SearchPage } from "./pages/SearchPage";
import { Settings } from "./pages/Settings";
import { NotificationBell } from "./components/NotificationBell";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30000 } },
});

const navClass = ({ isActive }) =>
  isActive ? "text-indigo-600 font-semibold" : "text-gray-600 hover:text-indigo-600";

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50">
          <nav className="bg-white border-b px-6 py-3 flex items-center gap-6 sticky top-0 z-40 shadow-sm">
            <Link to="/" className="font-bold text-indigo-700 text-lg">ICP Leads</Link>
            <NavLink to="/" end className={navClass}>Dashboard</NavLink>
            <NavLink to="/leads" className={navClass}>Leads</NavLink>
            <NavLink to="/search" className={navClass}>Buscar</NavLink>
            <NavLink to="/settings" className={navClass}>Configurações</NavLink>
            <div className="ml-auto">
              <NotificationBell />
            </div>
          </nav>
          <main>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/leads" element={<LeadList />} />
              <Route path="/leads/:id" element={<LeadProfile />} />
              <Route path="/search" element={<SearchPage />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
