import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Plus, Search, Edit, Trash2, UserPlus, UserMinus, DoorOpen } from 'lucide-react';
import { Link } from 'react-router-dom';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const Rooms = () => {
  const [rooms, setRooms] = useState([]);
  const [properties, setProperties] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterProperty, setFilterProperty] = useState('all');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [assignDialog, setAssignDialog] = useState(false);
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [assignTenantId, setAssignTenantId] = useState('');
  const [formData, setFormData] = useState({
    property_id: '', room_number: '', room_type: 'single', floor: '', monthly_rent: 0, description: '', bill_responsible: ''
  });

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      const [r, p, t] = await Promise.all([
        axios.get(`${API}/rooms`, { withCredentials: true }),
        axios.get(`${API}/properties`, { withCredentials: true }),
        axios.get(`${API}/tenants`, { withCredentials: true }),
      ]);
      setRooms(r.data);
      setProperties(p.data);
      setTenants(t.data);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/rooms`, formData, { withCredentials: true });
      setDialogOpen(false);
      setFormData({ property_id: '', room_number: '', room_type: 'single', floor: '', monthly_rent: 0, description: '', bill_responsible: '' });
      fetchAll();
    } catch (err) { alert(err.response?.data?.detail || 'Errore'); }
  };

  const handleAssign = async () => {
    if (!selectedRoom || !assignTenantId) return;
    try {
      const fd = new FormData();
      fd.append('tenant_id', assignTenantId);
      await axios.post(`${API}/rooms/${selectedRoom.id}/assign`, fd, { withCredentials: true });
      setAssignDialog(false);
      setAssignTenantId('');
      fetchAll();
    } catch (err) { alert(err.response?.data?.detail || 'Errore'); }
  };

  const handleUnassign = async (roomId) => {
    if (!window.confirm('Rimuovere inquilino dalla stanza?')) return;
    try {
      await axios.post(`${API}/rooms/${roomId}/unassign`, {}, { withCredentials: true });
      fetchAll();
    } catch (err) { alert(err.response?.data?.detail || 'Errore'); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Eliminare questa stanza?')) return;
    try {
      await axios.delete(`${API}/rooms/${id}`, { withCredentials: true });
      fetchAll();
    } catch (err) { alert(err.response?.data?.detail || 'Errore'); }
  };

  const filtered = rooms.filter(r => {
    const matchSearch = r.room_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.tenant_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.property_address?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchProp = filterProperty === 'all' || r.property_id === filterProperty;
    return matchSearch && matchProp;
  });

  return (
    <div data-testid="rooms-page" className="luxury-fade-in">
      <div className="mb-10 flex items-center justify-between">
        <div>
          <h1 className="luxury-title mb-2" data-testid="rooms-title">Stanze</h1>
          <p className="luxury-subtitle">Gestisci stanze, assegnazioni e occupazione</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="btn-luxury" data-testid="add-room-button"><Plus size={18} className="mr-2" /> Aggiungi Stanza</Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg luxury-modal">
            <DialogHeader><DialogTitle>Nuova Stanza</DialogTitle></DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label>Immobile *</Label>
                <Select value={formData.property_id} onValueChange={v => setFormData({ ...formData, property_id: v })}>
                  <SelectTrigger><SelectValue placeholder="Seleziona immobile" /></SelectTrigger>
                  <SelectContent>{properties.map(p => <SelectItem key={p.id} value={p.id}>{p.property_code} - {p.address}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div><Label>N. Stanza *</Label><Input value={formData.room_number} onChange={e => setFormData({ ...formData, room_number: e.target.value })} required className="luxury-input" /></div>
                <div>
                  <Label>Tipo *</Label>
                  <Select value={formData.room_type} onValueChange={v => setFormData({ ...formData, room_type: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="single">Singola</SelectItem>
                      <SelectItem value="double">Doppia</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div><Label>Piano</Label><Input value={formData.floor} onChange={e => setFormData({ ...formData, floor: e.target.value })} className="luxury-input" /></div>
                <div><Label>Affitto Mensile</Label><Input type="number" step="0.01" value={formData.monthly_rent} onChange={e => setFormData({ ...formData, monthly_rent: parseFloat(e.target.value) || 0 })} className="luxury-input" /></div>
              </div>
              <div><Label>Descrizione</Label><Input value={formData.description} onChange={e => setFormData({ ...formData, description: e.target.value })} className="luxury-input" /></div>
              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)} className="rounded-xl">Annulla</Button>
                <Button type="submit" className="btn-luxury">Crea Stanza</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Assign Dialog */}
      <Dialog open={assignDialog} onOpenChange={setAssignDialog}>
        <DialogContent className="luxury-modal">
          <DialogHeader><DialogTitle>Assegna Inquilino a Stanza {selectedRoom?.room_number}</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <Select value={assignTenantId} onValueChange={setAssignTenantId}>
              <SelectTrigger><SelectValue placeholder="Seleziona inquilino" /></SelectTrigger>
              <SelectContent>{tenants.filter(t => !t.room_id).map(t => <SelectItem key={t.id} value={t.id}>{t.full_name}</SelectItem>)}</SelectContent>
            </Select>
            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => setAssignDialog(false)} className="rounded-xl">Annulla</Button>
              <Button onClick={handleAssign} className="btn-luxury">Assegna</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <div className="luxury-card overflow-hidden">
        <div className="p-5 flex gap-4" style={{ borderBottom: '1px solid rgba(184,134,11,0.12)' }}>
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2" size={18} style={{ color: '#B8860B' }} />
            <Input placeholder="Cerca stanza..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="pl-11 luxury-input" />
          </div>
          <Select value={filterProperty} onValueChange={setFilterProperty}>
            <SelectTrigger className="w-[200px]"><SelectValue placeholder="Filtra per immobile" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tutti gli immobili</SelectItem>
              {properties.map(p => <SelectItem key={p.id} value={p.id}>{p.property_code}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>

        {loading ? (
          <div className="flex items-center justify-center p-12"><div className="luxury-spinner h-10 w-10" /></div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow style={{ background: 'linear-gradient(135deg, #9F1239 0%, #BE123C 100%)' }}>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Stanza</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Immobile</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Tipo</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Stato</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Inquilino</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Affitto</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider text-right">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.length === 0 ? (
                <TableRow><TableCell colSpan={7} className="text-center py-10" style={{ color: '#8B7355' }}>Nessuna stanza trovata</TableCell></TableRow>
              ) : filtered.map(room => (
                <TableRow key={room.id} className="hover:bg-rose-50/30 transition-colors">
                  <TableCell className="font-medium" style={{ color: '#2C1810' }}><DoorOpen size={16} className="inline mr-2" style={{ color: '#9F1239' }} />{room.room_number}</TableCell>
                  <TableCell style={{ color: '#4A3B31' }}>{room.property_address}</TableCell>
                  <TableCell><span className="luxury-badge" style={{ background: room.room_type === 'double' ? '#EDE9FE' : '#F0FDF4', color: room.room_type === 'double' ? '#7C3AED' : '#059669' }}>{room.room_type === 'single' ? 'Singola' : 'Doppia'}</span></TableCell>
                  <TableCell><span className={`luxury-badge ${room.status === 'occupied' ? 'badge-success' : ''}`} style={room.status !== 'occupied' ? { background: '#FEF2F2', color: '#DC2626' } : {}}>{room.status === 'occupied' ? 'Occupata' : 'Libera'}</span></TableCell>
                  <TableCell>{room.tenant_name ? <Link to={`/tenants/${room.tenant_id}`} className="font-medium underline" style={{ color: '#9F1239' }}>{room.tenant_name}</Link> : <span style={{ color: '#8B7355' }}>-</span>}</TableCell>
                  <TableCell className="font-medium" style={{ color: '#2C1810' }}>&euro;{room.monthly_rent?.toFixed(2)}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      {room.status === 'available' ? (
                        <Button variant="ghost" size="sm" className="rounded-lg hover:bg-green-50" onClick={() => { setSelectedRoom(room); setAssignDialog(true); }}><UserPlus size={16} style={{ color: '#059669' }} /></Button>
                      ) : (
                        <Button variant="ghost" size="sm" className="rounded-lg hover:bg-orange-50" onClick={() => handleUnassign(room.id)}><UserMinus size={16} style={{ color: '#D97706' }} /></Button>
                      )}
                      <Button variant="ghost" size="sm" className="rounded-lg hover:bg-red-50" onClick={() => handleDelete(room.id)}><Trash2 size={16} className="text-red-500" /></Button>
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

export default Rooms;
