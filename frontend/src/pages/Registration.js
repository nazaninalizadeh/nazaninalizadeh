import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { Upload, FileText, Trash2, Search, Download, Users, Package } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const Registration = () => {
  const [tenants, setTenants] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTenant, setSelectedTenant] = useState('');
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef(null);

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      const [t] = await Promise.all([
        axios.get(`${API}/tenants`, { withCredentials: true }),
      ]);
      setTenants(t.data);
      // Load all documents of type registration
      const allDocs = [];
      for (const tenant of t.data) {
        try {
          const { data } = await axios.get(`${API}/documents/${tenant.id}`, { withCredentials: true });
          const regDocs = data.filter(d => ['registration', 'passport', 'id_card', 'codice_fiscale', 'contract', 'owner_document'].includes(d.doc_type));
          regDocs.forEach(d => { d.tenant_name = tenant.full_name; d.tenant_id = tenant.id; });
          allDocs.push(...regDocs);
        } catch {}
      }
      setDocuments(allDocs);
    } catch { toast.error('Errore nel caricamento'); }
    setLoading(false);
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || !selectedTenant) {
      toast.error('Seleziona un inquilino prima di caricare');
      return;
    }
    setUploading(true);
    const fd = new FormData();
    fd.append('owner_id', selectedTenant);
    fd.append('doc_type', 'registration');
    fd.append('file', file);
    try {
      await axios.post(`${API}/registration/upload`, fd, { withCredentials: true });
      toast.success('Documento caricato');
      fetchAll();
    } catch { toast.error('Errore nel caricamento'); }
    setUploading(false);
    if (fileRef.current) fileRef.current.value = '';
  };

  const handleDownloadZip = async (tenantId, tenantName) => {
    try {
      const response = await axios.get(`${API}/documents/bundle/${tenantId}`, {
        withCredentials: true, responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `documenti_${tenantName?.replace(/\s/g, '_')}.zip`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success('ZIP scaricato');
    } catch (err) {
      toast.error(err.response?.status === 404 ? 'Nessun documento trovato' : 'Errore');
    }
  };

  const docTypeLabels = {
    passport: 'Passaporto', id_card: "Carta d'identita", codice_fiscale: 'Codice Fiscale',
    registration: 'Registrazione', contract: 'Contratto', owner_document: 'Documento Proprietario',
    hospitality: 'Ospitalita', other: 'Altro',
  };

  const filteredDocs = documents.filter(d =>
    d.tenant_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    d.filename?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    d.doc_type?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) return <div className="flex items-center justify-center p-12"><div className="luxury-spinner h-10 w-10" /></div>;

  return (
    <div data-testid="registration-page" className="luxury-fade-in">
      <div className="mb-8">
        <h1 className="luxury-title mb-2">Registrazione</h1>
        <p className="luxury-subtitle">Gestione documenti e pacchetto condivisione</p>
      </div>

      {/* Upload Section */}
      <div className="luxury-card p-6 mb-6">
        <h3 className="text-sm font-semibold mb-4 flex items-center gap-2" style={{ color: '#0B8A3E' }}>
          <Upload size={18} /> Carica Documento
        </h3>
        <div className="flex items-end gap-4 flex-wrap">
          <div className="flex-1 min-w-[200px]">
            <Label className="text-xs">Inquilino *</Label>
            <Select value={selectedTenant} onValueChange={setSelectedTenant}>
              <SelectTrigger><SelectValue placeholder="Seleziona inquilino" /></SelectTrigger>
              <SelectContent>
                {tenants.map(t => (
                  <SelectItem key={t.id} value={t.id}>{t.full_name}{t.property_address ? ` — ${t.property_address}` : ''}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <label>
            <input type="file" ref={fileRef} className="hidden" onChange={handleUpload} accept=".pdf,.jpg,.jpeg,.png,.doc,.docx" />
            <span className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm cursor-pointer transition-all hover:shadow-md" style={{ background: '#0B8A3E', color: 'white' }}>
              <Upload size={15} /> {uploading ? 'Caricamento...' : 'Carica File'}
            </span>
          </label>
        </div>
      </div>

      {/* ZIP Bundle Section */}
      <div className="luxury-card p-6 mb-6">
        <h3 className="text-sm font-semibold mb-3 flex items-center gap-2" style={{ color: '#0B8A3E' }}>
          <Package size={18} /> Pacchetto Documenti (ZIP)
        </h3>
        <p className="text-xs mb-2" style={{ color: '#64748B' }}>
          Ogni pacchetto include i file qui sotto:
        </p>
        <ul className="text-xs mb-4 ml-5 list-disc" style={{ color: '#334155' }}>
          <li>Modulo di Registrazione</li>
          <li>Documento del Proprietario (carta d'identità o passaporto)</li>
          <li>Modulo di Ospitalità (Comunicazione di Ospitalità - Articolo 7)</li>
          <li>Documento dell'Inquilino (passaporto o carta d'identità)</li>
          <li>Contratto di locazione (se attivo)</li>
        </ul>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {tenants.filter(t => t.room_id).map(t => (
            <div key={t.id} className="flex items-center gap-3 p-3 rounded-xl"
              style={{ background: 'rgba(11,138,62,0.03)', border: '1px solid rgba(11,138,62,0.1)' }}
              data-testid={`zip-card-${t.id}`}>
              <button onClick={() => handleDownloadZip(t.id, t.full_name)} className="flex items-center gap-3 flex-1 text-left hover:opacity-80 transition-all min-w-0" data-testid={`zip-download-${t.id}`}>
                <Package size={16} style={{ color: '#0B8A3E' }} />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium truncate" style={{ color: '#0F172A' }}>{t.full_name}</p>
                  <p className="text-[10px]" style={{ color: '#64748B' }}>{t.property_address}</p>
                </div>
              </button>
              <div className="flex gap-1">
                <button
                  onClick={() => toast.info('WhatsApp: invio pacchetto (in attesa di configurazione API Business)')}
                  className="text-[10px] px-2 py-1 rounded font-semibold hover:shadow-sm transition-all"
                  style={{ background: 'rgba(5,150,105,0.12)', color: '#059669' }}
                  data-testid={`zip-wa-${t.id}`}
                  title="Condividi via WhatsApp">WA</button>
                <button
                  onClick={() => toast.info('Email: invio pacchetto (in attesa di configurazione SMTP/Resend)')}
                  className="text-[10px] px-2 py-1 rounded font-semibold hover:shadow-sm transition-all"
                  style={{ background: 'rgba(37,99,235,0.12)', color: '#2563EB' }}
                  data-testid={`zip-email-${t.id}`}
                  title="Invia via Email">Email</button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Documents List */}
      <div className="luxury-card overflow-hidden">
        <div className="p-4" style={{ borderBottom: '1px solid rgba(217,42,42,0.12)' }}>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2" size={16} style={{ color: '#D92A2A' }} />
            <Input placeholder="Cerca documenti..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="pl-9 luxury-input" />
          </div>
        </div>
        <div className="divide-y" style={{ borderColor: 'rgba(217,42,42,0.08)' }}>
          {filteredDocs.length === 0 ? (
            <div className="p-10 text-center" style={{ color: '#64748B' }}>Nessun documento</div>
          ) : filteredDocs.map(doc => (
            <div key={doc.id} className="px-5 py-3 flex items-center justify-between hover:bg-rose-50/20">
              <div className="flex items-center gap-3">
                <FileText size={16} style={{ color: '#0B8A3E' }} />
                <div>
                  <Link to={`/tenants/${doc.tenant_id}`} className="text-sm font-medium hover:underline" style={{ color: '#0B8A3E' }}>{doc.tenant_name}</Link>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-[10px] px-2 py-0.5 rounded" style={{ background: 'rgba(11,138,62,0.08)', color: '#0B8A3E' }}>
                      {docTypeLabels[doc.doc_type] || doc.doc_type}
                    </span>
                    <span className="text-xs" style={{ color: '#64748B' }}>{doc.filename}</span>
                  </div>
                </div>
              </div>
              <a href={`${process.env.REACT_APP_BACKEND_URL}${doc.url}`} target="_blank" rel="noopener noreferrer">
                <Button variant="ghost" size="sm" className="rounded-lg"><Download size={14} style={{ color: '#059669' }} /></Button>
              </a>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Registration;
