import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Mail, Lock, ShieldCheck, KeyRound, ArrowLeft } from 'lucide-react';
import ReCAPTCHA from 'react-google-recaptcha';

function formatApiError(detail) {
  if (detail == null) return 'Si e verificato un errore. Riprova.';
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail))
    return detail.map((e) => (e?.msg || JSON.stringify(e))).join(' ');
  if (detail?.msg) return detail.msg;
  return String(detail);
}

const Login = () => {
  const navigate = useNavigate();
  const { loginStep1, verifyOtp } = useAuth();
  const captchaRef = useRef(null);

  // Step management
  const [step, setStep] = useState('credentials'); // 'credentials' | 'otp'
  const [loginSessionId, setLoginSessionId] = useState('');

  // Form fields
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [otpCode, setOtpCode] = useState('');

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Step 1: Submit email + password + captcha
  const handleStep1 = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const captchaToken = captchaRef.current?.getValue() || '';
      const data = await loginStep1(email, password, captchaToken);
      setLoginSessionId(data.login_session_id);
      setStep('otp');
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail) || err.message);
      captchaRef.current?.reset();
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Submit OTP
  const handleStep2 = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await verifyOtp(loginSessionId, otpCode);
      navigate('/');
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail) || err.message);
    } finally {
      setLoading(false);
    }
  };

  const goBackToStep1 = () => {
    setStep('credentials');
    setOtpCode('');
    setError('');
    setLoginSessionId('');
    captchaRef.current?.reset();
  };

  return (
    <div className="min-h-screen flex" data-testid="login-page">
      {/* Left panel - Branding */}
      <div
        className="hidden lg:block lg:w-1/2 bg-cover bg-center relative"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1760246964044-1384f71665b9?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzB8MHwxfHNlYXJjaHwxfHxtb2Rlcm4lMjBjb3Jwb3JhdGUlMjBvZmZpY2UlMjBidWlsZGluZyUyMGV4dGVyaW9yfGVufDB8fHx8MTc3NTczMDUwNHww&ixlib=rb-4.1.0&q=85')`,
        }}
      >
        <div className="absolute inset-0 bg-gradient-to-br from-rose-900/90 to-red-900/90"></div>
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
          <div className="mt-8 p-4 rounded-xl text-center" style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)' }}>
            <ShieldCheck size={20} className="mx-auto mb-2 text-emerald-300" />
            <p className="text-xs text-white/70">Accesso protetto con verifica a 2 fattori</p>
          </div>
        </div>
      </div>

      {/* Right panel - Login form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8" style={{ background: 'linear-gradient(145deg, #FEFDFB 0%, #FAF7F0 100%)' }}>
        <div className="w-full max-w-md luxury-fade-in">

          {/* Step 1: Credentials */}
          {step === 'credentials' && (
            <>
              <div className="mb-10">
                <h2 className="text-3xl font-semibold font-heading mb-2" style={{ color: '#9F1239' }} data-testid="login-title">
                  Accesso Sicuro
                </h2>
                <p className="text-sm" style={{ color: '#8B7355' }}>
                  Inserisci le tue credenziali per accedere al sistema
                </p>
              </div>

              {error && (
                <div className="mb-6 p-4 rounded-xl text-sm" style={{ background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)', color: '#DC2626' }} data-testid="error-message">
                  {error}
                </div>
              )}

              <form onSubmit={handleStep1} className="space-y-5" data-testid="login-form">
                <div>
                  <Label htmlFor="email" className="text-sm font-medium" style={{ color: '#4A3B31' }}>
                    Indirizzo Email
                  </Label>
                  <div className="relative mt-2">
                    <Mail className="absolute left-3.5 top-1/2 transform -translate-y-1/2" size={18} style={{ color: '#B8860B' }} />
                    <Input
                      id="email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="La tua email"
                      required
                      className="pl-11 luxury-input"
                      data-testid="email-input"
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="password" className="text-sm font-medium" style={{ color: '#4A3B31' }}>
                    Password
                  </Label>
                  <div className="relative mt-2">
                    <Lock className="absolute left-3.5 top-1/2 transform -translate-y-1/2" size={18} style={{ color: '#B8860B' }} />
                    <Input
                      id="password"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="La tua password"
                      required
                      className="pl-11 luxury-input"
                      data-testid="password-input"
                    />
                  </div>
                </div>

                <div className="flex justify-center" data-testid="captcha-container">
                  <ReCAPTCHA
                    ref={captchaRef}
                    sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
                  />
                </div>

                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full btn-luxury h-12 text-base"
                  data-testid="login-step1-button"
                >
                  {loading ? 'Verifica in corso...' : 'Continua'}
                </Button>
              </form>
            </>
          )}

          {/* Step 2: OTP Verification */}
          {step === 'otp' && (
            <>
              <div className="mb-10">
                <button
                  onClick={goBackToStep1}
                  className="flex items-center gap-1 text-sm mb-6 transition-colors"
                  style={{ color: '#9F1239' }}
                  data-testid="back-to-step1"
                >
                  <ArrowLeft size={16} /> Torna indietro
                </button>
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 rounded-xl" style={{ background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                    <KeyRound size={24} style={{ color: '#059669' }} />
                  </div>
                  <div>
                    <h2 className="text-2xl font-semibold font-heading" style={{ color: '#9F1239' }} data-testid="otp-title">
                      Verifica OTP
                    </h2>
                    <p className="text-xs" style={{ color: '#8B7355' }}>
                      Codice inviato a {email}
                    </p>
                  </div>
                </div>
                <p className="text-sm" style={{ color: '#8B7355' }}>
                  Inserisci il codice di verifica a 6 cifre. Il codice scade tra 5 minuti.
                </p>
              </div>

              {error && (
                <div className="mb-6 p-4 rounded-xl text-sm" style={{ background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)', color: '#DC2626' }} data-testid="otp-error-message">
                  {error}
                </div>
              )}

              <form onSubmit={handleStep2} className="space-y-5" data-testid="otp-form">
                <div>
                  <Label htmlFor="otp" className="text-sm font-medium" style={{ color: '#4A3B31' }}>
                    Codice OTP
                  </Label>
                  <div className="relative mt-2">
                    <KeyRound className="absolute left-3.5 top-1/2 transform -translate-y-1/2" size={18} style={{ color: '#059669' }} />
                    <Input
                      id="otp"
                      type="text"
                      inputMode="numeric"
                      pattern="[0-9]{6}"
                      maxLength={6}
                      value={otpCode}
                      onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                      placeholder="000000"
                      required
                      className="pl-11 luxury-input text-center text-2xl tracking-[0.5em] font-mono"
                      data-testid="otp-input"
                      autoFocus
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  disabled={loading || otpCode.length !== 6}
                  className="w-full h-12 text-base"
                  style={{
                    background: 'linear-gradient(135deg, #059669 0%, #10B981 100%)',
                    color: 'white',
                    borderRadius: '12px',
                    border: 'none',
                    boxShadow: '0 4px 14px rgba(5, 150, 105, 0.3)',
                  }}
                  data-testid="verify-otp-button"
                >
                  {loading ? 'Verifica in corso...' : 'Verifica e Accedi'}
                </Button>
              </form>

              <div className="mt-6 p-4 rounded-xl text-center" style={{ background: 'rgba(16, 185, 129, 0.04)', border: '1px solid rgba(16, 185, 129, 0.15)' }}>
                <p className="text-xs" style={{ color: '#8B7355' }}>
                  Il codice OTP e visibile nei log del server (modalita sviluppo).
                  <br />In produzione verra inviato via email.
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Login;
