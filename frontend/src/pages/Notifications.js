import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { Bell, AlertTriangle, Clock, FileText, Cake } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const severityConfig = {
  high: { icon: AlertTriangle, color: '#DC2626', bg: 'rgba(239,68,68,0.06)', border: 'rgba(239,68,68,0.2)' },
  medium: { icon: Clock, color: '#D97706', bg: 'rgba(217,119,6,0.06)', border: 'rgba(217,119,6,0.2)' },
  low: { icon: FileText, color: '#2563EB', bg: 'rgba(37,99,235,0.06)', border: 'rgba(37,99,235,0.2)' },
  info: { icon: Cake, color: '#7C3AED', bg: 'rgba(124,58,237,0.06)', border: 'rgba(124,58,237,0.2)' },
};

const Notifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch notifications AND mark them seen so the badge resets to 0.
    // Layout polls /notifications/count every 60s, so the badge will catch up.
    axios.get(`${API}/notifications`, { withCredentials: true })
      .then(res => setNotifications(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
    axios.post(`${API}/notifications/mark-seen`, {}, { withCredentials: true })
      .then(() => window.dispatchEvent(new Event('notifications:seen')))
      .catch(() => {});
  }, []);

  if (loading) return <div className="flex items-center justify-center p-12"><div className="luxury-spinner h-10 w-10" /></div>;

  return (
    <div data-testid="notifications-page" className="luxury-fade-in">
      <div className="mb-10">
        <h1 className="luxury-title mb-2">Notifiche e Promemoria</h1>
        <p className="luxury-subtitle">Pagamenti scaduti, contratti in scadenza e compleanni</p>
      </div>

      {notifications.length === 0 ? (
        <div className="luxury-card p-14 text-center">
          <Bell className="mx-auto mb-4" size={64} style={{ color: 'rgba(217,42,42,0.3)' }} />
          <h3 className="text-lg font-semibold mb-2" style={{ color: '#0F172A' }}>Nessuna Notifica</h3>
          <p style={{ color: '#64748B' }}>Tutto in ordine!</p>
        </div>
      ) : (
        <div className="space-y-3">
          {notifications.map((n, i) => {
            const cfg = severityConfig[n.severity] || severityConfig.info;
            const Icon = cfg.icon;
            return (
              <div key={i} className="luxury-card p-5 flex items-start gap-4" style={{ borderLeft: `4px solid ${cfg.color}` }}>
                <div className="p-2.5 rounded-xl" style={{ background: cfg.bg }}>
                  <Icon size={20} style={{ color: cfg.color }} />
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-sm" style={{ color: '#0F172A' }}>{n.title}</p>
                  <p className="text-sm mt-1" style={{ color: '#475569' }}>{n.message}</p>
                  <p className="text-xs mt-2" style={{ color: '#64748B' }}>{n.date}</p>
                </div>
                {n.tenant_id && (
                  <Link to={`/tenants/${n.tenant_id}`} className="text-xs underline whitespace-nowrap" style={{ color: '#0B8A3E' }}>
                    Vedi Profilo
                  </Link>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default Notifications;
