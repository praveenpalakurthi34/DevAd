import React from 'react';
import { BrowserRouter, Routes, Route, NavLink, Link } from 'react-router-dom';
import {
  LayoutDashboard,
  PlusCircle,
  History,
  Brain,
  Sparkles,
  Menu,
  X,
} from 'lucide-react';
import Dashboard from './pages/Dashboard';
import NewCampaign from './pages/NewCampaign';
import CampaignDetail from './pages/CampaignDetail';
import HistoryPage from './pages/History';
import Learning from './pages/Learning';

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/campaigns/new', label: 'Create Campaign', icon: PlusCircle },
  { to: '/history', label: 'Campaign History', icon: History },
  { to: '/learning', label: 'Learning', icon: Brain },
];

export default function App() {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        {/* Top nav */}
        <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-lg border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex h-16 items-center justify-between">
              {/* Logo */}
              <Link to="/" className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center">
                  <Sparkles className="w-4.5 h-4.5 text-white" />
                </div>
                <span className="text-xl font-bold bg-gradient-to-r from-brand-600 to-brand-800 bg-clip-text text-transparent">
                  DevAd
                </span>
              </Link>

              {/* Desktop nav */}
              <div className="hidden md:flex items-center gap-1">
                {navItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.to === '/'}
                    className={({ isActive }) =>
                      `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                        isActive
                          ? 'bg-brand-50 text-brand-700'
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                      }`
                    }
                  >
                    <item.icon className="w-4 h-4" />
                    {item.label}
                  </NavLink>
                ))}
              </div>

              {/* Mobile menu button */}
              <button
                className="md:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </div>
          </div>

          {/* Mobile nav */}
          {mobileMenuOpen && (
            <div className="md:hidden border-t border-gray-200 bg-white animate-fade-in">
              <div className="px-4 py-3 space-y-1">
                {navItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.to === '/'}
                    onClick={() => setMobileMenuOpen(false)}
                    className={({ isActive }) =>
                      `flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium ${
                        isActive
                          ? 'bg-brand-50 text-brand-700'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`
                    }
                  >
                    <item.icon className="w-4 h-4" />
                    {item.label}
                  </NavLink>
                ))}
              </div>
            </div>
          )}
        </nav>

        {/* Main content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/campaigns/new" element={<NewCampaign />} />
            <Route path="/campaigns/:id" element={<CampaignDetail />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/learning" element={<Learning />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
