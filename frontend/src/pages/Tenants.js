import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Link, useSearchParams } from 'react-router-dom';
import { Plus, Search, Eye, Edit, Trash2, Filter } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import OcrScanner from '../components/OcrScanner';
import { Combobox } from '../components/Combobox';
import { NATIONALITIES, COUNTRIES } from '../lib/it_dictionaries';
import { ITALIAN_CITIES } from '../lib/it_cities';
import { fmtDate } from '../lib/format';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Tenants = () => {
  const [tenants, setTenants] = useState([]);
  const [properties, setProperties] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingTenant, setEditingTenant] = useState(null);
  const [searchParams] = useSearchParams();

  const [formData, setFormData] = useState({
    surname: '', name: '', codice_fiscale: '', passport_number: '', nationality: 'Italiana',
    date_of_birth: '', place_of_birth: '', country_of_birth: 'Italia',
    passport_issue_date: '', passport_expiry_date: '',
    id_type: '', id_number: '', phone: '', email: '',
    notes: '', deposit_amount: 0, property_id: '', room_id: '',
    payment_due_day: 5, address: '',
  });

  useEffect(() => {
    const filter = searchParams.get('status');
    if (filter && ['paid', 'not_paid', 'late'].includes(filter)) setStatusFilter(filter);
    fetchAll();
  }, []);

  const fetchAll = async () => {
    try {
      const [t, p, r] = await Promise.all([
        axios.get(`${API_URL}/tenants`, { withCredentials: true }),
        axios.get(`${API_URL}/properties`, { withCredentials: true }),
        axios.get(`${API_URL}/rooms`, { withCredentials: true }),
      ]);
      setTenants(t.data); setProperties(p.data); setRooms(r.data);
    } catch { toast.error('Errore nel caricamento'); }
    setLoading(false);
  };

  const resetForm = () => {
    setFormData({ surname: '', name: '', codice_fiscale: '', passport_number: '', nationality: 'Italiana', date_of_birth: '', place_of_birth: '', country_of_birth: 'Italia', passport_issue_date: '', passport_expiry_date: '', id_type: '', id_number: '', phone: '', email: '', notes: '', deposit_amount: 0, property_id: '', room_id: '', payment_due_day: 5, address: '' });
    setEditingTenant(null);
  };

  const openEditDialog = (tenant) => {
    setEditingTenant(tenant);
    // full_name is stored "Surname Name" — split for editing
    const [surname = '', ...nameParts] = (tenant.full_name || '').split(' ');
    setFormData({
      surname: tenant.surname || surname, name: tenant.name || nameParts.join(' '),
      codice_fiscale: tenant.codice_fiscale || '',
      passport_number: tenant.passport_number || '', nationality: tenant.nationality || 'Italiana',
      date_of_birth: tenant.date_of_birth || '',
      place_of_birth: tenant.place_of_birth || '',
      country_of_birth: tenant.country_of_birth || 'Italia',
      passport_issue_date: tenant.passport_issue_date || '',
      passport_expiry_date: tenant.passport_expiry_date || '', id_type: tenant.id_type || '',
      id_number: tenant.id_number || '', phone: tenant.phone || '', email: tenant.email || '',
      notes: tenant.notes || '', deposit_amount: tenant.deposit_amount || 0,
      property_id: tenant.property_id || '', room_id: tenant.room_id || '',
      payment_due_day: tenant.payment_due_day || 5,
      address: tenant.address || '',
    });
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Build full_name as "Surname Name" (Italian/Italian government format)
      const payload = { ...formData, full_name: `${formData.surname} ${formData.name}`.trim() };
      if (editingTenant) {
        await axios.put(`${API_URL}/tenants/${editingTenant.id}`, payload, { withCredentials: true });
        toast.success('Inquilino aggiornato');
      } else {
        await axios.post(`${API_URL}/tenants`, payload, { withCredentials: true });
        toast.success('Inquilino creato');
      }
      setDialogOpen(false); resetForm(); fetchAll();
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore'); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Eliminare questo inquilino?')) return;
    try {
      await axios.delete(`${API_URL}/tenants/${id}`, { withCredentials: true });
      toast.success('Eliminato'); fetchAll();
    } catch { toast.error('Errore'); }
  };

  const filteredTenants = tenants.filter(t => {
    if (statusFilter !== 'all' && t.payment_status !== statusFilter) return false;
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      return t.full_name?.toLowerCase().includes(q) || t.passport_number?.toLowerCase().includes(q) ||
        t.email?.toLowerCase().includes(q) || t.codice_fiscale?.toLowerCase().includes(q);
    }
    return true;
  });

  const availableRooms = rooms.filter(r => r.property_id === formData.property_id && (r.status === 'available' || r.id === formData.room_id));

  // Quick status change handler - uses dialog instead of prompt
  const [quickTenant, setQuickTenant] = useState(null);
  const [quickMethod, setQuickMethod] = useState('contanti');
  const [quickAmount, setQuickAmount] = useState('');
  const [quickDialogOpen, setQuickDialogOpen] = useState(false);

  const handleQuickPaid = async () => {
    if (!quickTenant) return;
    const now = new Date();
    const month = now.getMonth() + 1;
    const year = now.getFullYear();
    try {
      await axios.put(`${API_URL}/payment-calendar/${quickTenant.id}/${year}/${month}`, {
        status: 'paid', amount: parseFloat(quickAmount) || 0,
        payment_method: quickMethod, payment_date: now.toISOString().slice(0, 10),
      }, { withCredentials: true });
      toast.success(`${quickTenant.full_name} → Pagato`);
      setQuickDialogOpen(false); setQuickTenant(null); setQuickAmount(''); fetchAll();
    } catch { toast.error('Errore'); }
  };

  const handleQuickStatusChange = async (tenant, newStatus) => {
    if (newStatus === 'paid') {
      setQuickTenant(tenant); setQuickDialogOpen(true); return;
    }
    const now = new Date();
    const month = now.getMonth() + 1;
    const year = now.getFullYear();
    try {
      await axios.put(`${API_URL}/payment-calendar/${tenant.id}/${year}/${month}`, { status: newStatus }, { withCredentials: true });
      toast.success(`${tenant.full_name} → ${newStatus === 'late' ? 'In Ritardo' : 'Non Pagato'}`);
      fetchAll();
    } catch { toast.error('Errore'); }
  };

  // Status badge component - clickable for quick change
  const StatusBadge = ({ tenant }) => {
    if (tenant.payment_status === 'paid') {
      return (
        <div className="flex items-center gap-2">
          <button onClick={() => handleQuickStatusChange(tenant, 'not_paid')} className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold cursor-pointer hover:shadow-md transition-all" style={{ background: '#ECFDF5', color: '#059669' }} title="Clicca per cambiare stato" data-testid={`status-btn-${tenant.id}`}>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" /> Pagato
          </button>
          <span className="text-xs font-bold" style={{ color: '#059669' }}>&euro;{tenant.month_paid_amount?.toFixed(0)}</span>
          {tenant.month_payment_method && <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: 'rgba(184,134,11,0.08)', color: '#8B7355' }}>{tenant.month_payment_method}</span>}
        </div>
      );
    }
    if (tenant.payment_status === 'late') {
      return (
        <button onClick={() => handleQuickStatusChange(tenant, 'paid')} className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold cursor-pointer hover:shadow-md transition-all" style={{ background: '#FEF2F2', color: '#DC2626' }} title="Clicca per segnare pagato" data-testid={`status-btn-${tenant.id}`}>
          <span className="w-1.5 h-1.5 rounded-full bg-red-500" /> In Ritardo
        </button>
      );
    }
    if (tenant.room_id) {
      return (
        <button onClick={() => handleQuickStatusChange(tenant, 'paid')} className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold cursor-pointer hover:shadow-md transition-all" style={{ background: '#FFF7ED', color: '#D97706' }} title="Clicca per segnare pagato" data-testid={`status-btn-${tenant.id}`}>
          <span className="w-1.5 h-1.5 rounded-full bg-amber-500" /> Non Pagato
        </button>
      );
    }
    return <span className="text-xs" style={{ color: '#94A3B8' }}>-</span>;
  };

  // Status counts
  const paidCount = tenants.filter(t => t.payment_status === 'paid').length;
  const notPaidCount = tenants.filter(t => t.payment_status === 'not_paid' && t.room_id).length;
  const lateCount = tenants.filter(t => t.payment_status === 'late').length;

  return (
    <div data-testid="tenants-page" className="luxury-fade-in">
      <div className="mb-8 flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="luxury-title mb-2" data-testid="tenants-title">Inquilini</h1>
          <p className="luxury-subtitle">Gestisci inquilini e stato pagamenti</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="btn-luxury" data-testid="add-tenant-button"><Plus size={18} className="mr-2" />Aggiungi Inquilino</Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto luxury-modal w-[95vw] sm:w-auto">
            <DialogHeader><DialogTitle>{editingTenant ? 'Modifica Inquilino' : 'Nuovo Inquilino'}</DialogTitle></DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="pb-3 mb-3" style={{ borderBottom: '1px solid rgba(184,134,11,0.12)' }}>
                <OcrScanner onDataExtracted={(data) => { setFormData(prev => ({ ...prev, ...Object.fromEntries(Object.entries(data).filter(([_, v]) => v)) })); }} />
                <p className="text-xs mt-2" style={{ color: '#8B7355' }}>Scansiona un passaporto o documento per compilare automaticamente</p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div><Label>Cognome *</Label><Input value={formData.surname} onChange={e => setFormData({ ...formData, surname: e.target.value })} required className="luxury-input" data-testid="tenant-surname-input" /></div>
                <div><Label>Nome *</Label><Input value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} required className="luxury-input" data-testid="tenant-name-input" /></div>
                <div><Label>Codice Fiscale</Label><Input value={formData.codice_fiscale} onChange={e => setFormData({ ...formData, codice_fiscale: e.target.value })} className="luxury-input" /></div>
                <div><Label>Numero Passaporto *</Label><Input value={formData.passport_number} onChange={e => setFormData({ ...formData, passport_number: e.target.value })} required className="luxury-input" /></div>
                <div>
                  <Label>Nazionalità *</Label>
                  <Combobox options={NATIONALITIES} value={formData.nationality} onChange={v => setFormData({ ...formData, nationality: v })} placeholder="Es: Italiana, Iraniana..." dataTestid="tenant-nationality" />
                </div>
                <div><Label>Data di Nascita *</Label><Input type="date" value={formData.date_of_birth} onChange={e => setFormData({ ...formData, date_of_birth: e.target.value })} required className="luxury-input" /></div>
                <div>
                  <Label>Luogo di Nascita</Label>
                  <Combobox options={ITALIAN_CITIES} value={formData.place_of_birth} onChange={v => setFormData({ ...formData, place_of_birth: v })} placeholder="Es: Padova, Roma..." dataTestid="tenant-place-of-birth" />
                </div>
                <div>
                  <Label>Paese di Nascita</Label>
                  <Combobox options={COUNTRIES} value={formData.country_of_birth} onChange={v => setFormData({ ...formData, country_of_birth: v })} placeholder="Es: Italia, Iran..." dataTestid="tenant-country" />
                </div>
                <div><Label>Rilascio Passaporto *</Label><Input type="date" value={formData.passport_issue_date} onChange={e => setFormData({ ...formData, passport_issue_date: e.target.value })} required className="luxury-input" /></div>
                <div><Label>Scadenza Passaporto *</Label><Input type="date" value={formData.passport_expiry_date} onChange={e => setFormData({ ...formData, passport_expiry_date: e.target.value })} required className="luxury-input" /></div>
                <div><Label>Telefono *</Label><Input value={formData.phone} onChange={e => setFormData({ ...formData, phone: e.target.value })} required className="luxury-input" placeholder="+39 333 1234567" data-testid="tenant-phone-input" /></div>
                <div><Label>Email *</Label><Input type="email" value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })} required className="luxury-input" data-testid="tenant-email-input" /></div>
                <div className="col-span-1 sm:col-span-2"><Label>Indirizzo di Residenza</Label><Input value={formData.address} onChange={e => setFormData({ ...formData, address: e.target.value })} className="luxury-input" placeholder="Via, civico, città" /></div>
                <div><Label>Deposito (Garanzia)</Label><Input type="number" step="0.01" value={formData.deposit_amount} onChange={e => setFormData({ ...formData, deposit_amount: parseFloat(e.target.value) || 0 })} className="luxury-input" /></div>
                <div><Label>Giorno Scadenza Pagamento</Label><Input type="number" min="1" max="28" value={formData.payment_due_day} onChange={e => setFormData({ ...formData, payment_due_day: parseInt(e.target.value) || 5 })} className="luxury-input" /></div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <Label>Immobile</Label>
                  <Select value={formData.property_id || 'none'} onValueChange={v => setFormData({ ...formData, property_id: v === 'none' ? '' : v, room_id: '' })}>
                    <SelectTrigger><SelectValue placeholder="Seleziona" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Nessuno</SelectItem>
                      {properties.map(p => <SelectItem key={p.id} value={p.id}>{p.property_code} - {p.address}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Stanza</Label>
                  <Select value={formData.room_id || 'none'} onValueChange={v => setFormData({ ...formData, room_id: v === 'none' ? '' : v })} disabled={!formData.property_id}>
                    <SelectTrigger><SelectValue placeholder="Seleziona" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Nessuna</SelectItem>
                      {availableRooms.map(r => <SelectItem key={r.id} value={r.id}>Stanza {r.room_number}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div><Label>Note</Label><Input value={formData.notes} onChange={e => setFormData({ ...formData, notes: e.target.value })} className="luxury-input" /></div>
              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="rounded-xl">Annulla</Button>
                <Button type="submit" className="btn-luxury" data-testid="save-tenant-button">{editingTenant ? 'Aggiorna' : 'Crea'}</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Status Filter Tabs */}
      <div className="flex items-center gap-3 mb-5 flex-wrap">
        {[
          { key: 'all', label: 'Tutti', count: tenants.length },
          { key: 'paid', label: 'Pagato', count: paidCount, color: '#059669' },
          { key: 'not_paid', label: 'Non Pagato', count: notPaidCount, color: '#D97706' },
          { key: 'late', label: 'In Ritardo', count: lateCount, color: '#DC2626' },
        ].map(tab => (
          <button key={tab.key} onClick={() => setStatusFilter(tab.key)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${statusFilter === tab.key ? 'shadow-sm' : ''}`}
            style={statusFilter === tab.key ? { background: 'white', color: tab.color || '#9F1239', border: `1.5px solid ${tab.color || '#9F1239'}` } : { background: 'rgba(184,134,11,0.04)', color: '#8B7355', border: '1px solid transparent' }}
            data-testid={`filter-${tab.key}`}>
            {tab.label} ({tab.count})
          </button>
        ))}
      </div>

      <div className="luxury-card overflow-hidden">
        <div className="p-5" style={{ borderBottom: '1px solid rgba(184,134,11,0.12)' }}>
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2" size={18} style={{ color: '#B8860B' }} />
            <Input placeholder="Cerca per nome, passaporto, email..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="pl-11 luxury-input" data-testid="search-tenant-input" />
          </div>
        </div>

        {loading ? <div className="flex items-center justify-center p-12"><div className="luxury-spinner h-10 w-10" /></div> : (
          <Table>
            <TableHeader>
              <TableRow style={{ background: 'linear-gradient(135deg, #9F1239 0%, #BE123C 100%)' }}>
                <TableHead className="text-white font-semibold text-xs uppercase">Nome</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase">Immobile</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase">Stanza</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase">Deposito</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase">Stato Mese</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase text-right">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredTenants.length === 0 ? (
                <TableRow><TableCell colSpan={6} className="text-center py-10" style={{ color: '#8B7355' }}>Nessun inquilino trovato</TableCell></TableRow>
              ) : filteredTenants.map(tenant => (
                <TableRow key={tenant.id} className="hover:bg-rose-50/30 transition-colors" data-testid={`tenant-row-${tenant.id}`}>
                  <TableCell><Link to={`/tenants/${tenant.id}`} className="font-medium hover:underline" style={{ color: '#9F1239' }}>{tenant.full_name}</Link></TableCell>
                  <TableCell style={{ color: tenant.property_address ? '#4A3B31' : '#94A3B8' }}>{tenant.property_address || <span className="italic text-xs">Non assegnato</span>}</TableCell>
                  <TableCell style={{ color: tenant.room_number ? '#4A3B31' : '#94A3B8' }}>{tenant.room_number ? `Stanza ${tenant.room_number}` : <span className="italic text-xs">Non assegnato</span>}</TableCell>
                  <TableCell style={{ color: '#4A3B31' }}>&euro;{(tenant.deposit_amount || 0).toFixed(0)}</TableCell>
                  <TableCell><StatusBadge tenant={tenant} /></TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      <Link to={`/tenants/${tenant.id}`}><Button variant="ghost" size="sm" className="rounded-lg hover:bg-rose-50"><Eye size={16} style={{ color: '#9F1239' }} /></Button></Link>
                      <Button variant="ghost" size="sm" className="rounded-lg hover:bg-amber-50" onClick={() => openEditDialog(tenant)}><Edit size={16} style={{ color: '#B8860B' }} /></Button>
                      <Button variant="ghost" size="sm" className="rounded-lg hover:bg-red-50" onClick={() => handleDelete(tenant.id)}><Trash2 size={16} className="text-red-500" /></Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      {/* Quick Pay Dialog */}
      {quickDialogOpen && quickTenant && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: 'rgba(44,24,16,0.5)' }} onClick={() => { setQuickDialogOpen(false); setQuickTenant(null); }}>
          <div className="p-6 rounded-2xl max-w-sm w-full mx-4" style={{ background: '#FFFBF5', border: '1px solid rgba(184,134,11,0.2)', boxShadow: '0 25px 50px rgba(159,18,57,0.2)' }}
            onClick={e => e.stopPropagation()}>
            <h4 className="font-semibold text-lg mb-2" style={{ color: '#059669' }}>Segna Pagamento</h4>
            <p className="text-sm mb-4" style={{ color: '#4A3B31' }}>{quickTenant.full_name}</p>
            <div className="space-y-3">
              <div>
                <p className="text-xs font-semibold mb-2" style={{ color: '#8B7355' }}>Metodo Pagamento</p>
                <div className="grid grid-cols-2 gap-2">
                  <button onClick={() => setQuickMethod('contanti')} className={`p-2.5 rounded-xl text-sm font-medium text-center transition-all ${quickMethod === 'contanti' ? 'ring-2 ring-emerald-500' : ''}`} style={{ background: quickMethod === 'contanti' ? '#D1FAE5' : '#F0FDF4', color: '#059669' }}>
                    Contanti
                  </button>
                  <button onClick={() => setQuickMethod('bonifico')} className={`p-2.5 rounded-xl text-sm font-medium text-center transition-all ${quickMethod === 'bonifico' ? 'ring-2 ring-emerald-500' : ''}`} style={{ background: quickMethod === 'bonifico' ? '#D1FAE5' : '#F0FDF4', color: '#059669' }}>
                    Bonifico
                  </button>
                </div>
              </div>
              <div>
                <p className="text-xs font-semibold mb-1" style={{ color: '#8B7355' }}>Importo (€)</p>
                <input type="number" placeholder="500" value={quickAmount} onChange={e => setQuickAmount(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl text-sm" style={{ border: '1px solid rgba(5,150,105,0.3)', background: 'white' }} />
              </div>
              <div className="flex gap-2 pt-2">
                <button onClick={() => { setQuickDialogOpen(false); setQuickTenant(null); }} className="flex-1 px-4 py-2 rounded-xl text-sm font-medium" style={{ color: '#8B7355', border: '1px solid rgba(184,134,11,0.2)' }}>
                  Annulla
                </button>
                <button onClick={handleQuickPaid} className="flex-1 px-4 py-2 rounded-xl text-sm font-semibold text-white" style={{ background: '#059669' }}>
                  Conferma
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Tenants;
