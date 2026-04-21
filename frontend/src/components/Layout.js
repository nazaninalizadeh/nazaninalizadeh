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
  BarChart3,
  DoorOpen,
  CreditCard
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
    { path: '/rooms', label: 'Stanze', icon: DoorOpen },
    { path: '/payments', label: 'Pagamenti', icon: CreditCard },
    { path: '/contracts', label: 'Contratti', icon: FileText },
    { path: '/invoices', label: 'Fatture', icon: Receipt },
    { path: '/notifications', label: 'Notifiche', icon: Bell },
    { path: '/reports', label: 'Report', icon: BarChart3 },
  ];

  return (
    <div className="min-h-screen flex" style={{ background: 'linear-gradient(135deg, #FAF7F0 0%, #F5F1E8 100%)' }}>
      {/* Mobile menu button */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2.5 rounded-xl shadow-lg"
        style={{ background: 'white', border: '1px solid rgba(184, 134, 11, 0.15)' }}
        data-testid="mobile-menu-button"
      >
        {sidebarOpen ? <X size={22} /> : <Menu size={22} />}
      </button>

      {/* Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-40 w-[270px] luxury-sidebar transform transition-transform duration-300 ease-in-out ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
        data-testid="sidebar"
      >
        <div className="flex flex-col h-full">
          <div className="p-6" style={{ borderBottom: '1px solid rgba(184, 134, 11, 0.15)' }}>
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 rounded-xl" style={{ background: 'linear-gradient(135deg, #9F1239 0%, #BE123C 100%)', boxShadow: '0 4px 12px rgba(159, 18, 57, 0.3)' }}>
                <svg width="24" height="24" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M16 2L4 10v12c0 3.314 2.686 6 6 6h12c3.314 0 6-2.686 6-6V10L16 2z" fill="white" stroke="white" strokeWidth="1.5"/>
                  <rect x="12" y="18" width="8" height="10" fill="#9F1239"/>
                </svg>
              </div>
              <div>
                <h1 className="text-lg font-semibold font-heading" style={{ color: '#9F1239' }} data-testid="app-title">
                  Consulenze immobiliari
                </h1>
                <p className="text-xs" style={{ color: '#8B7355' }}>Via Vigonovese 114</p>
              </div>
            </div>
            <p className="text-[10px] uppercase tracking-[0.15em] font-medium" style={{ color: '#B8860B' }}>Affitta &bull; Compra &bull; Vende &bull; Ristruttura</p>
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
                  className={`luxury-nav-item flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 ${
                    isActive
                      ? 'active font-semibold'
                      : ''
                  }`}
                  style={isActive ? {
                    background: 'linear-gradient(135deg, rgba(159, 18, 57, 0.12) 0%, rgba(190, 18, 60, 0.06) 100%)',
                    color: '#9F1239',
                    borderLeft: '3px solid #9F1239',
                  } : {
                    color: '#5C4A3A',
                  }}
                  data-testid={`nav-${item.label.toLowerCase()}`}
                >
                  <Icon size={20} strokeWidth={isActive ? 2.5 : 2} />
                  <span className="text-sm">{item.label}</span>
                </Link>
              );
            })}
          </nav>

          <div className="p-4" style={{ borderTop: '1px solid rgba(184, 134, 11, 0.15)' }}>
            <div className="mb-3 px-4">
              <p className="text-sm font-semibold" style={{ color: '#2C1810' }} data-testid="user-name">{user?.name}</p>
              <p className="text-xs capitalize" style={{ color: '#8B7355' }} data-testid="user-role">{user?.role?.replace('_', ' ')}</p>
            </div>
            <Button
              onClick={handleLogout}
              variant="outline"
              className="w-full justify-start rounded-xl text-sm"
              style={{ borderColor: 'rgba(184, 134, 11, 0.2)', color: '#5C4A3A' }}
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
        <div className="p-6 lg:p-10">
          <Outlet />
        </div>
      </main>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 z-30 luxury-modal-overlay"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
};

export default Layout;
