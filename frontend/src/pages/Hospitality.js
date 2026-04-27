import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { ScrollText, Download, Plus, Home, DoorOpen, Search, Users, ScanLine, Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const Hospitality = () => {
  const [tenants, setTenants] = useState([]);
  const [properties, setProperties] = useState([]);
  const [landlords, setLandlords] = useState([]);
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [downloading, setDownloading] = useState(null);
  const [createOpen, setCreateOpen] = useState(false);

  // OCR state
  const [ocrStatus, setOcrStatus] = useState('idle');
  const [ocrResult, setOcrResult] = useState(null);
  const [ocrPreview, setOcrPreview] = useState(null);
  const fileRef = useRef(null);

  // Create form
  const [form, setForm] = useState({
    tenant_id: '', property_id: '', room_id: '',
    check_in_date: '', check_out_date: '',
    hosting_type: 'alloggio',
    host_surname: '', host_name: '', host_dob: '', host_birth_place: '',
    host_province: '', host_residence: '',
    property_comune: '', property_provincia: '', property_number: '',
    property_interno: '', property_piano: '', notes: '',
    signature_type: 'owner',
  });

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      const [t, p, r, l] = await Promise.all([
        axios.get(`${API}/tenants`, { withCredentials: true }),
        axios.get(`${API}/properties`, { withCredentials: true }),
        axios.get(`${API}/hospitality/records`, { withCredentials: true }).catch(() => ({ data: [] })),
        axios.get(`${API}/landlords`, { withCredentials: true }).catch(() => ({ data: [] })),
      ]);
      setTenants(t.data);
      setProperties(p.data);
      setRecords(r.data);
      setLandlords(l.data);
    } catch { toast.error('Errore nel caricamento'); }
    setLoading(false);
  };

  const handleDownloadPdf = async (tenantId, tenantName) => {
    setDownloading(tenantId);
    try {
      const response = await axios.get(`${API}/hospitality/pdf/${tenantId}`, {
        withCredentials: true, responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `ospitalita_${tenantName?.replace(/\s/g, '_')}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success('PDF scaricato');
    } catch { toast.error('Errore nel generare il PDF'); }
    setDownloading(null);
  };

  // OCR Scan
  const handleOcrScan = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setOcrPreview(URL.createObjectURL(file));
    setOcrStatus('processing');
    setOcrResult(null);
    const fd = new FormData();
    fd.append('file', file);
    try {
      const { data } = await axios.post(`${API}/ocr/scan`, fd, { withCredentials: true });
      if (data.status === 'completed' && data.extracted_data) {
        setOcrResult(data.extracted_data);
        setOcrStatus('completed');
        // Auto-fill form from OCR
        const d = data.extracted_data;
        setForm(prev => ({
          ...prev,
          // Try to find matching tenant by name or passport
          ...(d.full_name ? {} : {}),
        }));
        toast.success('Documento scansionato! Rivedi i dati e seleziona inquilino.');
      } else {
        setOcrStatus('failed');
        toast.error(data.error || 'Scansione fallita');
      }
    } catch (err) {
      setOcrStatus('failed');
      toast.error(err.response?.data?.detail || 'Errore OCR');
    }
    if (fileRef.current) fileRef.current.value = '';
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    if (!form.tenant_id || !form.property_id || !form.check_in_date) {
      toast.error('Seleziona inquilino, immobile e data check-in');
      return;
    }
    try {
      await axios.post(`${API}/hospitality/records`, form, { withCredentials: true });
      toast.success('Record ospitalita creato');
      setCreateOpen(false);
      setForm({ tenant_id: '', property_id: '', room_id: '', check_in_date: '', check_out_date: '', hosting_type: 'alloggio', host_surname: '', host_name: '', host_dob: '', host_birth_place: '', host_province: '', host_residence: '', property_comune: '', property_provincia: '', property_number: '', property_interno: '', property_piano: '', notes: '' });
      setOcrStatus('idle');
      setOcrResult(null);
      setOcrPreview(null);
      fetchAll();
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore'); }
  };

  const filtered = tenants.filter(t =>
    t.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.property_address?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.nationality?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const sorted = [...filtered].sort((a, b) => (a.room_id && !b.room_id) ? -1 : (!a.room_id && b.room_id) ? 1 : 0);

  if (loading) return <div className="flex items-center justify-center p-12"><div className="luxury-spinner h-10 w-10" /></div>;

  return (
    <div data-testid="hospitality-page" className="luxury-fade-in">
      <div className="mb-8 flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="luxury-title mb-2">Ospitalita</h1>
          <p className="luxury-subtitle">Comunicazione di ospitalita - Art. 7 D.Lvo 286/98</p>
        </div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button className="btn-luxury" data-testid="create-hospitality-button">
              <Plus size={18} className="mr-2" /> Nuova Ospitalita
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto luxury-modal">
            <DialogHeader><DialogTitle>Nuova Comunicazione di Ospitalita</DialogTitle></DialogHeader>
            <form onSubmit={handleCreateSubmit} className="space-y-5">

              {/* OCR Section */}
              <div className="p-4 rounded-xl" style={{ background: 'rgba(159,18,57,0.03)', border: '1px solid rgba(159,18,57,0.1)' }}>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-semibold flex items-center gap-2" style={{ color: '#9F1239' }}>
                    <ScanLine size={16} /> Scansione OCR Documento
                  </h4>
                  <label data-testid="ocr-upload-button">
                    <input type="file" ref={fileRef} className="hidden" accept="image/jpeg,image/png,image/webp" onChange={handleOcrScan} />
                    <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs cursor-pointer" style={{ background: '#9F1239', color: 'white' }}>
                      <ScanLine size={14} /> Scansiona Documento
                    </span>
                  </label>
                </div>
                {ocrStatus === 'processing' && (
                  <div className="flex items-center gap-2 text-sm" style={{ color: '#B8860B' }}>
                    <Loader2 size={16} className="animate-spin" /> Analisi in corso...
                  </div>
                )}
                {ocrStatus === 'completed' && ocrResult && (
                  <div className="flex items-center gap-2 text-sm" style={{ color: '#059669' }}>
                    <CheckCircle2 size={16} /> Scansione completata - {ocrResult.full_name || 'Dati estratti'}
                    {ocrResult.passport_number && <span className="ml-2 text-xs font-mono">Pass: {ocrResult.passport_number}</span>}
                  </div>
                )}
                {ocrStatus === 'failed' && (
                  <div className="flex items-center gap-2 text-sm" style={{ color: '#DC2626' }}>
                    <XCircle size={16} /> Scansione fallita - Riprova
                  </div>
                )}
                {ocrPreview && <img src={ocrPreview} alt="Preview" className="mt-2 max-h-32 rounded-lg object-contain" />}
              </div>

              {/* Tenant + Property Selection */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Inquilino (Ospitato) *</Label>
                  <Select value={form.tenant_id} onValueChange={v => setForm({ ...form, tenant_id: v })}>
                    <SelectTrigger><SelectValue placeholder="Seleziona inquilino" /></SelectTrigger>
                    <SelectContent>
                      {tenants.map(t => (
                        <SelectItem key={t.id} value={t.id}>
                          {t.full_name}{t.property_address ? ` — ${t.property_address}` : ''}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Immobile *</Label>
                  <Select value={form.property_id} onValueChange={v => {
                    const prop = properties.find(p => p.id === v);
                    const ll = prop ? landlords.find(l => l.id === prop.landlord_id) : null;
                    const llName = ll?.full_name || '';
                    const llParts = llName.includes(' ') ? llName.split(' ') : [llName, ''];
                    setForm(prev => ({
                      ...prev, property_id: v,
                      host_surname: llParts[0] || prev.host_surname,
                      host_name: llParts.slice(1).join(' ') || prev.host_name,
                    }));
                  }}>
                    <SelectTrigger><SelectValue placeholder="Seleziona immobile" /></SelectTrigger>
                    <SelectContent>
                      {properties.map(p => (
                        <SelectItem key={p.id} value={p.id}>{p.property_code} — {p.address}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Dates */}
              <div className="grid grid-cols-2 gap-4">
                <div><Label>Data Check-in (DAL) *</Label><Input type="date" value={form.check_in_date} onChange={e => setForm({ ...form, check_in_date: e.target.value })} required className="luxury-input" /></div>
                <div><Label>Data Check-out (FINO AL)</Label><Input type="date" value={form.check_out_date} onChange={e => setForm({ ...form, check_out_date: e.target.value })} className="luxury-input" /></div>
              </div>

              {/* Host (Dichiarante) */}
              <div className="p-3 rounded-xl" style={{ background: 'rgba(184,134,11,0.04)', border: '1px solid rgba(184,134,11,0.1)' }}>
                <h4 className="text-xs font-semibold uppercase mb-3" style={{ color: '#8B7355' }}>Dichiarante (Ospitante)</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div><Label className="text-xs">Cognome</Label><Input value={form.host_surname} onChange={e => setForm({ ...form, host_surname: e.target.value })} className="luxury-input h-8 text-sm" /></div>
                  <div><Label className="text-xs">Nome</Label><Input value={form.host_name} onChange={e => setForm({ ...form, host_name: e.target.value })} className="luxury-input h-8 text-sm" /></div>
                  <div><Label className="text-xs">Data Nascita</Label><Input type="date" value={form.host_dob} onChange={e => setForm({ ...form, host_dob: e.target.value })} className="luxury-input h-8 text-sm" /></div>
                  <div><Label className="text-xs">Luogo Nascita</Label><Input value={form.host_birth_place} onChange={e => setForm({ ...form, host_birth_place: e.target.value })} className="luxury-input h-8 text-sm" /></div>
                  <div><Label className="text-xs">Provincia</Label><Input value={form.host_province} onChange={e => setForm({ ...form, host_province: e.target.value })} className="luxury-input h-8 text-sm" /></div>
                  <div><Label className="text-xs">Residenza</Label><Input value={form.host_residence} onChange={e => setForm({ ...form, host_residence: e.target.value })} className="luxury-input h-8 text-sm" /></div>
                </div>
              </div>

              {/* Property Details */}
              <div className="p-3 rounded-xl" style={{ background: 'rgba(184,134,11,0.04)', border: '1px solid rgba(184,134,11,0.1)' }}>
                <h4 className="text-xs font-semibold uppercase mb-3" style={{ color: '#8B7355' }}>Dettagli Immobile</h4>
                <div className="grid grid-cols-3 gap-3">
                  <div><Label className="text-xs">Comune</Label><Input value={form.property_comune} onChange={e => setForm({ ...form, property_comune: e.target.value })} className="luxury-input h-8 text-sm" /></div>
                  <div><Label className="text-xs">Provincia</Label><Input value={form.property_provincia} onChange={e => setForm({ ...form, property_provincia: e.target.value })} className="luxury-input h-8 text-sm" /></div>
                  <div><Label className="text-xs">Numero</Label><Input value={form.property_number} onChange={e => setForm({ ...form, property_number: e.target.value })} className="luxury-input h-8 text-sm" /></div>
                  <div><Label className="text-xs">Interno</Label><Input value={form.property_interno} onChange={e => setForm({ ...form, property_interno: e.target.value })} className="luxury-input h-8 text-sm" /></div>
                  <div><Label className="text-xs">Piano</Label><Input value={form.property_piano} onChange={e => setForm({ ...form, property_piano: e.target.value })} className="luxury-input h-8 text-sm" /></div>
                </div>
              </div>

              <div><Label>Note</Label><Input value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} className="luxury-input" /></div>

              {/* Firma / Signature */}
              <div className="p-3 rounded-xl" style={{ background: 'rgba(159,18,57,0.03)', border: '1px solid rgba(159,18,57,0.1)' }}>
                <h4 className="text-xs font-semibold uppercase mb-3" style={{ color: '#9F1239' }}>Firma</h4>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { value: 'owner', label: 'Proprietario' },
                    { value: 'agency', label: 'Agenzia' },
                    { value: 'blank', label: 'Vuoto' },
                  ].map(opt => (
                    <button key={opt.value} type="button"
                      onClick={() => setForm({ ...form, signature_type: opt.value })}
                      className={`p-2 rounded-lg text-xs font-medium text-center transition-all ${form.signature_type === opt.value ? 'ring-2 ring-rose-500' : ''}`}
                      style={{ background: form.signature_type === opt.value ? 'rgba(159,18,57,0.08)' : 'white', color: '#9F1239', border: '1px solid rgba(159,18,57,0.15)' }}>
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => setCreateOpen(false)} className="rounded-xl">Annulla</Button>
                <Button type="submit" className="btn-luxury">Crea e Salva</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Existing Records */}
      {records.length > 0 && (
        <div className="luxury-card p-5 mb-6">
          <h3 className="text-sm font-semibold mb-3" style={{ color: '#9F1239' }}>Record Salvati ({records.length})</h3>
          <div className="space-y-2">
            {records.map(r => (
              <div key={r.id} className="flex items-center justify-between p-3 rounded-xl hover:bg-rose-50/20" style={{ border: '1px solid rgba(184,134,11,0.08)' }}>
                <div>
                  <span className="font-medium text-sm" style={{ color: '#2C1810' }}>{r.tenant_name}</span>
                  <span className="text-xs ml-3" style={{ color: '#8B7355' }}>{r.property_address} | {r.check_in_date} → {r.check_out_date || 'Indeterminato'}</span>
                </div>
                <Button size="sm" className="btn-luxury text-xs" onClick={() => handleDownloadPdf(r.tenant_id, r.tenant_name)}>
                  <Download size={14} className="mr-1" /> PDF
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search */}
      <div className="luxury-card p-4 mb-6">
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2" size={18} style={{ color: '#B8860B' }} />
          <Input placeholder="Cerca inquilino..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="pl-11 luxury-input" />
        </div>
      </div>

      {/* Tenant List for Quick PDF */}
      <h3 className="text-sm font-semibold mb-3" style={{ color: '#8B7355' }}>Genera PDF Rapido per Inquilino</h3>
      <div className="space-y-2">
        {sorted.map(tenant => (
          <div key={tenant.id} className="luxury-card p-4 flex items-center justify-between hover:shadow-md transition-all" data-testid={`hospitality-tenant-${tenant.id}`}>
            <div className="flex items-center gap-3 min-w-0">
              <Users size={16} style={{ color: tenant.room_id ? '#059669' : '#94A3B8' }} />
              <div className="min-w-0">
                <Link to={`/tenants/${tenant.id}`} className="font-medium text-sm hover:underline truncate block" style={{ color: '#9F1239' }}>
                  {tenant.full_name}
                </Link>
                <div className="flex items-center gap-2 mt-0.5 text-xs" style={{ color: '#8B7355' }}>
                  {tenant.nationality && <span>{tenant.nationality}</span>}
                  {tenant.property_address && <span className="inline-flex items-center gap-1"><Home size={10} /> {tenant.property_address}</span>}
                  {tenant.room_number && <span className="inline-flex items-center gap-1"><DoorOpen size={10} /> Stanza {tenant.room_number}</span>}
                </div>
              </div>
            </div>
            <Button className="btn-luxury shrink-0 text-xs" disabled={downloading === tenant.id}
              onClick={() => handleDownloadPdf(tenant.id, tenant.full_name)} data-testid={`download-hospitality-${tenant.id}`}>
              <Download size={14} className="mr-1" /> {downloading === tenant.id ? '...' : 'PDF'}
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Hospitality;
