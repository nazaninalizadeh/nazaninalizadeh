import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Users, Home, FileText, CreditCard, DoorOpen, AlertTriangle, TrendingUp, ArrowUpRight } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/dashboard/stats`, { withCredentials: true })
      .then(res => setStats(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center p-12"><div className="luxury-spinner h-10 w-10" /></div>;

  const cards = [
    { label: 'Inquilini', value: stats?.total_tenants || 0, icon: Users, color: '#9F1239', link: '/tenants' },
    { label: 'Proprietari', value: stats?.total_landlords || 0, icon: Home, color: '#B8860B', link: '/landlords' },
    { label: 'Immobili', value: stats?.total_properties || 0, icon: Home, color: '#059669', link: '/properties' },
    { label: 'Stanze', value: stats?.total_rooms || 0, icon: DoorOpen, color: '#7C3AED', link: '/rooms' },
    { label: 'Contratti Attivi', value: stats?.active_contracts || 0, icon: FileText, color: '#2563EB', link: '/contracts' },
  ];

  return (
    <div data-testid="dashboard-page" className="luxury-fade-in">
      <div className="mb-10">
        <h1 className="luxury-title mb-2" data-testid="dashboard-title">Dashboard</h1>
        <p className="luxury-subtitle">Benvenuto, {user?.name}. Ecco il riepilogo della tua attivita.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 mb-10">
        {cards.map((card) => (
          <Link key={card.label} to={card.link} className="luxury-card p-6 hover:shadow-lg transition-all group" data-testid={`stat-${card.label.toLowerCase().replace(/\s/g, '-')}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium" style={{ color: '#8B7355' }}>{card.label}</p>
                <p className="text-3xl font-bold mt-1" style={{ color: card.color }}>{card.value}</p>
              </div>
              <div className="p-3 rounded-xl transition-transform group-hover:scale-110" style={{ background: `${card.color}15` }}>
                <card.icon size={24} style={{ color: card.color }} />
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Financial Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10">
        <div className="luxury-card p-7">
          <h3 className="text-lg font-semibold font-heading mb-5 flex items-center gap-2" style={{ color: '#9F1239' }}>
            <TrendingUp size={20} /> Riepilogo Mese Corrente
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center py-3" style={{ borderBottom: '1px solid rgba(184,134,11,0.1)' }}>
              <span style={{ color: '#5C4A3A' }}>Incassato Questo Mese</span>
              <span className="font-bold text-lg" style={{ color: '#059669' }}>&euro;{(stats?.month_collected || 0).toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center py-3" style={{ borderBottom: '1px solid rgba(184,134,11,0.1)' }}>
              <span style={{ color: '#5C4A3A' }}>Inquilini Pagato</span>
              <Link to="/tenants?status=paid" className="font-bold text-lg hover:underline" style={{ color: '#059669' }}>{stats?.tenants_paid || 0}</Link>
            </div>
            <div className="flex justify-between items-center py-3" style={{ borderBottom: '1px solid rgba(184,134,11,0.1)' }}>
              <span style={{ color: '#5C4A3A' }}>Inquilini Non Pagato</span>
              <Link to="/tenants?status=not_paid" className="font-bold text-lg hover:underline" style={{ color: '#D97706' }}>{stats?.tenants_not_paid || 0}</Link>
            </div>
            <div className="flex justify-between items-center py-3" style={{ borderBottom: '1px solid rgba(184,134,11,0.1)' }}>
              <span style={{ color: '#5C4A3A' }}>Inquilini In Ritardo</span>
              <Link to="/tenants?status=late" className="font-bold text-lg hover:underline" style={{ color: '#DC2626' }}>{stats?.tenants_late || 0}</Link>
            </div>
            <div className="flex justify-between items-center py-3">
              <span style={{ color: '#5C4A3A' }}>Depositi Totali (Garanzia)</span>
              <span className="font-bold text-lg" style={{ color: '#7C3AED' }}>&euro;{(stats?.total_deposits || 0).toLocaleString()}</span>
            </div>
          </div>
        </div>

        <div className="luxury-card p-7">
          <h3 className="text-lg font-semibold font-heading mb-5 flex items-center gap-2" style={{ color: '#9F1239' }}>
            <DoorOpen size={20} /> Occupazione Stanze
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center py-3" style={{ borderBottom: '1px solid rgba(184,134,11,0.1)' }}>
              <span style={{ color: '#5C4A3A' }}>Stanze Totali</span>
              <span className="font-bold text-lg" style={{ color: '#2C1810' }}>{stats?.total_rooms || 0}</span>
            </div>
            <div className="flex justify-between items-center py-3" style={{ borderBottom: '1px solid rgba(184,134,11,0.1)' }}>
              <span style={{ color: '#5C4A3A' }}>Occupate</span>
              <span className="font-bold text-lg" style={{ color: '#059669' }}>{stats?.occupied_rooms || 0}</span>
            </div>
            <div className="flex justify-between items-center py-3">
              <span style={{ color: '#5C4A3A' }}>Libere</span>
              <span className="font-bold text-lg" style={{ color: '#DC2626' }}>{stats?.vacant_rooms || 0}</span>
            </div>
            {stats?.total_rooms > 0 && (
              <div className="mt-3 p-3 rounded-xl" style={{ background: 'rgba(5,150,105,0.05)' }}>
                <div className="h-3 rounded-full overflow-hidden" style={{ background: '#f1f5f9' }}>
                  <div className="h-full rounded-full transition-all" style={{ width: `${(stats.occupied_rooms / stats.total_rooms) * 100}%`, background: 'linear-gradient(90deg, #059669, #10B981)' }} />
                </div>
                <p className="text-xs mt-2 text-center" style={{ color: '#8B7355' }}>
                  {Math.round((stats.occupied_rooms / stats.total_rooms) * 100)}% occupazione
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Payments */}
      {stats?.recent_payments?.length > 0 && (
        <div className="luxury-card p-7">
          <h3 className="text-lg font-semibold font-heading mb-5 flex items-center gap-2" style={{ color: '#9F1239' }}>
            <CreditCard size={20} /> Pagamenti Recenti
          </h3>
          <div className="space-y-3">
            {stats.recent_payments.map((p, i) => (
              <div key={i} className="flex items-center justify-between py-3 px-4 rounded-xl" style={{ background: 'rgba(250,247,240,0.5)', border: '1px solid rgba(184,134,11,0.08)' }}>
                <div>
                  <p className="font-medium text-sm" style={{ color: '#2C1810' }}>{p.tenant_name || 'N/A'}</p>
                  <p className="text-xs" style={{ color: '#8B7355' }}>{p.payment_date} - {p.payment_method}</p>
                </div>
                <span className="font-bold" style={{ color: '#059669' }}>&euro;{p.amount?.toFixed(2)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
