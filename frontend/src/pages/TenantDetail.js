import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, FileText, CreditCard, Upload, Trash2, Download, ScrollText, Calendar } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const TenantDetail = () => {
  const { id } = useParams();
  const [tenant, setTenant] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [calendar, setCalendar] = useState(null);
  const [editDialog, setEditDialog] = useState(false);
  const [editMonth, setEditMonth] = useState(null);

  useEffect(() => { fetchTenant(); fetchCalendar(); }, [id]);

  const fetchTenant = async () => {
    try {
      const { data } = await axios.get(`${API_URL}/tenants/${id}`, { withCredentials: true });
      setTenant(data);
    } catch { toast.error('Errore nel caricamento'); }
    setLoading(false);
  };

  const fetchCalendar = async () => {
    try {
      const { data } = await axios.get(`${API_URL}/payment-calendar/${id}`, { withCredentials: true });
      setCalendar(data);
    } catch {}
  };

  const handleUpload = async (e, docType) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    const fd = new FormData();
    fd.append('file', file);
    fd.append('owner_id', id);
    fd.append('owner_type', 'tenant');
    fd.append('doc_type', docType);
    try {
      await axios.post(`${API_URL}/documents/upload`, fd, { withCredentials: true });
      toast.success('Documento caricato');
      fetchTenant();
    } catch { toast.error('Errore upload'); }
    setUploading(false);
  };

  const handleDeleteDoc = async (docId) => {
    if (!window.confirm('Eliminare documento?')) return;
    try {
      await axios.delete(`${API_URL}/documents/${docId}`, { withCredentials: true });
      toast.success('Documento eliminato');
      fetchTenant();
    } catch { toast.error('Errore'); }
  };

  if (loading) return <div className="flex items-center justify-center p-12"><div className="luxury-spinner h-10 w-10" /></div>;
  if (!tenant) return <div className="text-center p-12">Inquilino non trovato</div>;

  const balance = 0; // Removed: deposit is constant, not for rent

  return (
    <div data-testid="tenant-detail-page" className="luxury-fade-in">
      <Link to="/tenants">
        <Button variant="ghost" className="mb-6 rounded-xl" style={{ color: '#9F1239' }}>
          <ArrowLeft size={18} className="mr-2" /> Torna agli Inquilini
        </Button>
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Info */}
        <div className="lg:col-span-2 space-y-6">
          <div className="luxury-card p-7">
            <h2 className="text-2xl font-semibold font-heading mb-6" style={{ color: '#9F1239' }}>{tenant.full_name}</h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              {[
                ['Codice Fiscale', tenant.codice_fiscale],
                ['Passaporto', tenant.passport_number],
                ['Nazionalita', tenant.nationality],
                ['Data di Nascita', tenant.date_of_birth],
                ['Rilascio Passaporto', tenant.passport_issue_date],
                ['Scadenza Passaporto', tenant.passport_expiry_date],
                ['Tipo Doc. ID', tenant.id_type],
                ['Numero Doc. ID', tenant.id_number],
                ['Telefono', tenant.phone],
                ['Email', tenant.email],
                ['WhatsApp', tenant.whatsapp],
              ].map(([label, value]) => value ? (
                <div key={label} className="py-2" style={{ borderBottom: '1px solid rgba(184,134,11,0.08)' }}>
                  <p className="text-xs uppercase tracking-wide mb-1" style={{ color: '#8B7355' }}>{label}</p>
                  <p className="font-medium" style={{ color: '#2C1810' }}>{value}</p>
                </div>
              ) : null)}
            </div>
            {tenant.notes && (
              <div className="mt-4 p-3 rounded-xl notes-text" style={{ background: 'rgba(184,134,11,0.04)' }}>
                <p className="text-xs uppercase tracking-wide mb-1" style={{ color: '#8B7355' }}>Note</p>
                <p>{tenant.notes}</p>
              </div>
            )}
          </div>

          {/* Hospitality PDF */}
          <div className="luxury-card p-7">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold font-heading flex items-center gap-2" style={{ color: '#9F1239' }}>
                <ScrollText size={20} /> Documento di Ospitalita
              </h3>
              <Button
                className="btn-luxury"
                data-testid="hospitality-pdf-button"
                onClick={async () => {
                  try {
                    const response = await axios.get(`${API_URL}/hospitality/pdf/${id}`, {
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
                }}
              >
                <Download size={16} className="mr-2" /> Scarica PDF Ospitalita
              </Button>
            </div>
            <p className="text-xs mt-2" style={{ color: '#8B7355' }}>
              Genera la dichiarazione di ospitalita per questo inquilino con tutti i dati necessari.
            </p>
          </div>

          {/* Monthly Payment Calendar - Editable */}
          <div className="luxury-card p-7">
            <h3 className="text-lg font-semibold font-heading mb-4 flex items-center gap-2" style={{ color: '#9F1239' }}>
              <Calendar size={20} /> Calendario Pagamenti {calendar?.year}
            </h3>
            {calendar?.calendar ? (
              <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-3">
                {calendar.calendar.map(m => {
                  if (m.status === 'none') {
                    return (
                      <div key={m.month} className="p-3 rounded-xl text-center" style={{ background: 'rgba(184,134,11,0.04)', border: '1.5px solid rgba(184,134,11,0.1)' }}>
                        <p className="text-[10px] uppercase tracking-wide font-semibold" style={{ color: '#8B7355' }}>{m.month_name?.substring(0, 3)}</p>
                        <p className="text-[10px] mt-1" style={{ color: '#94A3B8' }}>—</p>
                      </div>
                    );
                  }
                  return (
                    <button key={m.month} onClick={() => { setEditMonth(m); setEditDialog(true); }}
                      className="p-3 rounded-xl text-center cursor-pointer hover:shadow-md transition-all"
                      style={{
                        background: m.status === 'paid' ? '#ECFDF5' : m.status === 'late' ? '#FEF2F2' : '#FFF7ED',
                        border: `1.5px solid ${m.status === 'paid' ? 'rgba(5,150,105,0.3)' : m.status === 'late' ? 'rgba(220,38,38,0.3)' : 'rgba(217,119,6,0.3)'}`,
                      }} data-testid={`calendar-month-${m.month}`}>
                      <p className="text-[10px] uppercase tracking-wide font-semibold" style={{ color: '#8B7355' }}>{m.month_name?.substring(0, 3)}</p>
                      {m.status === 'paid' && (
                        <>
                          <div className="w-2 h-2 rounded-full bg-emerald-500 mx-auto my-1" />
                          <p className="text-xs font-bold" style={{ color: '#059669' }}>&euro;{m.amount?.toFixed(0)}</p>
                          {m.payment_method && <p className="text-[8px]" style={{ color: '#8B7355' }}>{m.payment_method}</p>}
                        </>
                      )}
                      {m.status === 'late' && (
                        <><div className="w-2 h-2 rounded-full bg-red-500 mx-auto my-1" /><p className="text-[10px] font-semibold" style={{ color: '#DC2626' }}>In Ritardo</p></>
                      )}
                      {m.status === 'not_paid' && (
                        <><div className="w-2 h-2 rounded-full bg-amber-500 mx-auto my-1" /><p className="text-[10px] font-semibold" style={{ color: '#D97706' }}>Non Pagato</p></>
                      )}
                      {m.manual_override && <p className="text-[7px] mt-0.5" style={{ color: '#9F1239' }}>manuale</p>}
                    </button>
                  );
                })}
              </div>
            ) : <p className="text-sm" style={{ color: '#8B7355' }}>Caricamento calendario...</p>}
            <p className="text-xs mt-3" style={{ color: '#8B7355' }}>Clicca su un mese per cambiare lo stato di pagamento</p>
          </div>

          {/* Edit Month Status Dialog */}
          {editDialog && editMonth && (
            <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: 'rgba(44,24,16,0.5)' }} onClick={() => setEditDialog(false)}>
              <div className="p-6 rounded-2xl max-w-sm w-full mx-4" style={{ background: '#FFFBF5', border: '1px solid rgba(184,134,11,0.2)', boxShadow: '0 25px 50px rgba(159,18,57,0.2)' }}
                onClick={e => e.stopPropagation()}>
                <h4 className="font-semibold text-lg mb-4" style={{ color: '#9F1239' }}>
                  {editMonth.month_name} {editMonth.year}
                </h4>
                <p className="text-xs mb-4" style={{ color: '#8B7355' }}>
                  Stato attuale: <strong>{editMonth.status === 'paid' ? 'Pagato' : editMonth.status === 'late' ? 'In Ritardo' : 'Non Pagato'}</strong>
                  {editMonth.manual_override && ' (manuale)'}
                </p>
                <div className="space-y-2 mb-4">
                  {[
                    { status: 'paid', label: 'Pagato', color: '#059669', bg: '#ECFDF5' },
                    { status: 'not_paid', label: 'Non Pagato', color: '#D97706', bg: '#FFF7ED' },
                    { status: 'late', label: 'In Ritardo', color: '#DC2626', bg: '#FEF2F2' },
                  ].map(opt => (
                    <button key={opt.status} onClick={async () => {
                      try {
                        const body = { status: opt.status };
                        if (opt.status === 'paid') {
                          const method = window.prompt('Metodo di pagamento? (contanti / bonifico)', 'contanti');
                          const amount = window.prompt('Importo?', '500');
                          body.amount = parseFloat(amount) || 0;
                          body.payment_method = method || 'contanti';
                          body.payment_date = new Date().toISOString().slice(0, 10);
                        }
                        await axios.put(`${API_URL}/payment-calendar/${id}/${editMonth.year}/${editMonth.month}`, body, { withCredentials: true });
                        toast.success(`${editMonth.month_name} → ${opt.label}`);
                        setEditDialog(false);
                        fetchCalendar();
                        fetchTenant();
                      } catch { toast.error('Errore'); }
                    }}
                      className="w-full flex items-center gap-3 p-3 rounded-xl text-left hover:shadow-md transition-all"
                      style={{ background: opt.bg, border: `1.5px solid ${opt.color}30` }}
                      data-testid={`set-month-${opt.status}`}>
                      <div className="w-3 h-3 rounded-full" style={{ background: opt.color }} />
                      <span className="font-semibold text-sm" style={{ color: opt.color }}>{opt.label}</span>
                    </button>
                  ))}
                </div>
                {editMonth.manual_override && (
                  <button onClick={async () => {
                    try {
                      await axios.delete(`${API_URL}/payment-calendar/${id}/${editMonth.year}/${editMonth.month}`, { withCredentials: true });
                      toast.success('Override rimosso');
                      setEditDialog(false);
                      fetchCalendar();
                      fetchTenant();
                    } catch { toast.error('Errore'); }
                  }} className="w-full text-center text-xs py-2 rounded-xl hover:bg-rose-50 transition-all" style={{ color: '#9F1239', border: '1px solid rgba(159,18,57,0.2)' }}>
                    Rimuovi override manuale
                  </button>
                )}
                <button onClick={() => setEditDialog(false)} className="w-full text-center text-xs py-2 mt-2" style={{ color: '#8B7355' }}>
                  Chiudi
                </button>
              </div>
            </div>
          )}

          {/* Property & Room */}
          {tenant.property_info && (
            <div className="luxury-card p-7">
              <h3 className="text-lg font-semibold font-heading mb-4" style={{ color: '#9F1239' }}>Alloggio</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><p className="text-xs uppercase" style={{ color: '#8B7355' }}>Immobile</p><p className="font-medium">{tenant.property_info.address}</p></div>
                <div><p className="text-xs uppercase" style={{ color: '#8B7355' }}>Codice</p><p className="font-medium">{tenant.property_info.property_code}</p></div>
                {tenant.room_info && <>
                  <div><p className="text-xs uppercase" style={{ color: '#8B7355' }}>Stanza</p><p className="font-medium">{tenant.room_info.room_number}</p></div>
                  <div><p className="text-xs uppercase" style={{ color: '#8B7355' }}>Tipo</p><p className="font-medium">{tenant.room_info.room_type === 'single' ? 'Singola' : 'Doppia'}</p></div>
                </>}
              </div>
            </div>
          )}

          {/* Payments History */}
          <div className="luxury-card p-7">
            <h3 className="text-lg font-semibold font-heading mb-4 flex items-center gap-2" style={{ color: '#9F1239' }}>
              <CreditCard size={20} /> Storico Pagamenti
            </h3>
            {tenant.payments?.length > 0 ? (
              <div className="space-y-2">
                {tenant.payments.map(p => (
                  <div key={p.id} className="flex items-center justify-between py-3 px-4 rounded-xl" style={{ background: 'rgba(250,247,240,0.5)', border: '1px solid rgba(184,134,11,0.08)' }}>
                    <div>
                      <p className="font-medium text-sm" style={{ color: '#2C1810' }}>&euro;{p.amount?.toFixed(2)}</p>
                      <p className="text-xs" style={{ color: '#8B7355' }}>{p.payment_date} - {p.payment_method}</p>
                    </div>
                    {p.notes && <p className="text-xs notes-text" style={{ color: '#8B7355' }}>{p.notes}</p>}
                  </div>
                ))}
              </div>
            ) : <p style={{ color: '#8B7355' }}>Nessun pagamento registrato</p>}
          </div>

          {/* Documents */}
          <div className="luxury-card p-7">
            <h3 className="text-lg font-semibold font-heading mb-4 flex items-center gap-2" style={{ color: '#9F1239' }}>
              <FileText size={20} /> Documenti
            </h3>
            <div className="flex gap-3 mb-4 flex-wrap">
              <label className="cursor-pointer">
                <input type="file" className="hidden" onChange={e => handleUpload(e, 'passport')} />
                <span className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm" style={{ background: 'rgba(159,18,57,0.05)', border: '1px solid rgba(159,18,57,0.2)', color: '#9F1239' }}>
                  <Upload size={16} /> Carica Passaporto
                </span>
              </label>
              <label className="cursor-pointer">
                <input type="file" className="hidden" onChange={e => handleUpload(e, 'id_card')} />
                <span className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm" style={{ background: 'rgba(184,134,11,0.05)', border: '1px solid rgba(184,134,11,0.2)', color: '#B8860B' }}>
                  <Upload size={16} /> Carica Doc. Identita
                </span>
              </label>
              <label className="cursor-pointer">
                <input type="file" className="hidden" onChange={e => handleUpload(e, 'other')} />
                <span className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm" style={{ background: 'rgba(5,150,105,0.05)', border: '1px solid rgba(5,150,105,0.2)', color: '#059669' }}>
                  <Upload size={16} /> Altro Documento
                </span>
              </label>
            </div>
            {tenant.documents?.length > 0 ? (
              <div className="space-y-2">
                {tenant.documents.map(doc => (
                  <div key={doc.id} className="flex items-center justify-between py-2 px-4 rounded-xl" style={{ border: '1px solid rgba(184,134,11,0.1)' }}>
                    <div>
                      <p className="text-sm font-medium" style={{ color: '#2C1810' }}>{doc.filename}</p>
                      <p className="text-xs" style={{ color: '#8B7355' }}>{doc.doc_type} - {doc.uploaded_at?.slice(0, 10)}</p>
                    </div>
                    <div className="flex gap-2">
                      <a href={`${process.env.REACT_APP_BACKEND_URL}${doc.url}`} target="_blank" rel="noreferrer">
                        <Button variant="ghost" size="sm" className="rounded-lg"><Download size={14} /></Button>
                      </a>
                      <Button variant="ghost" size="sm" className="rounded-lg" onClick={() => handleDeleteDoc(doc.id)}><Trash2 size={14} className="text-red-500" /></Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : <p style={{ color: '#8B7355' }}>Nessun documento caricato</p>}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Current Month Status */}
          <div className="luxury-card p-7">
            <h3 className="text-lg font-semibold font-heading mb-4" style={{ color: '#9F1239' }}>Stato Mese Corrente</h3>
            {tenant.payment_status === 'paid' ? (
              <div className="p-4 rounded-xl" style={{ background: '#ECFDF5', border: '1px solid rgba(5,150,105,0.2)' }}>
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-3 h-3 rounded-full bg-emerald-500" />
                  <span className="font-bold text-lg" style={{ color: '#059669' }}>Pagato</span>
                </div>
                <p className="text-2xl font-bold" style={{ color: '#059669' }}>&euro;{(tenant.month_paid_amount || 0).toFixed(2)}</p>
                {tenant.month_payment_method && (
                  <p className="text-sm mt-1" style={{ color: '#8B7355' }}>Metodo: {tenant.month_payment_method}</p>
                )}
              </div>
            ) : (
              <div className="p-4 rounded-xl" style={{ background: '#FEF2F2', border: '1px solid rgba(220,38,38,0.2)' }}>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-red-500" />
                  <span className="font-bold text-lg" style={{ color: '#DC2626' }}>Non Pagato</span>
                </div>
              </div>
            )}
          </div>

          {/* Deposit (Guarantee - constant) */}
          <div className="luxury-card p-7">
            <h3 className="text-lg font-semibold font-heading mb-4" style={{ color: '#9F1239' }}>Deposito Garanzia</h3>
            <p className="text-2xl font-bold" style={{ color: '#2C1810' }}>&euro;{(tenant.deposit_amount || 0).toFixed(2)}</p>
            <p className="text-xs mt-1" style={{ color: '#8B7355' }}>Il deposito e solo garanzia, non viene scalato</p>
          </div>

          {/* Contracts */}
          {tenant.contracts?.length > 0 && (
            <div className="luxury-card p-7">
              <h3 className="text-lg font-semibold font-heading mb-4" style={{ color: '#9F1239' }}>Contratti</h3>
              <div className="space-y-2">
                {tenant.contracts.map(c => (
                  <div key={c.id} className="p-3 rounded-xl" style={{ border: '1px solid rgba(184,134,11,0.1)' }}>
                    <p className="text-sm font-medium font-mono" style={{ color: '#2C1810' }}>{c.contract_number}</p>
                    <p className="text-xs" style={{ color: '#8B7355' }}>{c.start_date} - {c.end_date}</p>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${c.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-600'}`}>{c.status}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Invoices */}
          {tenant.invoices?.length > 0 && (
            <div className="luxury-card p-7">
              <h3 className="text-lg font-semibold font-heading mb-4" style={{ color: '#9F1239' }}>Fatture</h3>
              <div className="space-y-2">
                {tenant.invoices.map(inv => (
                  <div key={inv.id} className="p-3 rounded-xl" style={{ border: '1px solid rgba(184,134,11,0.1)' }}>
                    <div className="flex justify-between">
                      <p className="text-sm font-mono" style={{ color: '#2C1810' }}>{inv.invoice_number}</p>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${inv.payment_status === 'paid' ? 'bg-green-100 text-green-700' : inv.payment_status === 'partial' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}`}>
                        {inv.payment_status === 'paid' ? 'Pagato' : inv.payment_status === 'partial' ? 'Parziale' : 'Non Pagato'}
                      </span>
                    </div>
                    <p className="text-xs" style={{ color: '#8B7355' }}>&euro;{inv.amount?.toFixed(2)} - Scadenza: {inv.due_date}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TenantDetail;
