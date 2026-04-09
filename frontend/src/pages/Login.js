import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Mail, Lock, ShieldCheck } from 'lucide-react';
import ReCAPTCHA from 'react-google-recaptcha';

const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const captchaRef = useRef(null);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const captchaToken = captchaRef.current?.getValue() || '';
      await login(email, password, captchaToken);
      navigate('/');
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Errore di accesso. Riprova.');
      captchaRef.current?.reset();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex" data-testid="login-page">
      {/* Left panel */}
      <div
        className="hidden lg:block lg:w-1/2 bg-cover bg-center relative"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1760246964044-1384f71665b9?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzB8MHwxfHNlYXJjaHwxfHxtb2Rlcm4lMjBjb3Jwb3JhdGUlMjBvZmZpY2UlMjBidWlsZGluZyUyMGV4dGVyaW9yfGVufDB8fHx8MTc3NTczMDUwNHww&ixlib=rb-4.1.0&q=85')`,
        }}
      >
        <div className="absolute inset-0 bg-gradient-to-br from-rose-900/90 to-red-900/90" />
        <div className="absolute inset-0 flex flex-col justify-center items-center text-white p-12">
          <div className="p-4 rounded-2xl mb-6" style={{ background: 'rgba(255,255,255,0.15)', backdropFilter: 'blur(10px)' }}>
            <ShieldCheck size={48} strokeWidth={1.5} />
          </div>
          <h1
            className="text-5xl font-semibold font-heading mb-3"
            style={{ color: 'white', WebkitTextFillColor: 'white', textShadow: '0 2px 20px rgba(0,0,0,0.3)' }}
            data-testid="brand-name"
          >
            Consulenze immobiliari
          </h1>
          <p className="text-sm text-white/80 mb-2 tracking-wider">Via Vigonovese 114</p>
          <p className="text-lg text-white/70 text-center max-w-md uppercase tracking-widest font-light">
            Affitta &bull; Compra &bull; Vende &bull; Ristruttura
          </p>
        </div>
      </div>

      {/* Right panel */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8" style={{ background: 'linear-gradient(145deg, #FEFDFB 0%, #FAF7F0 100%)' }}>
        <div className="w-full max-w-md luxury-fade-in">
          <div className="mb-10">
            <h2 className="text-3xl font-semibold font-heading mb-2" style={{ color: '#9F1239' }} data-testid="login-title">
              Accesso Sicuro
            </h2>
            <p className="text-sm" style={{ color: '#8B7355' }}>Inserisci le tue credenziali per accedere al sistema</p>
          </div>

          {error && (
            <div className="mb-6 p-4 rounded-xl text-sm" style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: '#DC2626' }} data-testid="error-message">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5" data-testid="login-form">
            <div>
              <Label htmlFor="email" className="text-sm font-medium" style={{ color: '#4A3B31' }}>Indirizzo Email</Label>
              <div className="relative mt-2">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2" size={18} style={{ color: '#B8860B' }} />
                <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="La tua email" required className="pl-11 luxury-input" data-testid="email-input" />
              </div>
            </div>

            <div>
              <Label htmlFor="password" className="text-sm font-medium" style={{ color: '#4A3B31' }}>Password</Label>
              <div className="relative mt-2">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2" size={18} style={{ color: '#B8860B' }} />
                <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="La tua password" required className="pl-11 luxury-input" data-testid="password-input" />
              </div>
            </div>

            <div className="flex justify-center" data-testid="captcha-container">
              <ReCAPTCHA ref={captchaRef} sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI" />
            </div>

            <Button type="submit" disabled={loading} className="w-full btn-luxury h-12 text-base" data-testid="login-button">
              {loading ? 'Accesso in corso...' : 'Accedi'}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
