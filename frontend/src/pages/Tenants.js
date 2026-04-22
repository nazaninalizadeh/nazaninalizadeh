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
    full_name: '', codice_fiscale: '', passport_number: '', nationality: '',
    date_of_birth: '', passport_issue_date: '', passport_expiry_date: '',
    id_type: '', id_number: '', phone: '', email: '', whatsapp: '',
    notes: '', deposit_amount: 0, property_id: '', room_id: '',
    payment_due_day: 5,
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
    setFormData({ full_name: '', codice_fiscale: '', passport_number: '', nationality: '', date_of_birth: '', passport_issue_date: '', passport_expiry_date: '', id_type: '', id_number: '', phone: '', email: '', whatsapp: '', notes: '', deposit_amount: 0, property_id: '', room_id: '', payment_due_day: 5 });
    setEditingTenant(null);
  };

  const openEditDialog = (tenant) => {
    setEditingTenant(tenant);
    setFormData({
      full_name: tenant.full_name || '', codice_fiscale: tenant.codice_fiscale || '',
      passport_number: tenant.passport_number || '', nationality: tenant.nationality || '',
      date_of_birth: tenant.date_of_birth || '', passport_issue_date: tenant.passport_issue_date || '',
      passport_expiry_date: tenant.passport_expiry_date || '', id_type: tenant.id_type || '',
      id_number: tenant.id_number || '', phone: tenant.phone || '', email: tenant.email || '',
      whatsapp: tenant.whatsapp || '',
      notes: tenant.notes || '', deposit_amount: tenant.deposit_amount || 0,
      property_id: tenant.property_id || '', room_id: tenant.room_id || '',
      payment_due_day: tenant.payment_due_day || 5,
    });
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingTenant) {
        await axios.put(`${API_URL}/tenants/${editingTenant.id}`, formData, { withCredentials: true });
        toast.success('Inquilino aggiornato');
      } else {
        await axios.post(`${API_URL}/tenants`, formData, { withCredentials: true });
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

  // Status badge component
  const StatusBadge = ({ tenant }) => {
    if (tenant.payment_status === 'paid') {
      return (
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold" style={{ background: '#ECFDF5', color: '#059669' }}>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" /> Pagato
          </span>
          <span className="text-xs font-bold" style={{ color: '#059669' }}>&euro;{tenant.month_paid_amount?.toFixed(0)}</span>
          {tenant.month_payment_method && <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: 'rgba(184,134,11,0.08)', color: '#8B7355' }}>{tenant.month_payment_method}</span>}
        </div>
      );
    }
    if (tenant.payment_status === 'late') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold" style={{ background: '#FEF2F2', color: '#DC2626' }}>
          <span className="w-1.5 h-1.5 rounded-full bg-red-500" /> In Ritardo
        </span>
      );
    }
    if (tenant.room_id) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold" style={{ background: '#FFF7ED', color: '#D97706' }}>
          <span className="w-1.5 h-1.5 rounded-full bg-amber-500" /> Non Pagato
        </span>
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
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="luxury-title mb-2" data-testid="tenants-title">Inquilini</h1>
          <p className="luxury-subtitle">Gestisci inquilini e stato pagamenti</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="btn-luxury" data-testid="add-tenant-button"><Plus size={18} className="mr-2" />Aggiungi Inquilino</Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto luxury-modal">
            <DialogHeader><DialogTitle>{editingTenant ? 'Modifica Inquilino' : 'Nuovo Inquilino'}</DialogTitle></DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="pb-3 mb-3" style={{ borderBottom: '1px solid rgba(184,134,11,0.12)' }}>
                <OcrScanner onDataExtracted={(data) => { setFormData(prev => ({ ...prev, ...Object.fromEntries(Object.entries(data).filter(([_, v]) => v)) })); }} />
                <p className="text-xs mt-2" style={{ color: '#8B7355' }}>Scansiona un passaporto o documento per compilare automaticamente</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div><Label>Nome Completo *</Label><Input value={formData.full_name} onChange={e => setFormData({ ...formData, full_name: e.target.value })} required className="luxury-input" data-testid="tenant-name-input" /></div>
                <div><Label>Codice Fiscale</Label><Input value={formData.codice_fiscale} onChange={e => setFormData({ ...formData, codice_fiscale: e.target.value })} className="luxury-input" /></div>
                <div><Label>Numero Passaporto *</Label><Input value={formData.passport_number} onChange={e => setFormData({ ...formData, passport_number: e.target.value })} required className="luxury-input" /></div>
                <div><Label>Nazionalita *</Label><Input value={formData.nationality} onChange={e => setFormData({ ...formData, nationality: e.target.value })} required className="luxury-input" /></div>
                <div><Label>Data di Nascita *</Label><Input type="date" value={formData.date_of_birth} onChange={e => setFormData({ ...formData, date_of_birth: e.target.value })} required className="luxury-input" /></div>
                <div><Label>Rilascio Passaporto *</Label><Input type="date" value={formData.passport_issue_date} onChange={e => setFormData({ ...formData, passport_issue_date: e.target.value })} required className="luxury-input" /></div>
                <div><Label>Scadenza Passaporto *</Label><Input type="date" value={formData.passport_expiry_date} onChange={e => setFormData({ ...formData, passport_expiry_date: e.target.value })} required className="luxury-input" /></div>
                <div><Label>WhatsApp *</Label><Input value={formData.whatsapp} onChange={e => setFormData({ ...formData, whatsapp: e.target.value })} required className="luxury-input" placeholder="+39 333 1234567" /></div>
                <div><Label>Email *</Label><Input type="email" value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })} required className="luxury-input" data-testid="tenant-email-input" /></div>
                <div><Label>Deposito (Garanzia)</Label><Input type="number" step="0.01" value={formData.deposit_amount} onChange={e => setFormData({ ...formData, deposit_amount: parseFloat(e.target.value) || 0 })} className="luxury-input" /></div>
                <div><Label>Giorno Scadenza Pagamento</Label><Input type="number" min="1" max="28" value={formData.payment_due_day} onChange={e => setFormData({ ...formData, payment_due_day: parseInt(e.target.value) || 5 })} className="luxury-input" /></div>
              </div>
              <div className="grid grid-cols-2 gap-4">
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
    </div>
  );
};

export default Tenants;
