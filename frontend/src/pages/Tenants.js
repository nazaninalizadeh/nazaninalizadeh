import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { Plus, Search, Eye, Edit, Trash2 } from 'lucide-react';
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
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingTenant, setEditingTenant] = useState(null);
  const [formData, setFormData] = useState({
    full_name: '', codice_fiscale: '', passport_number: '', nationality: '',
    date_of_birth: '', passport_issue_date: '', passport_expiry_date: '',
    id_type: '', id_number: '', phone: '', email: '', whatsapp: '',
    address: '', occupation: '', notes: '', deposit_amount: 0,
    property_id: '', room_id: ''
  });

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      const [t, p, r] = await Promise.all([
        axios.get(`${API_URL}/tenants`, { withCredentials: true }),
        axios.get(`${API_URL}/properties`, { withCredentials: true }),
        axios.get(`${API_URL}/rooms`, { withCredentials: true }),
      ]);
      setTenants(t.data);
      setProperties(p.data);
      setRooms(r.data);
    } catch (err) { toast.error('Errore nel caricamento'); }
    setLoading(false);
  };

  const resetForm = () => {
    setFormData({ full_name: '', codice_fiscale: '', passport_number: '', nationality: '', date_of_birth: '', passport_issue_date: '', passport_expiry_date: '', id_type: '', id_number: '', phone: '', email: '', whatsapp: '', address: '', occupation: '', notes: '', deposit_amount: 0, property_id: '', room_id: '' });
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
      whatsapp: tenant.whatsapp || '', address: tenant.address || '', occupation: tenant.occupation || '',
      notes: tenant.notes || '', deposit_amount: tenant.deposit_amount || 0,
      property_id: tenant.property_id || '', room_id: tenant.room_id || ''
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
      setDialogOpen(false);
      resetForm();
      fetchAll();
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore'); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Eliminare questo inquilino?')) return;
    try {
      await axios.delete(`${API_URL}/tenants/${id}`, { withCredentials: true });
      toast.success('Inquilino eliminato');
      fetchAll();
    } catch (err) { toast.error('Errore'); }
  };

  const filteredTenants = tenants.filter(t =>
    t.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.passport_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.codice_fiscale?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const availableRooms = rooms.filter(r => r.property_id === formData.property_id && (r.status === 'available' || r.id === formData.room_id));

  return (
    <div data-testid="tenants-page" className="luxury-fade-in">
      <div className="mb-10 flex items-center justify-between">
        <div>
          <h1 className="luxury-title mb-2" data-testid="tenants-title">Inquilini</h1>
          <p className="luxury-subtitle">Gestisci inquilini e stato pagamenti</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="btn-luxury" data-testid="add-tenant-button"><Plus size={18} className="mr-2" />Aggiungi Inquilino</Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto luxury-modal">
            <DialogHeader>
              <DialogTitle>{editingTenant ? 'Modifica Inquilino' : 'Nuovo Inquilino'}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* OCR Scanner */}
              <div className="pb-3 mb-3" style={{ borderBottom: '1px solid rgba(184,134,11,0.12)' }}>
                <OcrScanner onDataExtracted={(data) => {
                  setFormData(prev => ({
                    ...prev,
                    ...Object.fromEntries(Object.entries(data).filter(([_, v]) => v))
                  }));
                }} />
                <p className="text-xs mt-2" style={{ color: '#8B7355' }}>
                  Scansiona un passaporto o documento d'identita per compilare automaticamente i campi
                </p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div><Label>Nome Completo *</Label><Input value={formData.full_name} onChange={e => setFormData({ ...formData, full_name: e.target.value })} required className="luxury-input" data-testid="tenant-name-input" /></div>
                <div><Label>Codice Fiscale</Label><Input value={formData.codice_fiscale} onChange={e => setFormData({ ...formData, codice_fiscale: e.target.value })} className="luxury-input" placeholder="RSSMRA85M01H501Z" /></div>
                <div><Label>Numero Passaporto *</Label><Input value={formData.passport_number} onChange={e => setFormData({ ...formData, passport_number: e.target.value })} required className="luxury-input" /></div>
                <div><Label>Nazionalita *</Label><Input value={formData.nationality} onChange={e => setFormData({ ...formData, nationality: e.target.value })} required className="luxury-input" /></div>
                <div><Label>Data di Nascita *</Label><Input type="date" value={formData.date_of_birth} onChange={e => setFormData({ ...formData, date_of_birth: e.target.value })} required className="luxury-input" /></div>
                <div><Label>Rilascio Passaporto *</Label><Input type="date" value={formData.passport_issue_date} onChange={e => setFormData({ ...formData, passport_issue_date: e.target.value })} required className="luxury-input" /></div>
                <div><Label>Scadenza Passaporto *</Label><Input type="date" value={formData.passport_expiry_date} onChange={e => setFormData({ ...formData, passport_expiry_date: e.target.value })} required className="luxury-input" /></div>
                <div><Label>Tipo Documento ID</Label><Input value={formData.id_type} onChange={e => setFormData({ ...formData, id_type: e.target.value })} className="luxury-input" placeholder="Carta d'identita, Patente..." /></div>
                <div><Label>Numero Documento ID</Label><Input value={formData.id_number} onChange={e => setFormData({ ...formData, id_number: e.target.value })} className="luxury-input" /></div>
                <div><Label>Telefono *</Label><Input type="tel" value={formData.phone} onChange={e => setFormData({ ...formData, phone: e.target.value })} required className="luxury-input" /></div>
                <div><Label>Email *</Label><Input type="email" value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })} required className="luxury-input" data-testid="tenant-email-input" /></div>
                <div><Label>WhatsApp *</Label><Input value={formData.whatsapp} onChange={e => setFormData({ ...formData, whatsapp: e.target.value })} required className="luxury-input" /></div>
                <div><Label>Professione *</Label><Input value={formData.occupation} onChange={e => setFormData({ ...formData, occupation: e.target.value })} required className="luxury-input" /></div>
                <div><Label>Deposito (Garanzia)</Label><Input type="number" step="0.01" value={formData.deposit_amount} onChange={e => setFormData({ ...formData, deposit_amount: parseFloat(e.target.value) || 0 })} className="luxury-input" /></div>
              </div>
              <div><Label>Indirizzo *</Label><Input value={formData.address} onChange={e => setFormData({ ...formData, address: e.target.value })} required className="luxury-input" /></div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Immobile Assegnato</Label>
                  <Select value={formData.property_id || 'none'} onValueChange={v => setFormData({ ...formData, property_id: v === 'none' ? '' : v, room_id: '' })}>
                    <SelectTrigger><SelectValue placeholder="Seleziona immobile" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Nessuno</SelectItem>
                      {properties.map(p => <SelectItem key={p.id} value={p.id}>{p.property_code} - {p.address}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Stanza Assegnata</Label>
                  <Select value={formData.room_id || 'none'} onValueChange={v => setFormData({ ...formData, room_id: v === 'none' ? '' : v })} disabled={!formData.property_id}>
                    <SelectTrigger><SelectValue placeholder="Seleziona stanza" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Nessuna</SelectItem>
                      {availableRooms.map(r => <SelectItem key={r.id} value={r.id}>Stanza {r.room_number} ({r.room_type})</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div><Label>Note</Label><Input value={formData.notes} onChange={e => setFormData({ ...formData, notes: e.target.value })} className="luxury-input notes-text" /></div>
              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="rounded-xl">Annulla</Button>
                <Button type="submit" className="btn-luxury" data-testid="save-tenant-button">{editingTenant ? 'Aggiorna' : 'Crea'}</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="luxury-card overflow-hidden">
        <div className="p-5" style={{ borderBottom: '1px solid rgba(184,134,11,0.12)' }}>
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2" size={18} style={{ color: '#B8860B' }} />
            <Input placeholder="Cerca per nome, passaporto, codice fiscale..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="pl-11 luxury-input" data-testid="search-tenant-input" />
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center p-12"><div className="luxury-spinner h-10 w-10" /></div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow style={{ background: 'linear-gradient(135deg, #9F1239 0%, #BE123C 100%)' }}>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Nome</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Immobile</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Stanza</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Deposito</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Stato Mese</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider text-right">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredTenants.length === 0 ? (
                <TableRow><TableCell colSpan={6} className="text-center py-10" style={{ color: '#8B7355' }}>Nessun inquilino trovato</TableCell></TableRow>
              ) : filteredTenants.map(tenant => (
                <TableRow key={tenant.id} className="hover:bg-rose-50/30 transition-colors" data-testid={`tenant-row-${tenant.id}`}>
                  <TableCell className="font-medium" style={{ color: '#2C1810' }}>{tenant.full_name}</TableCell>
                  <TableCell style={{ color: '#4A3B31' }}>{tenant.property_address || '-'}</TableCell>
                  <TableCell style={{ color: '#4A3B31' }}>{tenant.room_number || '-'}</TableCell>
                  <TableCell style={{ color: '#4A3B31' }}>&euro;{(tenant.deposit_amount || 0).toFixed(0)}</TableCell>
                  <TableCell>
                    {tenant.payment_status === 'paid' ? (
                      <div className="flex items-center gap-2">
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold" style={{ background: '#ECFDF5', color: '#059669' }} data-testid={`status-paid-${tenant.id}`}>
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                          Pagato
                        </span>
                        <span className="text-xs font-bold" style={{ color: '#059669' }}>&euro;{tenant.month_paid_amount?.toFixed(0)}</span>
                        {tenant.month_payment_method && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: 'rgba(184,134,11,0.08)', color: '#8B7355' }}>{tenant.month_payment_method}</span>
                        )}
                      </div>
                    ) : tenant.room_id ? (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold" style={{ background: '#FEF2F2', color: '#DC2626' }} data-testid={`status-notpaid-${tenant.id}`}>
                        <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                        Non Pagato
                      </span>
                    ) : (
                      <span className="text-xs" style={{ color: '#94A3B8' }}>-</span>
                    )}
                  </TableCell>
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
