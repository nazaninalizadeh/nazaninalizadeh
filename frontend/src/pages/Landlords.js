import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { Plus, Search, Eye, Edit, Trash2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Landlords = () => {
  const [landlords, setLandlords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingLandlord, setEditingLandlord] = useState(null);
  const [formData, setFormData] = useState({
    full_name: '', codice_fiscale: '', phone: '', email: '', whatsapp: '',
    id_type: '', id_number: '', bank_details: '', notes: ''
  });

  useEffect(() => { fetchLandlords(); }, []);

  const fetchLandlords = async () => {
    try {
      const { data } = await axios.get(`${API_URL}/landlords`, { withCredentials: true });
      setLandlords(data);
    } catch { toast.error('Errore'); }
    setLoading(false);
  };

  const resetForm = () => {
    setFormData({ full_name: '', codice_fiscale: '', phone: '', email: '', whatsapp: '', id_type: '', id_number: '', bank_details: '', notes: '' });
    setEditingLandlord(null);
  };

  const openEditDialog = (ll) => {
    setEditingLandlord(ll);
    setFormData({
      full_name: ll.full_name || '', codice_fiscale: ll.codice_fiscale || '',
      phone: ll.phone || '', email: ll.email || '', whatsapp: ll.whatsapp || '',
      id_type: ll.id_type || '', id_number: ll.id_number || '',
      bank_details: ll.bank_details || '', notes: ll.notes || ''
    });
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingLandlord) {
        await axios.put(`${API_URL}/landlords/${editingLandlord.id}`, formData, { withCredentials: true });
        toast.success('Proprietario aggiornato');
      } else {
        await axios.post(`${API_URL}/landlords`, formData, { withCredentials: true });
        toast.success('Proprietario creato');
      }
      setDialogOpen(false); resetForm(); fetchLandlords();
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore'); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Eliminare?')) return;
    try {
      await axios.delete(`${API_URL}/landlords/${id}`, { withCredentials: true });
      toast.success('Eliminato');
      fetchLandlords();
    } catch { toast.error('Errore'); }
  };

  const filtered = landlords.filter(l =>
    l.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    l.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    l.codice_fiscale?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div data-testid="landlords-page" className="luxury-fade-in">
      <div className="mb-10 flex items-center justify-between">
        <div>
          <h1 className="luxury-title mb-2">Proprietari</h1>
          <p className="luxury-subtitle">Gestisci proprietari, immobili e occupazione</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(o) => { setDialogOpen(o); if (!o) resetForm(); }}>
          <DialogTrigger asChild><Button className="btn-luxury"><Plus size={18} className="mr-2" />Aggiungi Proprietario</Button></DialogTrigger>
          <DialogContent className="max-w-2xl luxury-modal">
            <DialogHeader><DialogTitle>{editingLandlord ? 'Modifica' : 'Nuovo'} Proprietario</DialogTitle></DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div><Label>Nome Completo *</Label><Input value={formData.full_name} onChange={e => setFormData({ ...formData, full_name: e.target.value })} required className="luxury-input" /></div>
                <div><Label>Codice Fiscale</Label><Input value={formData.codice_fiscale} onChange={e => setFormData({ ...formData, codice_fiscale: e.target.value })} className="luxury-input" /></div>
                <div><Label>Tipo Doc. ID</Label><Input value={formData.id_type} onChange={e => setFormData({ ...formData, id_type: e.target.value })} className="luxury-input" placeholder="Carta d'identita..." /></div>
                <div><Label>Numero Documento *</Label><Input value={formData.id_number} onChange={e => setFormData({ ...formData, id_number: e.target.value })} required className="luxury-input" /></div>
                <div><Label>Telefono *</Label><Input value={formData.phone} onChange={e => setFormData({ ...formData, phone: e.target.value })} required className="luxury-input" /></div>
                <div><Label>Email *</Label><Input type="email" value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })} required className="luxury-input" /></div>
                <div><Label>WhatsApp *</Label><Input value={formData.whatsapp} onChange={e => setFormData({ ...formData, whatsapp: e.target.value })} required className="luxury-input" /></div>
                <div><Label>Dati Bancari *</Label><Input value={formData.bank_details} onChange={e => setFormData({ ...formData, bank_details: e.target.value })} required className="luxury-input" /></div>
              </div>
              <div><Label>Note</Label><Input value={formData.notes} onChange={e => setFormData({ ...formData, notes: e.target.value })} className="luxury-input notes-text" /></div>
              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="rounded-xl">Annulla</Button>
                <Button type="submit" className="btn-luxury">{editingLandlord ? 'Aggiorna' : 'Crea'}</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="luxury-card overflow-hidden">
        <div className="p-5" style={{ borderBottom: '1px solid rgba(184,134,11,0.12)' }}>
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2" size={18} style={{ color: '#B8860B' }} />
            <Input placeholder="Cerca proprietario..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="pl-11 luxury-input" />
          </div>
        </div>
        {loading ? (
          <div className="flex items-center justify-center p-12"><div className="luxury-spinner h-10 w-10" /></div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow style={{ background: 'linear-gradient(135deg, #9F1239 0%, #BE123C 100%)' }}>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Nome</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Codice Fiscale</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Email</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Immobili</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Stanze Occ./Tot.</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Libere</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider text-right">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.length === 0 ? (
                <TableRow><TableCell colSpan={7} className="text-center py-10" style={{ color: '#8B7355' }}>Nessun proprietario</TableCell></TableRow>
              ) : filtered.map(ll => (
                <TableRow key={ll.id} className="hover:bg-rose-50/30 transition-colors">
                  <TableCell className="font-medium" style={{ color: '#2C1810' }}>{ll.full_name}</TableCell>
                  <TableCell className="font-mono text-xs" style={{ color: '#4A3B31' }}>{ll.codice_fiscale || '-'}</TableCell>
                  <TableCell style={{ color: '#4A3B31' }}>{ll.email}</TableCell>
                  <TableCell className="font-medium" style={{ color: '#2C1810' }}>{ll.properties_count}</TableCell>
                  <TableCell>
                    <span style={{ color: '#059669' }}>{ll.occupied_rooms || 0}</span>/<span style={{ color: '#2C1810' }}>{ll.total_rooms || 0}</span>
                  </TableCell>
                  <TableCell>
                    <span className="font-bold" style={{ color: (ll.vacant_rooms || 0) > 0 ? '#DC2626' : '#059669' }}>{ll.vacant_rooms || 0}</span>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      <Link to={`/landlords/${ll.id}`}><Button variant="ghost" size="sm" className="rounded-lg hover:bg-rose-50"><Eye size={16} style={{ color: '#9F1239' }} /></Button></Link>
                      <Button variant="ghost" size="sm" className="rounded-lg hover:bg-amber-50" onClick={() => openEditDialog(ll)}><Edit size={16} style={{ color: '#B8860B' }} /></Button>
                      <Button variant="ghost" size="sm" className="rounded-lg hover:bg-red-50" onClick={() => handleDelete(ll.id)}><Trash2 size={16} className="text-red-500" /></Button>
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

export default Landlords;
