import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { 
  Users, 
  Home, 
  Building2, 
  FileText, 
  Receipt,
  DollarSign,
  TrendingUp
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const { data } = await axios.get(`${API_URL}/dashboard/stats`, {
        withCredentials: true,
      });
      setStats(data);
    } catch (error) {
      toast.error('Impossibile caricare le statistiche dashboard');
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      label: 'Totale Inquilini',
      value: stats?.total_tenants || 0,
      icon: Users,
      color: 'bg-rose-50 text-rose-700',
      testId: 'stat-total-tenants'
    },
    {
      label: 'Totale Proprietari',
      value: stats?.total_landlords || 0,
      icon: Home,
      color: 'bg-green-50 text-green-700',
      testId: 'stat-total-landlords'
    },
    {
      label: 'Totale Immobili',
      value: stats?.total_properties || 0,
      icon: Building2,
      color: 'bg-purple-50 text-purple-700',
      testId: 'stat-total-properties'
    },
    {
      label: 'Immobili Occupati',
      value: stats?.occupied_properties || 0,
      icon: Building2,
      color: 'bg-indigo-50 text-indigo-700',
      testId: 'stat-occupied-properties'
    },
    {
      label: 'Contratti Attivi',
      value: stats?.active_contracts || 0,
      icon: FileText,
      color: 'bg-orange-50 text-orange-700',
      testId: 'stat-active-contracts'
    },
    {
      label: 'Fatture Non Pagate',
      value: stats?.unpaid_invoices || 0,
      icon: Receipt,
      color: 'bg-red-50 text-red-700',
      testId: 'stat-unpaid-invoices'
    },
    {
      label: 'Reddito Mensile',
      value: `€${stats?.total_monthly_income?.toFixed(2) || '0.00'}`,
      icon: TrendingUp,
      color: 'bg-emerald-50 text-emerald-700',
      testId: 'stat-monthly-income'
    },
    {
      label: 'Totale Depositi',
      value: `€${stats?.total_deposits?.toFixed(2) || '0.00'}`,
      icon: DollarSign,
      color: 'bg-cyan-50 text-cyan-700',
      testId: 'stat-total-deposits'
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-rose-700 border-r-transparent" />
      </div>
    );
  }

  return (
    <div data-testid="dashboard-page">
      <div className="mb-8">
        <h1 className="text-4xl font-semibold font-heading text-slate-900 mb-2" data-testid="dashboard-title">
          Dashboard
        </h1>
        <p className="text-slate-600">Panoramica del tuo sistema di gestione immobiliare</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.label}
              className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow"
              data-testid={stat.testId}
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-lg ${stat.color}`}>
                  <Icon size={24} />
                </div>
              </div>
              <h3 className="text-2xl font-semibold text-slate-900 mb-1">{stat.value}</h3>
              <p className="text-sm text-slate-600">{stat.label}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Dashboard;
