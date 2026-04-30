import React, { useState, useEffect } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
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
  CreditCard,
  Sheet,
  ScrollText,
  ClipboardList
} from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';

const Layout = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notifCount, setNotifCount] = useState(0);

  const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

  useEffect(() => {
    const fetchCount = async () => {
      try {
        const { data } = await axios.get(`${API_URL}/notifications/count`, { withCredentials: true });
        setNotifCount(data.count || 0);
      } catch {}
    };
    fetchCount();
    const interval = setInterval(fetchCount, 60000);
    // Reset badge immediately when the Notifiche page marks notifications seen.
    const onSeen = () => setNotifCount(0);
    window.addEventListener('notifications:seen', onSeen);
    return () => { clearInterval(interval); window.removeEventListener('notifications:seen', onSeen); };
  }, []);

  // Re-fetch the badge whenever the user navigates somewhere (cheap and keeps badge in sync).
  useEffect(() => {
    if (location.pathname === '/notifications') return; // already cleared via event
    axios.get(`${API_URL}/notifications/count`, { withCredentials: true })
      .then(({ data }) => setNotifCount(data.count || 0))
      .catch(() => {});
  }, [location.pathname]);

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
    { path: '/landlords', label: 'Proprietari', icon: Home },
    { path: '/properties', label: 'Immobili', icon: Building2 },
    { path: '/tenants', label: 'Inquilini', icon: Users },
    { path: '/payments', label: 'Pagamenti', icon: CreditCard },
    { path: '/hospitality', label: 'Ospitalità', icon: ScrollText },
    { path: '/registration', label: 'Registrazione', icon: ClipboardList },
    { path: '/contracts', label: 'Contratti', icon: FileText },
    { path: '/invoices', label: 'Fatture', icon: Receipt },
    { path: '/preavviso', label: 'Preavviso di Fatturazione', icon: Receipt },
    { path: '/notifications', label: 'Notifiche', icon: Bell },
    { path: '/reports', label: 'Report', icon: BarChart3 },
    { path: '/data-exchange', label: 'Gestione Dati', icon: Sheet },
  ];

  return (
    <div className="min-h-screen flex" style={{ background: 'linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%)' }}>
      {/* Mobile menu button */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2.5 rounded-xl shadow-lg"
        style={{ background: 'white', border: '1px solid rgba(217, 42, 42, 0.15)' }}
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
          <div className="p-5" style={{ borderBottom: '1px solid #E2E8F0' }}>
            <div className="flex items-center gap-3 mb-2">
              <img
                src="/assets/logo.jpeg"
                alt="Housing in Padova"
                className="h-14 w-14 rounded-lg object-contain bg-white"
                style={{ border: '1px solid #E2E8F0' }}
                data-testid="app-logo"
              />
              <div className="min-w-0">
                <h1 className="text-base font-bold leading-tight truncate" style={{ color: '#0F172A', fontFamily: "'DM Sans', sans-serif" }} data-testid="app-title">
                  Housing in Padova
                </h1>
                <p className="text-[11px] font-medium" style={{ color: '#64748B' }}>Rent Room Service</p>
              </div>
            </div>
            <p className="text-[10px] uppercase tracking-[0.15em] font-medium" style={{ color: '#D92A2A' }}>by Consulenze Immobiliari</p>
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
                    background: 'linear-gradient(135deg, rgba(11, 138, 62, 0.12) 0%, rgba(7, 107, 45, 0.06) 100%)',
                    color: '#0B8A3E',
                    borderLeft: '3px solid #0B8A3E',
                  } : {
                    color: '#475569',
                  }}
                  data-testid={`nav-${item.label.toLowerCase()}`}
                >
                  <Icon size={20} strokeWidth={isActive ? 2.5 : 2} />
                  <span className="text-sm">{item.label}</span>
                  {item.label === 'Notifiche' && notifCount > 0 && (
                    <span className="ml-auto px-1.5 py-0.5 rounded-full text-[10px] font-bold text-white" style={{ background: '#DC2626', minWidth: 18, textAlign: 'center' }}>{notifCount}</span>
                  )}
                </Link>
              );
            })}
          </nav>

          <div className="p-4" style={{ borderTop: '1px solid rgba(217, 42, 42, 0.15)' }}>
            <div className="mb-3 px-4">
              <p className="text-sm font-semibold" style={{ color: '#0F172A' }} data-testid="user-name">{user?.name}</p>
              <p className="text-xs capitalize" style={{ color: '#64748B' }} data-testid="user-role">{user?.role?.replace('_', ' ')}</p>
            </div>
            <Button
              onClick={handleLogout}
              variant="outline"
              className="w-full justify-start rounded-xl text-sm"
              style={{ borderColor: 'rgba(217, 42, 42, 0.2)', color: '#475569' }}
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
        <div className="p-4 pt-16 sm:p-6 lg:p-10 lg:pt-10">
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
