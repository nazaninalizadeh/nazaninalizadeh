import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { ScrollText, Download, Home, DoorOpen, Search, Users } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const Hospitality = () => {
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [downloading, setDownloading] = useState(null);

  useEffect(() => { fetchTenants(); }, []);

  const fetchTenants = async () => {
    try {
      const { data } = await axios.get(`${API}/tenants`, { withCredentials: true });
      setTenants(data);
    } catch { toast.error('Errore nel caricamento'); }
    setLoading(false);
  };

  const handleDownloadPdf = async (tenant) => {
    setDownloading(tenant.id);
    try {
      const response = await axios.get(`${API}/hospitality/pdf/${tenant.id}`, {
        withCredentials: true,
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `ospitalita_${tenant.full_name?.replace(/\s/g, '_')}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success('PDF Ospitalita scaricato');
    } catch {
      toast.error('Errore nel generare il PDF');
    }
    setDownloading(null);
  };

  const filtered = tenants.filter(t =>
    t.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.property_address?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.nationality?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Tenants with room assignments first
  const sorted = [...filtered].sort((a, b) => {
    if (a.room_id && !b.room_id) return -1;
    if (!a.room_id && b.room_id) return 1;
    return 0;
  });

  if (loading) return <div className="flex items-center justify-center p-12"><div className="luxury-spinner h-10 w-10" /></div>;

  return (
    <div data-testid="hospitality-page" className="luxury-fade-in">
      <div className="mb-8">
        <h1 className="luxury-title mb-2">Ospitalita</h1>
        <p className="luxury-subtitle">Dichiarazioni di ospitalita per gli inquilini</p>
      </div>

      {/* Info Banner */}
      <div className="luxury-card p-5 mb-6" style={{ background: 'rgba(159,18,57,0.03)', border: '1px solid rgba(159,18,57,0.1)' }}>
        <div className="flex items-start gap-3">
          <ScrollText size={20} style={{ color: '#9F1239', marginTop: 2 }} />
          <div>
            <p className="text-sm font-medium" style={{ color: '#2C1810' }}>
              Genera la Dichiarazione di Ospitalita (art. 12 D.L. 59/1978) per ogni inquilino.
            </p>
            <p className="text-xs mt-1" style={{ color: '#8B7355' }}>
              Il PDF include dati dell'inquilino, documento d'identita, immobile, stanza e proprietario.
              I dati vengono automaticamente dal sistema - nessun inserimento manuale necessario.
            </p>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="luxury-card p-4 mb-6">
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2" size={18} style={{ color: '#B8860B' }} />
          <Input placeholder="Cerca inquilino, indirizzo, nazionalita..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="pl-11 luxury-input" />
        </div>
      </div>

      {/* Tenant Cards */}
      {sorted.length === 0 ? (
        <div className="luxury-card p-14 text-center">
          <Users className="mx-auto mb-4" size={48} style={{ color: 'rgba(184,134,11,0.3)' }} />
          <p style={{ color: '#8B7355' }}>Nessun inquilino trovato</p>
        </div>
      ) : (
        <div className="space-y-3">
          {sorted.map(tenant => (
            <div key={tenant.id} className="luxury-card p-5 flex items-center justify-between hover:shadow-md transition-all" data-testid={`hospitality-tenant-${tenant.id}`}>
              <div className="flex items-center gap-4 min-w-0">
                <div className="p-2 rounded-xl shrink-0" style={{ background: tenant.room_id ? 'rgba(5,150,105,0.1)' : 'rgba(148,163,184,0.1)' }}>
                  <Users size={18} style={{ color: tenant.room_id ? '#059669' : '#94A3B8' }} />
                </div>
                <div className="min-w-0">
                  <Link to={`/tenants/${tenant.id}`} className="font-semibold text-sm hover:underline block truncate" style={{ color: '#9F1239' }}>
                    {tenant.full_name}
                  </Link>
                  <div className="flex items-center gap-3 mt-1 flex-wrap">
                    {tenant.nationality && (
                      <span className="text-xs" style={{ color: '#8B7355' }}>{tenant.nationality}</span>
                    )}
                    {tenant.passport_number && (
                      <span className="text-xs font-mono" style={{ color: '#8B7355' }}>Pass: {tenant.passport_number}</span>
                    )}
                    {tenant.property_address ? (
                      <span className="inline-flex items-center gap-1 text-xs" style={{ color: '#4A3B31' }}>
                        <Home size={11} /> {tenant.property_address}
                      </span>
                    ) : null}
                    {tenant.room_number ? (
                      <span className="inline-flex items-center gap-1 text-xs" style={{ color: '#4A3B31' }}>
                        <DoorOpen size={11} /> Stanza {tenant.room_number}
                      </span>
                    ) : null}
                    {!tenant.property_address && !tenant.room_number && (
                      <span className="text-xs italic" style={{ color: '#94A3B8' }}>Non assegnato a immobile</span>
                    )}
                  </div>
                </div>
              </div>
              <Button
                className="btn-luxury shrink-0"
                disabled={downloading === tenant.id}
                onClick={() => handleDownloadPdf(tenant)}
                data-testid={`download-hospitality-${tenant.id}`}
              >
                <Download size={15} className="mr-2" />
                {downloading === tenant.id ? 'Generazione...' : 'Scarica PDF'}
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Hospitality;
