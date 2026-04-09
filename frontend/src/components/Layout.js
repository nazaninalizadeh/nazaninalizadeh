import React, { useState } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  LayoutDashboard, 
  Users, 
  Home, 
  FileText, 
  Receipt, 
  LogOut,
  Building2,
  Menu,
  X,
  Bell,
  BarChart3
} from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';

const Layout = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = async () => {
    try {
      await logout();
      toast.success('Disconnesso con successo');
      navigate('/login');
    } catch (error) {
      toast.error('Impossibile disconnettersi');
    }
  };

  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/tenants', label: 'Inquilini', icon: Users },
    { path: '/landlords', label: 'Proprietari', icon: Home },
    { path: '/properties', label: 'Immobili', icon: Building2 },
    { path: '/contracts', label: 'Contratti', icon: FileText },
    { path: '/invoices', label: 'Fatture', icon: Receipt },
    { path: '/notifications', label: 'Notifiche', icon: Bell },
    { path: '/reports', label: 'Report', icon: BarChart3 },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Mobile menu button */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-white shadow-md"
        data-testid="mobile-menu-button"
      >
        {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-40 w-64 bg-white border-r border-slate-200 transform transition-transform duration-200 ease-in-out ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
        data-testid="sidebar"
      >
        <div className="flex flex-col h-full">
          <div className="p-6 border-b border-slate-200">
            <div className="flex items-center gap-3 mb-2">
              <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M16 2L4 10v12c0 3.314 2.686 6 6 6h12c3.314 0 6-2.686 6-6V10L16 2z" fill="#9F1239" stroke="#9F1239" strokeWidth="1.5"/>
                <rect x="12" y="18" width="8" height="10" fill="white"/>
                <line x1="28" y1="8" x2="32" y2="8" stroke="#DC2626" strokeWidth="2"/>
              </svg>
              <div>
                <h1 className="text-xl font-semibold font-heading text-rose-800" data-testid="app-title">
                  Consulenze immobiliari
                </h1>
                <p className="text-xs text-slate-600">Via Vigonovese 114</p>
              </div>
            </div>
            <p className="text-xs text-slate-500 uppercase tracking-wide">Affitta • Compra • Vende • Ristruttura</p>
          </div>

          <nav className="flex-1 p-4 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-rose-50 text-rose-700 font-medium'
                      : 'text-slate-600 hover:bg-slate-50'
                  }`}
                  data-testid={`nav-${item.label.toLowerCase()}`}
                >
                  <Icon size={20} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          <div className="p-4 border-t border-slate-200">
            <div className="mb-3 px-4">
              <p className="text-sm font-medium text-slate-900" data-testid="user-name">{user?.name}</p>
              <p className="text-xs text-slate-500" data-testid="user-role">{user?.role?.replace('_', ' ')}</p>
            </div>
            <Button
              onClick={handleLogout}
              variant="outline"
              className="w-full justify-start"
              data-testid="logout-button"
            >
              <LogOut size={18} className="mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 lg:ml-0 overflow-auto">
        <div className="p-6 lg:p-8">
          <Outlet />
        </div>
      </main>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-slate-900/40 z-30"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
};

export default Layout;
