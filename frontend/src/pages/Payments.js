import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Plus, Home, DoorOpen, Search, Receipt } from 'lucide-react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const Payments = () => {
  const [overview, setOverview] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState('overview'); // overview | history
  const [formData, setFormData] = useState({
    tenant_id: '', invoice_id: '', amount: '', payment_method: 'contanti',
    payment_date: new Date().toISOString().slice(0, 10), notes: ''
  });

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      const [ov, t, p] = await Promise.all([
        axios.get(`${API}/payments/overview`, { withCredentials: true }),
        axios.get(`${API}/tenants`, { withCredentials: true }),
        axios.get(`${API}/payments`, { withCredentials: true }),
      ]);
      setOverview(ov.data);
      setTenants(t.data);
      setPayments(p.data);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/payments`, {
        ...formData,
        amount: parseFloat(formData.amount),
      }, { withCredentials: true });
      toast.success('Pagamento registrato');
      setDialogOpen(false);
      setFormData({ tenant_id: '', invoice_id: '', amount: '', payment_method: 'contanti', payment_date: new Date().toISOString().slice(0, 10), notes: '' });
      fetchAll();
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore'); }
  };

  // Stats
  const totalPaid = overview.reduce((s, p) => s + p.paid_count, 0);
  const totalNotPaid = overview.reduce((s, p) => s + p.not_paid_count, 0);

  // Filtered overview
  const filteredOverview = overview.map(prop => ({
    ...prop,
    rooms: prop.rooms.filter(r => {
      if (!searchTerm) return true;
      return r.tenant_name?.toLowerCase().includes(searchTerm.toLowerCase());
    })
  })).filter(p => p.rooms.length > 0 || !searchTerm);

  // Filtered payment history
  const filteredHistory = payments.filter(p =>
    p.tenant_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.payment_method?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // ALL tenants available for payment (not just assigned ones)
  const allTenants = tenants;

  if (loading) return <div className="flex items-center justify-center p-12"><div className="luxury-spinner h-10 w-10" /></div>;

  return (
    <div data-testid="payments-page" className="luxury-fade-in">
      <div className="mb-8 flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="luxury-title mb-2">Pagamenti</h1>
          <p className="luxury-subtitle">Chi ha pagato questo mese</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="btn-luxury" data-testid="add-payment-button"><Plus size={18} className="mr-2" /> Registra Pagamento</Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg luxury-modal">
            <DialogHeader><DialogTitle>Nuovo Pagamento</DialogTitle></DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label>Inquilino *</Label>
                <Select value={formData.tenant_id} onValueChange={v => setFormData({ ...formData, tenant_id: v })}>
                  <SelectTrigger><SelectValue placeholder="Seleziona inquilino" /></SelectTrigger>
                  <SelectContent>
                    {allTenants.map(t => (
                      <SelectItem key={t.id} value={t.id}>
                        {t.full_name}{t.property_address ? ` — ${t.property_address}` : ''}{t.room_number ? ` / Stanza ${t.room_number}` : ''}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Importo *</Label>
                  <Input type="number" step="0.01" value={formData.amount} onChange={e => setFormData({ ...formData, amount: e.target.value })} required className="luxury-input" placeholder="0.00" />
                </div>
                <div>
                  <Label>Metodo *</Label>
                  <Select value={formData.payment_method} onValueChange={v => setFormData({ ...formData, payment_method: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="contanti">Contanti</SelectItem>
                      <SelectItem value="bonifico">Bonifico</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div><Label>Data *</Label><Input type="date" value={formData.payment_date} onChange={e => setFormData({ ...formData, payment_date: e.target.value })} required className="luxury-input" /></div>
              <div><Label>Note</Label><Input value={formData.notes} onChange={e => setFormData({ ...formData, notes: e.target.value })} className="luxury-input" placeholder="Note opzionali..." /></div>
              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)} className="rounded-xl">Annulla</Button>
                <Button type="submit" className="btn-luxury">Registra Pagamento</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-8">
        <div className="luxury-card p-4 text-center">
          <p className="text-xs uppercase tracking-wide" style={{ color: '#8B7355' }}>Pagato</p>
          <p className="text-2xl font-bold" style={{ color: '#059669' }}>{totalPaid}</p>
        </div>
        <div className="luxury-card p-4 text-center">
          <p className="text-xs uppercase tracking-wide" style={{ color: '#8B7355' }}>Non Pagato</p>
          <p className="text-2xl font-bold" style={{ color: '#DC2626' }}>{totalNotPaid}</p>
        </div>
        <div className="luxury-card p-4 text-center">
          <p className="text-xs uppercase tracking-wide" style={{ color: '#8B7355' }}>Totale Stanze</p>
          <p className="text-2xl font-bold" style={{ color: '#2C1810' }}>{totalPaid + totalNotPaid}</p>
        </div>
      </div>

      {/* View Toggle + Search */}
      <div className="luxury-card p-4 mb-6 flex items-center gap-4 flex-wrap">
        <div className="flex gap-1 p-1 rounded-xl" style={{ background: 'rgba(184,134,11,0.06)' }}>
          <button
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${viewMode === 'overview' ? 'shadow-sm' : ''}`}
            style={viewMode === 'overview' ? { background: 'white', color: '#9F1239' } : { color: '#8B7355' }}
            onClick={() => setViewMode('overview')}
          >Mese Corrente</button>
          <button
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${viewMode === 'history' ? 'shadow-sm' : ''}`}
            style={viewMode === 'history' ? { background: 'white', color: '#9F1239' } : { color: '#8B7355' }}
            onClick={() => setViewMode('history')}
          >Storico</button>
        </div>
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2" size={16} style={{ color: '#B8860B' }} />
          <Input placeholder="Cerca inquilino..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="pl-9 luxury-input h-9" />
        </div>
      </div>

      {/* Overview - Grouped by Property */}
      {viewMode === 'overview' && (
        <div className="space-y-6">
          {filteredOverview.length === 0 ? (
            <div className="luxury-card p-14 text-center">
              <Home className="mx-auto mb-4" size={48} style={{ color: 'rgba(184,134,11,0.3)' }} />
              <p style={{ color: '#8B7355' }}>Nessun immobile con stanze assegnate</p>
            </div>
          ) : filteredOverview.map(prop => (
            <div key={prop.id} className="luxury-card overflow-hidden" data-testid={`payment-property-${prop.id}`}>
              <div className="px-6 py-4 flex items-center justify-between" style={{ background: 'linear-gradient(135deg, #9F1239 0%, #BE123C 100%)' }}>
                <div className="flex items-center gap-3">
                  <Home size={20} className="text-white" />
                  <div>
                    <h3 className="text-white font-semibold">{prop.address}</h3>
                    <p className="text-white/70 text-xs">Codice: {prop.property_code}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 text-white text-sm">
                  <span style={{ color: '#86EFAC' }}>{prop.paid_count} pagato</span>
                  <span className="text-white/40">|</span>
                  <span style={{ color: '#FCA5A5' }}>{prop.not_paid_count} non pagato</span>
                </div>
              </div>

              <div className="divide-y" style={{ borderColor: 'rgba(184,134,11,0.08)' }}>
                {prop.rooms.map(room => (
                  <div key={room.id} className="px-6 py-4 flex items-center justify-between" data-testid={`payment-room-${room.id}`}>
                    <div className="flex items-center gap-4 min-w-0">
                      <div className="flex items-center gap-2 w-24 shrink-0">
                        <DoorOpen size={16} style={{ color: room.status === 'occupied' ? '#059669' : '#94A3B8' }} />
                        <span className="font-semibold text-sm" style={{ color: '#2C1810' }}>Stanza {room.room_number}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        {room.tenant_name ? (
                          <Link to={`/tenants/${room.tenant_id}`} className="font-medium text-sm hover:underline truncate block" style={{ color: '#9F1239' }}>
                            {room.tenant_name}
                          </Link>
                        ) : (
                          <span className="text-sm italic" style={{ color: '#94A3B8' }}>Vuota</span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      {room.payment_status === 'paid' ? (
                        <>
                          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold" style={{ background: '#ECFDF5', color: '#059669' }}>
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                            Pagato
                          </span>
                          <span className="font-bold text-sm" style={{ color: '#059669' }}>
                            &euro;{room.payment_amount?.toLocaleString()}
                          </span>
                          <span className="px-2 py-0.5 rounded text-[11px] font-medium" style={{ background: 'rgba(184,134,11,0.08)', color: '#8B7355' }}>
                            {room.payment_method}
                          </span>
                        </>
                      ) : room.payment_status === 'not_paid' ? (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold" style={{ background: '#FEF2F2', color: '#DC2626' }}>
                          <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                          Non Pagato
                        </span>
                      ) : (
                        <span className="text-xs" style={{ color: '#94A3B8' }}>—</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* History View - Flat list of all payments */}
      {viewMode === 'history' && (
        <div className="luxury-card overflow-hidden">
          <div className="divide-y" style={{ borderColor: 'rgba(184,134,11,0.08)' }}>
            {filteredHistory.length === 0 ? (
              <div className="p-10 text-center" style={{ color: '#8B7355' }}>Nessun pagamento trovato</div>
            ) : filteredHistory.map(p => (
              <div key={p.id} className="px-6 py-4 flex items-center justify-between hover:bg-rose-50/20 transition-colors">
                <div className="flex items-center gap-4">
                  <div className="text-sm" style={{ color: '#8B7355', minWidth: 90 }}>{p.payment_date}</div>
                  {p.tenant_id && p.tenant_name ? (
                    <Link to={`/tenants/${p.tenant_id}`} className="font-medium text-sm hover:underline" style={{ color: '#9F1239' }}>
                      {p.tenant_name}
                    </Link>
                  ) : (
                    <span className="text-sm italic" style={{ color: '#94A3B8' }}>N/A</span>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <span className="font-bold" style={{ color: '#059669' }}>&euro;{p.amount?.toFixed(2)}</span>
                  <span className="px-2 py-0.5 rounded text-[11px] font-medium capitalize" style={{ background: 'rgba(184,134,11,0.08)', color: '#8B7355' }}>
                    {p.payment_method}
                  </span>
                  {p.notes && <span className="text-xs" style={{ color: '#94A3B8' }}>{p.notes}</span>}
                  <Button variant="ghost" size="sm" className="rounded-lg hover:bg-rose-50 h-7 px-2"
                    onClick={async () => {
                      try {
                        const resp = await axios.get(`${API}/ricevuta/from-payment/${p.id}`, { withCredentials: true, responseType: 'blob' });
                        const url = window.URL.createObjectURL(new Blob([resp.data]));
                        const a = document.createElement('a'); a.href = url; a.download = `ricevuta_${p.tenant_name || 'payment'}.pdf`; a.click();
                        window.URL.revokeObjectURL(url);
                        toast.success('Ricevuta scaricata');
                      } catch { toast.error('Errore'); }
                    }} data-testid={`ricevuta-btn-${p.id}`}>
                    <Receipt size={14} style={{ color: '#9F1239' }} />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Payments;
