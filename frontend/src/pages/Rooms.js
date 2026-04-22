import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Plus, Search, UserPlus, UserMinus, Trash2, DoorOpen, Home, Filter, Edit } from 'lucide-react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const Rooms = () => {
  const [overview, setOverview] = useState([]);
  const [properties, setProperties] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [filterHome, setFilterHome] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterMethod, setFilterMethod] = useState('all');
  const [searchName, setSearchName] = useState('');

  // Dialogs
  const [addRoomOpen, setAddRoomOpen] = useState(false);
  const [editRoomOpen, setEditRoomOpen] = useState(false);
  const [assignOpen, setAssignOpen] = useState(false);
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [assignTenantId, setAssignTenantId] = useState('');
  const [assignSearch, setAssignSearch] = useState('');
  const [roomForm, setRoomForm] = useState({
    property_id: '', room_number: '', room_type: 'single', floor: '', monthly_rent: 0, description: '', bill_responsible: ''
  });
  const [roomPropertySearch, setRoomPropertySearch] = useState('');
  const [editRoomForm, setEditRoomForm] = useState({
    property_id: '', room_number: '', room_type: 'single', floor: '', monthly_rent: 0, description: '', bill_responsible: ''
  });

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      const [ov, pr, tn] = await Promise.all([
        axios.get(`${API}/occupancy-overview`, { withCredentials: true }),
        axios.get(`${API}/properties`, { withCredentials: true }),
        axios.get(`${API}/tenants`, { withCredentials: true }),
      ]);
      setOverview(ov.data);
      setProperties(pr.data);
      setTenants(tn.data);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const handleAddRoom = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/rooms`, roomForm, { withCredentials: true });
      toast.success('Stanza aggiunta');
      setAddRoomOpen(false);
      setRoomForm({ property_id: '', room_number: '', room_type: 'single', floor: '', monthly_rent: 0, description: '', bill_responsible: '' });
      fetchAll();
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore'); }
  };

  const openEditRoom = (room) => {
    setSelectedRoom(room);
    setEditRoomForm({
      property_id: room.property_id || '', room_number: room.room_number || '',
      room_type: room.room_type || 'single', floor: room.floor || '',
      monthly_rent: room.monthly_rent || 0, description: room.description || '',
      bill_responsible: room.bill_responsible || '',
    });
    setEditRoomOpen(true);
  };

  const handleEditRoom = async (e) => {
    e.preventDefault();
    if (!selectedRoom) return;
    try {
      await axios.put(`${API}/rooms/${selectedRoom.id}`, editRoomForm, { withCredentials: true });
      toast.success('Stanza aggiornata');
      setEditRoomOpen(false);
      setSelectedRoom(null);
      fetchAll();
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore'); }
  };

  const handleAssign = async () => {
    if (!selectedRoom || !assignTenantId) return;
    try {
      const fd = new FormData();
      fd.append('tenant_id', assignTenantId);
      await axios.post(`${API}/rooms/${selectedRoom.id}/assign`, fd, { withCredentials: true });
      toast.success('Inquilino assegnato');
      setAssignOpen(false);
      setAssignTenantId('');
      fetchAll();
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore'); }
  };

  const handleUnassign = async (roomId) => {
    if (!window.confirm('Rimuovere inquilino?')) return;
    try {
      await axios.post(`${API}/rooms/${roomId}/unassign`, {}, { withCredentials: true });
      toast.success('Inquilino rimosso');
      fetchAll();
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore'); }
  };

  const handleDeleteRoom = async (roomId) => {
    if (!window.confirm('Eliminare stanza?')) return;
    try {
      await axios.delete(`${API}/rooms/${roomId}`, { withCredentials: true });
      toast.success('Stanza eliminata');
      fetchAll();
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore'); }
  };

  // Apply filters
  const filteredOverview = overview
    .filter(p => filterHome === 'all' || p.id === filterHome)
    .map(prop => ({
      ...prop,
      rooms: prop.rooms.filter(r => {
        if (filterStatus === 'paid' && r.payment_status !== 'paid') return false;
        if (filterStatus === 'not_paid' && r.payment_status !== 'not_paid') return false;
        if (filterStatus === 'empty' && r.status !== 'available') return false;
        if (filterMethod === 'contanti' && r.payment_method !== 'Contanti') return false;
        if (filterMethod === 'bonifico' && r.payment_method !== 'Bonifico') return false;
        if (searchName && r.tenant_name && !r.tenant_name.toLowerCase().includes(searchName.toLowerCase())) return false;
        if (searchName && !r.tenant_name) return false;
        return true;
      })
    }))
    .filter(p => p.rooms.length > 0 || (filterStatus === 'all' && filterMethod === 'all' && !searchName));

  // Summary stats
  const allRooms = overview.flatMap(p => p.rooms);
  const totalOccupied = allRooms.filter(r => r.status === 'occupied').length;
  const totalVacant = allRooms.filter(r => r.status === 'available').length;
  const totalPaid = allRooms.filter(r => r.payment_status === 'paid').length;
  const totalNotPaid = allRooms.filter(r => r.payment_status === 'not_paid').length;

  if (loading) return <div className="flex items-center justify-center p-12"><div className="luxury-spinner h-10 w-10" /></div>;

  return (
    <div data-testid="rooms-page" className="luxury-fade-in">
      <div className="mb-8 flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="luxury-title mb-2" data-testid="rooms-title">Panoramica Immobili</h1>
          <p className="luxury-subtitle">Chi abita dove, chi ha pagato e come</p>
        </div>
        <Dialog open={addRoomOpen} onOpenChange={setAddRoomOpen}>
          <DialogTrigger asChild>
            <Button className="btn-luxury" data-testid="add-room-button"><Plus size={18} className="mr-2" /> Aggiungi Stanza</Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg luxury-modal" style={{ background: '#FFFBF5' }}>
            <DialogHeader><DialogTitle>Nuova Stanza</DialogTitle></DialogHeader>
            <form onSubmit={handleAddRoom} className="space-y-4">
              <div>
                <Label>Cerca Immobile *</Label>
                <Input placeholder="Cerca per nome/indirizzo..." value={roomPropertySearch} onChange={e => setRoomPropertySearch(e.target.value)} className="luxury-input mb-2" />
                <div className="max-h-36 overflow-y-auto space-y-1 rounded-xl p-2" style={{ background: 'white', border: '1px solid rgba(184,134,11,0.15)' }}>
                  {properties.filter(p => !roomPropertySearch || p.address?.toLowerCase().includes(roomPropertySearch.toLowerCase()) || p.property_code?.toLowerCase().includes(roomPropertySearch.toLowerCase())).map(p => (
                    <button type="button" key={p.id} onClick={() => setRoomForm({ ...roomForm, property_id: p.id })}
                      className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all ${roomForm.property_id === p.id ? 'font-bold' : ''}`}
                      style={{ background: roomForm.property_id === p.id ? 'rgba(159,18,57,0.08)' : 'transparent', color: roomForm.property_id === p.id ? '#9F1239' : '#4A3B31' }}>
                      <span className="font-medium">{p.address}</span> <span className="text-xs" style={{ color: '#8B7355' }}>({p.property_code})</span>
                    </button>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div><Label>N. Stanza *</Label><Input value={roomForm.room_number} onChange={e => setRoomForm({ ...roomForm, room_number: e.target.value })} required className="luxury-input" /></div>
                <div>
                  <Label>Tipo *</Label>
                  <Select value={roomForm.room_type} onValueChange={v => setRoomForm({ ...roomForm, room_type: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent><SelectItem value="single">Singola</SelectItem><SelectItem value="double">Doppia</SelectItem></SelectContent>
                  </Select>
                </div>
                <div><Label>Piano</Label><Input value={roomForm.floor} onChange={e => setRoomForm({ ...roomForm, floor: e.target.value })} className="luxury-input" /></div>
                <div><Label>Affitto Mensile</Label><Input type="number" step="0.01" value={roomForm.monthly_rent} onChange={e => setRoomForm({ ...roomForm, monthly_rent: parseFloat(e.target.value) || 0 })} className="luxury-input" /></div>
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => setAddRoomOpen(false)} className="rounded-xl">Annulla</Button>
                <Button type="submit" className="btn-luxury">Crea Stanza</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        <div className="luxury-card p-4 text-center">
          <p className="text-xs uppercase tracking-wide" style={{ color: '#8B7355' }}>Occupate</p>
          <p className="text-2xl font-bold" style={{ color: '#059669' }}>{totalOccupied}</p>
        </div>
        <div className="luxury-card p-4 text-center">
          <p className="text-xs uppercase tracking-wide" style={{ color: '#8B7355' }}>Libere</p>
          <p className="text-2xl font-bold" style={{ color: '#DC2626' }}>{totalVacant}</p>
        </div>
        <div className="luxury-card p-4 text-center">
          <p className="text-xs uppercase tracking-wide" style={{ color: '#8B7355' }}>Pagato</p>
          <p className="text-2xl font-bold" style={{ color: '#059669' }}>{totalPaid}</p>
        </div>
        <div className="luxury-card p-4 text-center">
          <p className="text-xs uppercase tracking-wide" style={{ color: '#8B7355' }}>Non Pagato</p>
          <p className="text-2xl font-bold" style={{ color: '#DC2626' }}>{totalNotPaid}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="luxury-card p-5 mb-8">
        <div className="flex items-center gap-2 mb-3">
          <Filter size={16} style={{ color: '#B8860B' }} />
          <span className="text-sm font-semibold" style={{ color: '#4A3B31' }}>Filtri</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div>
            <Label className="text-xs">Immobile</Label>
            <Select value={filterHome} onValueChange={setFilterHome}>
              <SelectTrigger className="h-9"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tutti</SelectItem>
                {overview.map(p => <SelectItem key={p.id} value={p.id}>{p.property_code} - {p.address}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs">Stato Pagamento</Label>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="h-9"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tutti</SelectItem>
                <SelectItem value="paid">Pagato</SelectItem>
                <SelectItem value="not_paid">Non Pagato</SelectItem>
                <SelectItem value="empty">Stanze Vuote</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs">Metodo Pagamento</Label>
            <Select value={filterMethod} onValueChange={setFilterMethod}>
              <SelectTrigger className="h-9"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tutti</SelectItem>
                <SelectItem value="contanti">Contanti</SelectItem>
                <SelectItem value="bonifico">Bonifico</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs">Nome Inquilino</Label>
            <Input placeholder="Cerca nome..." value={searchName} onChange={e => setSearchName(e.target.value)} className="luxury-input h-9" />
          </div>
        </div>
      </div>

      {/* Assign Dialog - with search */}
      <Dialog open={assignOpen} onOpenChange={setAssignOpen}>
        <DialogContent className="luxury-modal" style={{ background: '#FFFBF5' }}>
          <DialogHeader><DialogTitle>Assegna Inquilino a Stanza {selectedRoom?.room_number}</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-xs mb-1 block">Cerca Inquilino</Label>
              <Input placeholder="Cerca per nome..." value={assignSearch} onChange={e => setAssignSearch(e.target.value)} className="luxury-input mb-2" autoFocus />
            </div>
            <div className="max-h-48 overflow-y-auto space-y-1 rounded-xl p-2" style={{ background: 'white', border: '1px solid rgba(184,134,11,0.15)' }}>
              {tenants.filter(t => !t.room_id).filter(t => !assignSearch || t.full_name?.toLowerCase().includes(assignSearch.toLowerCase())).map(t => (
                <button key={t.id} onClick={() => setAssignTenantId(t.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all ${assignTenantId === t.id ? 'font-bold' : ''}`}
                  style={{ background: assignTenantId === t.id ? 'rgba(159,18,57,0.08)' : 'transparent', color: assignTenantId === t.id ? '#9F1239' : '#4A3B31' }}>
                  {t.full_name} {t.nationality ? `(${t.nationality})` : ''}
                </button>
              ))}
              {tenants.filter(t => !t.room_id).filter(t => !assignSearch || t.full_name?.toLowerCase().includes(assignSearch.toLowerCase())).length === 0 && (
                <p className="text-center text-xs py-4" style={{ color: '#8B7355' }}>Nessun inquilino disponibile</p>
              )}
            </div>
            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => setAssignOpen(false)} className="rounded-xl">Annulla</Button>
              <Button onClick={handleAssign} className="btn-luxury" disabled={!assignTenantId}>Assegna</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Property Cards with Rooms */}
      {filteredOverview.length === 0 ? (
        <div className="luxury-card p-14 text-center">
          <Home className="mx-auto mb-4" size={64} style={{ color: 'rgba(184,134,11,0.3)' }} />
          <h3 className="text-lg font-semibold mb-2" style={{ color: '#2C1810' }}>Nessun Immobile</h3>
          <p style={{ color: '#8B7355' }}>Aggiungi immobili e stanze per vedere la panoramica</p>
        </div>
      ) : (
        <div className="space-y-6">
          {filteredOverview.map(prop => (
            <div key={prop.id} className="luxury-card overflow-hidden" data-testid={`property-card-${prop.id}`}>
              {/* Property Header */}
              <div className="px-6 py-4 flex items-center justify-between" style={{ background: 'linear-gradient(135deg, #9F1239 0%, #BE123C 100%)' }}>
                <div className="flex items-center gap-3">
                  <Home size={22} className="text-white" />
                  <div>
                    <h3 className="text-white font-semibold text-lg">{prop.address}</h3>
                    <p className="text-white/70 text-xs">Codice: {prop.property_code} | Proprietario: {prop.landlord_name}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-white text-sm">
                  <span><span className="font-bold">{prop.occupied_rooms}</span> occupate</span>
                  <span className="text-white/50">|</span>
                  <span><span className="font-bold">{prop.vacant_rooms}</span> libere</span>
                  <span className="text-white/50">|</span>
                  <span><span className="font-bold">{prop.total_rooms}</span> totali</span>
                </div>
              </div>

              {/* Rooms List */}
              <div className="divide-y" style={{ borderColor: 'rgba(184,134,11,0.08)' }}>
                {prop.rooms.length === 0 ? (
                  <div className="p-6 text-center" style={{ color: '#8B7355' }}>
                    Nessuna stanza in questo immobile. Aggiungi stanze per iniziare.
                  </div>
                ) : prop.rooms.map(room => (
                  <div
                    key={room.id}
                    className="px-6 py-4 flex items-center justify-between hover:bg-rose-50/20 transition-colors"
                    data-testid={`room-row-${room.id}`}
                  >
                    {/* Room Info */}
                    <div className="flex items-center gap-4 min-w-0">
                      <div className="flex items-center gap-2.5 w-28 shrink-0">
                        <DoorOpen size={18} style={{ color: room.status === 'occupied' ? '#059669' : '#94A3B8' }} />
                        <div>
                          <span className="font-semibold text-sm" style={{ color: '#2C1810' }}>Stanza {room.room_number}</span>
                          <p className="text-[11px]" style={{ color: '#8B7355' }}>{room.room_type === 'single' ? 'Singola' : 'Doppia'}</p>
                        </div>
                      </div>

                      {/* Tenant Name or Empty */}
                      <div className="flex-1 min-w-0">
                        {room.status === 'occupied' && room.tenant_name ? (
                          <Link
                            to={`/tenants/${room.tenant_id}`}
                            className="font-medium text-sm hover:underline truncate block"
                            style={{ color: '#9F1239' }}
                            data-testid={`tenant-link-${room.tenant_id}`}
                          >
                            {room.tenant_name}
                          </Link>
                        ) : (
                          <span className="text-sm italic" style={{ color: '#94A3B8' }}>Vuota</span>
                        )}
                      </div>
                    </div>

                    {/* Payment Status */}
                    <div className="flex items-center gap-4 shrink-0">
                      {room.status === 'occupied' && room.tenant_name ? (
                        room.payment_status === 'paid' ? (
                          <div className="flex items-center gap-3">
                            <span
                              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold"
                              style={{ background: '#ECFDF5', color: '#059669' }}
                              data-testid={`payment-badge-${room.id}`}
                            >
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                              Pagato
                            </span>
                            <span className="font-bold text-sm" style={{ color: '#059669' }}>
                              &euro;{room.payment_amount?.toLocaleString()}
                            </span>
                            <span
                              className="px-2 py-0.5 rounded text-[11px] font-medium"
                              style={{ background: 'rgba(184,134,11,0.08)', color: '#8B7355' }}
                            >
                              {room.payment_method}
                            </span>
                          </div>
                        ) : (
                          <span
                            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold"
                            style={{ background: '#FEF2F2', color: '#DC2626' }}
                            data-testid={`payment-badge-${room.id}`}
                          >
                            <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                            Non Pagato
                          </span>
                        )
                      ) : (
                        <span className="text-xs" style={{ color: '#94A3B8' }}>—</span>
                      )}

                      {/* Actions */}
                      <div className="flex items-center gap-1 ml-2">
                        {room.status === 'available' ? (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="rounded-lg hover:bg-green-50 h-8 w-8 p-0"
                            onClick={() => { setSelectedRoom(room); setAssignOpen(true); }}
                            title="Assegna inquilino"
                          >
                            <UserPlus size={15} style={{ color: '#059669' }} />
                          </Button>
                        ) : (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="rounded-lg hover:bg-orange-50 h-8 w-8 p-0"
                            onClick={() => handleUnassign(room.id)}
                            title="Rimuovi inquilino"
                          >
                            <UserMinus size={15} style={{ color: '#D97706' }} />
                          </Button>
                        )}
                        <Button variant="ghost" size="sm" className="rounded-lg hover:bg-amber-50 h-8 w-8 p-0"
                          onClick={() => openEditRoom(room)} title="Modifica stanza">
                          <Edit size={15} style={{ color: '#B8860B' }} />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="rounded-lg hover:bg-red-50 h-8 w-8 p-0"
                          onClick={() => handleDeleteRoom(room.id)}
                          title="Elimina stanza"
                        >
                          <Trash2 size={15} className="text-red-400" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Edit Room Dialog */}
      <Dialog open={editRoomOpen} onOpenChange={setEditRoomOpen}>
        <DialogContent className="luxury-modal">
          <DialogHeader><DialogTitle>Modifica Stanza</DialogTitle></DialogHeader>
          <form onSubmit={handleEditRoom} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Numero Stanza *</Label><Input value={editRoomForm.room_number} onChange={e => setEditRoomForm({ ...editRoomForm, room_number: e.target.value })} required className="luxury-input" /></div>
              <div>
                <Label>Tipo *</Label>
                <Select value={editRoomForm.room_type} onValueChange={v => setEditRoomForm({ ...editRoomForm, room_type: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="single">Singola</SelectItem>
                    <SelectItem value="double">Doppia</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div><Label>Piano</Label><Input value={editRoomForm.floor} onChange={e => setEditRoomForm({ ...editRoomForm, floor: e.target.value })} className="luxury-input" /></div>
              <div><Label>Affitto Mensile</Label><Input type="number" step="0.01" value={editRoomForm.monthly_rent} onChange={e => setEditRoomForm({ ...editRoomForm, monthly_rent: parseFloat(e.target.value) || 0 })} className="luxury-input" /></div>
            </div>
            <div><Label>Descrizione</Label><Input value={editRoomForm.description} onChange={e => setEditRoomForm({ ...editRoomForm, description: e.target.value })} className="luxury-input" /></div>
            <div className="flex justify-end gap-3 pt-2">
              <Button type="button" variant="outline" onClick={() => setEditRoomOpen(false)} className="rounded-xl">Annulla</Button>
              <Button type="submit" className="btn-luxury">Aggiorna</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Rooms;
