import React, { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';

const Login = () => {
  const { login, user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  // If already authenticated, send away from /login
  if (!authLoading && user) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) { toast.error('Inserisci email e password'); return; }
    setLoading(true);
    try {
      await login(email, password);
      navigate('/', { replace: true });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore di autenticazione');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: '#F8FAFC' }}>
      <div className="w-full max-w-md">
        {/* Logo/Brand */}
        <div className="text-center mb-8">
          <img
            src="/assets/logo.jpeg"
            alt="Housing in Padova"
            className="mx-auto h-28 w-28 rounded-2xl object-contain bg-white shadow-sm mb-4"
            style={{ border: '1px solid #E2E8F0' }}
            data-testid="login-logo"
          />
          <h1 className="text-3xl font-bold mb-1" style={{ color: '#0F172A', fontFamily: "'DM Sans', sans-serif" }}>
            Housing in Padova
          </h1>
          <p className="text-sm" style={{ color: '#64748B' }}>Sistema di gestione immobiliare</p>
        </div>

        {/* Login Card */}
        <div className="rounded-2xl p-8 shadow-sm" style={{ background: '#FFFFFF', border: '1px solid #E2E8F0' }}>
          <h2 className="text-xl font-semibold mb-6 text-center" style={{ color: '#0B8A3E' }}>
            Accesso Amministratore
          </h2>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label className="text-sm font-medium" style={{ color: '#334155' }}>Email</Label>
              <Input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="admin@example.com"
                required
                className="h-11 rounded-xl text-sm"
                style={{ background: '#FFFFFF', border: '1.5px solid #E2E8F0', color: '#0F172A' }}
                data-testid="login-email"
              />
            </div>

            <div className="space-y-2">
              <Label className="text-sm font-medium" style={{ color: '#334155' }}>Password</Label>
              <Input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="h-11 rounded-xl text-sm"
                style={{ background: '#FFFFFF', border: '1.5px solid #E2E8F0', color: '#0F172A' }}
                data-testid="login-password"
              />
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full h-11 rounded-xl text-sm font-semibold text-white transition-all hover:shadow-md"
              style={{ background: '#0B8A3E' }}
              data-testid="login-submit"
            >
              {loading ? 'Accesso in corso...' : 'Accedi'}
            </Button>
          </form>

          <p className="text-center text-xs mt-6" style={{ color: '#64748B' }}>
            Accesso riservato agli amministratori autorizzati
          </p>
        </div>

        <p className="text-center text-xs mt-6" style={{ color: '#94A3B8' }}>
          Housing in Padova — by Consulenze Immobiliari
        </p>
      </div>
    </div>
  );
};

export default Login;
