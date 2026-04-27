import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';

const Login = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) { toast.error('Inserisci email e password'); return; }
    setLoading(true);
    try {
      await login(email, password);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore di autenticazione');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)' }}>
      <div className="w-full max-w-md">
        {/* Logo/Brand */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2" style={{ fontFamily: "'DM Sans', sans-serif" }}>
            Consulenze immobiliari
          </h1>
          <p className="text-sm" style={{ color: 'rgba(255,255,255,0.5)' }}>Sistema di gestione immobiliare</p>
        </div>

        {/* Login Card */}
        <div className="rounded-2xl p-8 shadow-2xl" style={{ background: '#FFFBF5', border: '1px solid rgba(184,134,11,0.15)' }}>
          <h2 className="text-xl font-bold mb-6 text-center" style={{ color: '#9F1239' }}>
            Accesso Amministratore
          </h2>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label className="text-sm font-medium" style={{ color: '#4A3B31' }}>Email</Label>
              <Input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="admin@example.com"
                required
                className="h-11 rounded-xl text-sm"
                style={{ background: 'white', border: '1.5px solid rgba(184,134,11,0.2)', color: '#2C1810' }}
                data-testid="login-email"
              />
            </div>

            <div className="space-y-2">
              <Label className="text-sm font-medium" style={{ color: '#4A3B31' }}>Password</Label>
              <Input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="h-11 rounded-xl text-sm"
                style={{ background: 'white', border: '1.5px solid rgba(184,134,11,0.2)', color: '#2C1810' }}
                data-testid="login-password"
              />
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full h-11 rounded-xl text-sm font-semibold text-white transition-all hover:shadow-lg"
              style={{ background: 'linear-gradient(135deg, #9F1239 0%, #BE123C 100%)' }}
              data-testid="login-submit"
            >
              {loading ? 'Accesso in corso...' : 'Accedi'}
            </Button>
          </form>

          <p className="text-center text-xs mt-6" style={{ color: '#8B7355' }}>
            Accesso riservato agli amministratori autorizzati
          </p>
        </div>

        <p className="text-center text-xs mt-6" style={{ color: 'rgba(255,255,255,0.3)' }}>
          Consulenze immobiliari — Via Vigonovese 114
        </p>
      </div>
    </div>
  );
};

export default Login;
