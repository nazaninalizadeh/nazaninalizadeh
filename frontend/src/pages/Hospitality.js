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
import { fmtDate } from '../lib/format';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const Hospitality = () => {
  const [tenants, setTenants] = useState([]);
  const [properties, setProperties] = useState([]);
  const [landlords, setLandlords] = useState([]);
  const [records, setRecords] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [downloading, setDownloading] = useState(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);  // record id being edited (null = create mode)

  // OCR state
  const [ocrStatus, setOcrStatus] = useState('idle');
  const [ocrResult, setOcrResult] = useState(null);
  const [ocrPreview, setOcrPreview] = useState(null);
  const fileRef = useRef(null);

  // Create form
  const [form, setForm] = useState({
    mode: 'tenant',
    tenant_id: '', property_id: '', room_id: '', landlord_id: '', contract_id: '',
    check_in_date: '', check_out_date: '',
    hosting_type: 'alloggio',
    // Manual-mode guest fields
    guest_surname: '', guest_name: '', guest_dob: '', guest_birth_place: '',
    guest_nationality: '', guest_passport: '', guest_residence: '',
    host_surname: '', host_name: '', host_dob: '', host_birth_place: '',
    host_province: '', host_residence: '',
    property_comune: '', property_provincia: '', property_number: '',
    property_interno: '', property_piano: '', notes: '',
    signature_type: 'owner',
  });

  // Auto-fill landlord, property, contract & dates when tenant changes
  const handleTenantChange = (tid) => {
    const t = tenants.find((x) => x.id === tid);
    if (!t) { setForm((f) => ({ ...f, tenant_id: tid })); return; }
    const property = properties.find((p) => p.id === t.property_id);
    const ll = property ? landlords.find((l) => l.id === property.landlord_id) : null;
    const ctr = contracts.find((c) => c.tenant_id === tid && c.status === 'active') ||
                contracts.find((c) => c.tenant_id === tid);
    setForm((f) => ({
      ...f,
      tenant_id: tid,
      property_id: t.property_id || f.property_id,
      room_id: t.room_id || f.room_id,
      landlord_id: ll?.id || f.landlord_id,
      contract_id: ctr?.id || f.contract_id,
      check_in_date: ctr?.start_date || f.check_in_date,
      check_out_date: ctr?.end_date || f.check_out_date,
      property_comune: property?.comune || property?.city || f.property_comune,
      property_provincia: property?.province || f.property_provincia,
    }));
  };

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      const [t, p, r, l, ct] = await Promise.all([
        axios.get(`${API}/tenants`, { withCredentials: true }),
        axios.get(`${API}/properties`, { withCredentials: true }),
        axios.get(`${API}/hospitality/records`, { withCredentials: true }).catch(() => ({ data: [] })),
        axios.get(`${API}/landlords`, { withCredentials: true }).catch(() => ({ data: [] })),
        axios.get(`${API}/contracts`, { withCredentials: true }).catch(() => ({ data: [] })),
      ]);
      setTenants(t.data);
      setProperties(p.data);
      setRecords(r.data);
      setLandlords(l.data);
      setContracts(ct.data);
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

  const handleDownloadPdfByRecord = async (record) => {
    setDownloading(record.id);
    try {
      const isManual = (record.mode === 'manual') || !record.tenant_id;
      const url = isManual
        ? `${API}/hospitality/pdf/record/${record.id}`
        : `${API}/hospitality/pdf/${record.tenant_id}`;
      const response = await axios.get(url, { withCredentials: true, responseType: 'blob' });
      const objUrl = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement('a');
      a.href = objUrl;
      a.download = `ospitalita_${(record.tenant_name || 'record').replace(/\s/g, '_')}.pdf`;
      a.click();
      window.URL.revokeObjectURL(objUrl);
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
        // Auto-fill all hospitality fields the OCR can supply.
        const d = data.extracted_data;
        const surname = d.surname || (d.full_name ? d.full_name.split(' ')[0] : '');
        const name = d.name || (d.full_name ? d.full_name.split(' ').slice(1).join(' ') : '');
        setForm(prev => ({
          ...prev,
          // Guest section will be filled when tenant is selected; here we focus on host/declarant fields
          // when the OCR doc is the OWNER's ID (typical Hospitality flow scans the host's CI).
          host_surname: prev.host_surname || surname,
          host_name: prev.host_name || name,
          host_dob: prev.host_dob || d.date_of_birth || '',
          host_birth_place: prev.host_birth_place || d.place_of_birth || '',
          host_province: prev.host_province || d.province_of_birth || '',
          host_residence: prev.host_residence || d.residence || '',
          // doc-related
          guest_doc_authority: d.issuing_authority || prev.guest_doc_authority || '',
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
    if (form.mode === 'manual') {
      if (!form.landlord_id || !form.contract_id) {
        toast.error('In modalita manuale: seleziona Proprietario e Contratto');
        return;
      }
    } else {
      if (!form.tenant_id || !form.property_id || !form.check_in_date) {
        toast.error('Seleziona inquilino, immobile e data check-in');
        return;
      }
    }
    try {
      if (editingId) {
        await axios.put(`${API}/hospitality/records/${editingId}`, form, { withCredentials: true });
        toast.success('Record ospitalita aggiornato');
      } else {
        await axios.post(`${API}/hospitality/records`, form, { withCredentials: true });
        toast.success('Record ospitalita creato');
      }
      setCreateOpen(false);
      setEditingId(null);
      setForm({ mode: 'tenant', tenant_id: '', property_id: '', room_id: '', landlord_id: '', contract_id: '', check_in_date: '', check_out_date: '', hosting_type: 'alloggio', guest_surname: '', guest_name: '', guest_dob: '', guest_birth_place: '', guest_nationality: '', guest_passport: '', guest_residence: '', host_surname: '', host_name: '', host_dob: '', host_birth_place: '', host_province: '', host_residence: '', property_comune: '', property_provincia: '', property_number: '', property_interno: '', property_piano: '', notes: '', signature_type: 'owner' });
      setOcrStatus('idle');
      setOcrResult(null);
      setOcrPreview(null);
      fetchAll();
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore'); }
  };

  const handleDeleteRecord = async (id) => {
    if (!window.confirm('Eliminare questo record di ospitalita?')) return;
    try {
      await axios.delete(`${API}/hospitality/records/${id}`, { withCredentials: true });
      toast.success('Record eliminato');
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
        <Dialog open={createOpen} onOpenChange={(open) => { setCreateOpen(open); if (!open) setEditingId(null); }}>
          <DialogTrigger asChild>
            <Button className="btn-luxury" data-testid="create-hospitality-button">
              <Plus size={18} className="mr-2" /> Nuova Ospitalita
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto luxury-modal" aria-describedby="hospitality-dialog-desc">
            <DialogHeader>
              <DialogTitle>{editingId ? 'Modifica Comunicazione di Ospitalita' : 'Nuova Comunicazione di Ospitalita'}</DialogTitle>
              <p id="hospitality-dialog-desc" className="text-xs text-stone-500">Crea da inquilino esistente o manualmente con Proprietario + Contratto.</p>
            </DialogHeader>
            <form onSubmit={handleCreateSubmit} className="space-y-5">

              {/* Mode toggle */}
              <div className="grid grid-cols-2 gap-2 p-1 rounded-xl" style={{ background: 'rgba(217,42,42,0.06)' }}>
                <button type="button" data-testid="hospitality-mode-tenant"
                  onClick={() => setForm(prev => ({ ...prev, mode: 'tenant' }))}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${form.mode === 'tenant' ? 'bg-white shadow-sm' : ''}`}
                  style={{ color: '#0B8A3E' }}>
                  Da Inquilino
                </button>
                <button type="button" data-testid="hospitality-mode-manual"
                  onClick={() => setForm(prev => ({ ...prev, mode: 'manual', tenant_id: '' }))}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${form.mode === 'manual' ? 'bg-white shadow-sm' : ''}`}
                  style={{ color: '#0B8A3E' }}>
                  Crea Manualmente
                </button>
              </div>

              {/* OCR Section */}
              <div className="p-4 rounded-xl" style={{ background: 'rgba(11,138,62,0.03)', border: '1px solid rgba(11,138,62,0.1)' }}>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-semibold flex items-center gap-2" style={{ color: '#0B8A3E' }}>
                    <ScanLine size={16} /> Scansione OCR Documento
                  </h4>
                  <label data-testid="ocr-upload-button">
                    <input type="file" ref={fileRef} className="hidden" accept="image/jpeg,image/png,image/webp" onChange={handleOcrScan} />
                    <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs cursor-pointer" style={{ background: '#0B8A3E', color: 'white' }}>
                      <ScanLine size={14} /> Scansiona Documento
                    </span>
                  </label>
                </div>
                {ocrStatus === 'processing' && (
                  <div className="flex items-center gap-2 text-sm" style={{ color: '#D92A2A' }}>
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

              {/* Tenant + Property Selection (tenant mode only) */}
              {form.mode === 'tenant' && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <Label>Inquilino (Ospitato) *</Label>
                  <Select value={form.tenant_id} onValueChange={async v => {
                    setForm(prev => ({ ...prev, tenant_id: v }));
                    // Auto-fill dates from active contract + property from tenant.property_id
                    try {
                      const tenant = tenants.find(t => t.id === v);
                      if (tenant) {
                        // Find active contract for this tenant
                        const cr = await axios.get(`${API}/contracts`, { withCredentials: true });
                        const contract = cr.data.find(c => c.tenant_id === v && c.status === 'active');
                        const start = contract?.start_date || '';
                        const end = contract?.end_date || (start ? (() => { const d = new Date(start); d.setFullYear(d.getFullYear() + 1); return d.toISOString().split('T')[0]; })() : '');
                        const prop = tenant.property_id ? properties.find(p => p.id === tenant.property_id) : null;
                        const ll = prop ? landlords.find(l => l.id === prop.landlord_id) : null;
                        const llName = ll?.full_name || '';
                        const llParts = llName.includes(' ') ? llName.split(' ') : [llName, ''];
                        setForm(prev => ({
                          ...prev, tenant_id: v,
                          property_id: prop?.id || prev.property_id,
                          check_in_date: start || prev.check_in_date,
                          check_out_date: end || prev.check_out_date,
                          host_surname: llParts[0] || prev.host_surname,
                          host_name: llParts.slice(1).join(' ') || prev.host_name,
                          host_dob: ll?.date_of_birth || prev.host_dob,
                          host_birth_place: ll?.place_of_birth || prev.host_birth_place,
                          host_province: ll?.province_of_birth || prev.host_province,
                          host_residence: ll?.residence || prev.host_residence,
                          property_comune: prop?.city || prev.property_comune,
                          property_provincia: prop?.province || prev.property_provincia,
                        }));
                      }
                    } catch {}
                  }}>
                    <SelectTrigger data-testid="hospitality-tenant-select"><SelectValue placeholder="Seleziona inquilino" /></SelectTrigger>
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
              )}

              {/* Proprietario + Contratto (always required, especially in manual mode) */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <Label>Proprietario (Dichiarante) *</Label>
                  <Select value={form.landlord_id} onValueChange={(v) => {
                    const ll = landlords.find((l) => l.id === v);
                    const llName = ll?.full_name || '';
                    const parts = llName.split(' ');
                    setForm((prev) => ({
                      ...prev, landlord_id: v,
                      host_surname: ll?.surname || (parts.length >= 2 ? parts[parts.length - 1] : llName) || prev.host_surname,
                      host_name: ll?.name || (parts.length >= 2 ? parts.slice(0, -1).join(' ') : '') || prev.host_name,
                      host_dob: ll?.date_of_birth || prev.host_dob,
                      host_birth_place: ll?.place_of_birth || prev.host_birth_place,
                      host_province: ll?.province_of_birth || prev.host_province,
                      host_residence: ll?.residence || prev.host_residence,
                    }));
                  }}>
                    <SelectTrigger data-testid="hospitality-landlord-select"><SelectValue placeholder="Seleziona proprietario" /></SelectTrigger>
                    <SelectContent>
                      {landlords.map((l) => (
                        <SelectItem key={l.id} value={l.id}>{l.full_name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Contratto {form.mode === 'manual' ? '*' : '(auto)'}</Label>
                  <Select value={form.contract_id} onValueChange={(v) => {
                    const ctr = contracts.find((c) => c.id === v);
                    // In manual mode try to also pre-fill property + guest fields from the contract
                    setForm((prev) => {
                      const next = {
                        ...prev, contract_id: v,
                        check_in_date: ctr?.start_date || prev.check_in_date,
                        check_out_date: ctr?.end_date || prev.check_out_date,
                      };
                      if (prev.mode === 'manual' && ctr) {
                        const t = tenants.find(x => x.id === ctr.tenant_id);
                        const prop = ctr.property_id ? properties.find(p => p.id === ctr.property_id) : null;
                        if (t) {
                          const tParts = (t.full_name || '').split(' ');
                          next.guest_surname = prev.guest_surname || (tParts.length >= 2 ? tParts[tParts.length - 1] : (tParts[0] || ''));
                          next.guest_name = prev.guest_name || (tParts.length >= 2 ? tParts.slice(0, -1).join(' ') : '');
                          next.guest_dob = prev.guest_dob || t.date_of_birth || '';
                          next.guest_birth_place = prev.guest_birth_place || t.place_of_birth || '';
                          next.guest_nationality = prev.guest_nationality || t.nationality || '';
                          next.guest_passport = prev.guest_passport || t.passport_number || '';
                          next.guest_residence = prev.guest_residence || t.address || '';
                        }
                        if (prop) {
                          next.property_id = prev.property_id || prop.id;
                          next.property_comune = prev.property_comune || prop.comune || prop.city || '';
                          next.property_provincia = prev.property_provincia || prop.province || '';
                          next.property_number = prev.property_number || prop.civico || '';
                        }
                      }
                      return next;
                    });
                  }}>
                    <SelectTrigger data-testid="hospitality-contract-select"><SelectValue placeholder="Seleziona contratto" /></SelectTrigger>
                    <SelectContent>
                      {contracts.filter((c) => form.mode === 'manual' ? true : (!form.tenant_id || c.tenant_id === form.tenant_id)).map((c) => (
                        <SelectItem key={c.id} value={c.id}>{c.contract_number} ({c.start_date} → {c.end_date})</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Manual-mode guest fields (only when mode=manual) */}
              {form.mode === 'manual' && (
                <div className="p-3 rounded-xl" style={{ background: 'rgba(11,138,62,0.04)', border: '1px solid rgba(11,138,62,0.12)' }}>
                  <h4 className="text-xs font-semibold uppercase mb-3" style={{ color: '#0B8A3E' }}>Ospitato (Manuale)</h4>
                  <div className="grid grid-cols-2 gap-3">
                    <div><Label className="text-xs">Cognome</Label><Input data-testid="hospitality-guest-surname" value={form.guest_surname} onChange={e => setForm({ ...form, guest_surname: e.target.value })} className="luxury-input h-8 text-sm" /></div>
                    <div><Label className="text-xs">Nome</Label><Input data-testid="hospitality-guest-name" value={form.guest_name} onChange={e => setForm({ ...form, guest_name: e.target.value })} className="luxury-input h-8 text-sm" /></div>
                    <div><Label className="text-xs">Data Nascita</Label><Input type="date" value={form.guest_dob} onChange={e => setForm({ ...form, guest_dob: e.target.value })} className="luxury-input h-8 text-sm" /></div>
                    <div><Label className="text-xs">Luogo Nascita</Label><Input value={form.guest_birth_place} onChange={e => setForm({ ...form, guest_birth_place: e.target.value })} className="luxury-input h-8 text-sm" /></div>
                    <div><Label className="text-xs">Nazionalita</Label><Input value={form.guest_nationality} onChange={e => setForm({ ...form, guest_nationality: e.target.value })} className="luxury-input h-8 text-sm" /></div>
                    <div><Label className="text-xs">Passaporto</Label><Input value={form.guest_passport} onChange={e => setForm({ ...form, guest_passport: e.target.value })} className="luxury-input h-8 text-sm" /></div>
                    <div className="col-span-2"><Label className="text-xs">Residenza</Label><Input value={form.guest_residence} onChange={e => setForm({ ...form, guest_residence: e.target.value })} className="luxury-input h-8 text-sm" /></div>
                  </div>
                </div>
              )}

              {/* Dates */}
              <div className="grid grid-cols-2 gap-4">
                <div><Label>Data Check-in (DAL) {form.mode === 'tenant' ? '*' : ''}</Label><Input type="date" value={form.check_in_date} onChange={e => setForm({ ...form, check_in_date: e.target.value })} required={form.mode === 'tenant'} className="luxury-input" data-testid="hospitality-checkin-date" /></div>
                <div><Label>Data Check-out (FINO AL)</Label><Input type="date" value={form.check_out_date} onChange={e => setForm({ ...form, check_out_date: e.target.value })} className="luxury-input" /></div>
              </div>

              {/* Host (Dichiarante) */}
              <div className="p-3 rounded-xl" style={{ background: 'rgba(217,42,42,0.04)', border: '1px solid rgba(217,42,42,0.1)' }}>
                <h4 className="text-xs font-semibold uppercase mb-3" style={{ color: '#64748B' }}>Dichiarante (Ospitante)</h4>
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
              <div className="p-3 rounded-xl" style={{ background: 'rgba(217,42,42,0.04)', border: '1px solid rgba(217,42,42,0.1)' }}>
                <h4 className="text-xs font-semibold uppercase mb-3" style={{ color: '#64748B' }}>Dettagli Immobile</h4>
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
              <div className="p-3 rounded-xl" style={{ background: 'rgba(11,138,62,0.03)', border: '1px solid rgba(11,138,62,0.1)' }}>
                <h4 className="text-xs font-semibold uppercase mb-3" style={{ color: '#0B8A3E' }}>Firma</h4>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { value: 'owner', label: 'Proprietario' },
                    { value: 'agency', label: 'Agenzia' },
                    { value: 'blank', label: 'Vuoto' },
                  ].map(opt => (
                    <button key={opt.value} type="button"
                      onClick={() => setForm({ ...form, signature_type: opt.value })}
                      className={`p-2 rounded-lg text-xs font-medium text-center transition-all ${form.signature_type === opt.value ? 'ring-2 ring-rose-500' : ''}`}
                      style={{ background: form.signature_type === opt.value ? 'rgba(11,138,62,0.08)' : 'white', color: '#0B8A3E', border: '1px solid rgba(11,138,62,0.15)' }}>
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => setCreateOpen(false)} className="rounded-xl">Annulla</Button>
                <Button type="submit" className="btn-luxury" data-testid="hospitality-submit">{editingId ? 'Aggiorna Record' : 'Crea e Salva'}</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Existing Records */}
      {records.length > 0 && (
        <div className="luxury-card p-5 mb-6">
          <h3 className="text-sm font-semibold mb-3" style={{ color: '#0B8A3E' }}>Record Salvati ({records.length})</h3>
          <div className="space-y-2">
            {records.map(r => (
              <div key={r.id} className="flex items-center justify-between p-3 rounded-xl hover:bg-rose-50/20" style={{ border: '1px solid rgba(217,42,42,0.08)' }}>
                <div>
                  <span className="font-medium text-sm" style={{ color: '#0F172A' }}>{r.tenant_name}</span>
                  <span className="text-xs ml-3" style={{ color: '#64748B' }}>{r.property_address} | {fmtDate(r.check_in_date)} → {r.check_out_date ? fmtDate(r.check_out_date) : 'Indeterminato'}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Button size="sm" variant="outline" className="text-xs" onClick={() => {
                    // Re-open the create dialog with this record's data so the user can edit & re-save
                    setEditingId(r.id);
                    setForm({
                      mode: r.mode || (r.tenant_id ? 'tenant' : 'manual'),
                      tenant_id: r.tenant_id || '',
                      property_id: r.property_id || '',
                      room_id: r.room_id || '',
                      landlord_id: r.landlord_id || '',
                      contract_id: r.contract_id || '',
                      check_in_date: r.check_in_date || '',
                      check_out_date: r.check_out_date || '',
                      hosting_type: r.hosting_type || 'alloggio',
                      guest_surname: r.guest_surname || '', guest_name: r.guest_name || '',
                      guest_dob: r.guest_dob || '', guest_birth_place: r.guest_birth_place || '',
                      guest_nationality: r.guest_nationality || '', guest_passport: r.guest_passport || '',
                      guest_residence: r.guest_residence || '',
                      host_surname: r.host_surname || '', host_name: r.host_name || '',
                      host_dob: r.host_dob || '', host_birth_place: r.host_birth_place || '',
                      host_province: r.host_province || '', host_residence: r.host_residence || '',
                      property_comune: r.property_comune || '', property_provincia: r.property_provincia || '',
                      property_number: r.property_number || '', property_interno: r.property_interno || '',
                      property_piano: r.property_piano || '', notes: r.notes || '',
                      signature_type: r.signature_type || 'owner',
                    });
                    setCreateOpen(true);
                  }} data-testid={`edit-hospitality-${r.id}`}>Modifica</Button>
                  <Button size="sm" variant="outline" className="text-xs" style={{ color: '#0B8A3E', borderColor: '#0B8A3E' }} onClick={() => handleDeleteRecord(r.id)} data-testid={`delete-hospitality-${r.id}`}>Elimina</Button>
                  <Button size="sm" className="btn-luxury text-xs" onClick={() => handleDownloadPdfByRecord(r)} data-testid={`download-record-${r.id}`}>
                    <Download size={14} className="mr-1" /> PDF
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search */}
      <div className="luxury-card p-4 mb-6">
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2" size={18} style={{ color: '#D92A2A' }} />
          <Input placeholder="Cerca inquilino..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="pl-11 luxury-input" />
        </div>
      </div>

      {/* Tenant List for Quick PDF */}
      <h3 className="text-sm font-semibold mb-3" style={{ color: '#64748B' }}>Genera PDF Rapido per Inquilino</h3>
      <div className="space-y-2">
        {sorted.map(tenant => (
          <div key={tenant.id} className="luxury-card p-4 flex items-center justify-between hover:shadow-md transition-all" data-testid={`hospitality-tenant-${tenant.id}`}>
            <div className="flex items-center gap-3 min-w-0">
              <Users size={16} style={{ color: tenant.room_id ? '#059669' : '#94A3B8' }} />
              <div className="min-w-0">
                <Link to={`/tenants/${tenant.id}`} className="font-medium text-sm hover:underline truncate block" style={{ color: '#0B8A3E' }}>
                  {tenant.full_name}
                </Link>
                <div className="flex items-center gap-2 mt-0.5 text-xs" style={{ color: '#64748B' }}>
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
