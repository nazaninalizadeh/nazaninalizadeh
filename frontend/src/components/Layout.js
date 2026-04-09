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
      toast.success('Logged out successfully');
      navigate('/login');
    } catch (error) {
      toast.error('Failed to logout');
    }
  };

  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/tenants', label: 'Tenants', icon: Users },
    { path: '/landlords', label: 'Landlords', icon: Home },
    { path: '/properties', label: 'Properties', icon: Building2 },
    { path: '/contracts', label: 'Contracts', icon: FileText },
    { path: '/invoices', label: 'Invoices', icon: Receipt },
    { path: '/notifications', label: 'Notifications', icon: Bell },
    { path: '/reports', label: 'Reports', icon: BarChart3 },
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
            <h1 className="text-2xl font-semibold font-heading text-slate-900" data-testid="app-title">
              PropertyOps
            </h1>
            <p className="text-sm text-slate-500 mt-1">Rental Management</p>
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
                      ? 'bg-blue-50 text-blue-700 font-medium'
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
