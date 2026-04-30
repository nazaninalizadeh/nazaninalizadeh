import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { Plus, Search, Edit, Trash2, Home, DoorOpen, Users, ChevronDown, ChevronUp, Upload, UserPlus, UserMinus, Image as ImageIcon, X, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { Combobox } from '../components/Combobox';
import { PROVINCES } from '../lib/it_dictionaries';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const Properties = () => {
  const [properties, setProperties] = useState([]);
  const [landlords, setLandlords] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showOnlyAvailable, setShowOnlyAvailable] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingProperty, setEditingProperty] = useState(null);
  const [expandedIds, setExpandedIds] = useState(new Set());
  const [propertyDetails, setPropertyDetails] = useState({});
  // Room form
  const [addRoomOpen, setAddRoomOpen] = useState(false);
  const [roomForProperty, setRoomForProperty] = useState(null);
  const [roomForm, setRoomForm] = useState({ room_number: '', room_type: 'single', monthly_rent: 0 });
  // Assign tenant
  const [assignOpen, setAssignOpen] = useState(false);
  const [assignRoom, setAssignRoom] = useState(null);
  const [assignSearch, setAssignSearch] = useState('');
  const [assignTenantId, setAssignTenantId] = useState('');
  // Photo gallery lightbox
  const [gallery, setGallery] = useState(null); // { propertyId, images, index }

  const [formData, setFormData] = useState({
    property_code: '', address: '', property_type: 'Appartamento', number_of_rooms: 1,
    capacity: 1, landlord_id: '', rental_amount: 0, additional_charges: '',
    province: 'PD', phone: '',
  });

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      const [p, l, t] = await Promise.all([
        axios.get(`${API}/properties`, { withCredentials: true }),
        axios.get(`${API}/landlords`, { withCredentials: true }),
        axios.get(`${API}/tenants`, { withCredentials: true }),
      ]);
      setProperties(p.data); setLandlords(l.data); setTenants(t.data);
    } catch { toast.error('Errore'); }
    setLoading(false);
  };

  const toggleExpand = async (propId) => {
    const s = new Set(expandedIds);
    if (s.has(propId)) { s.delete(propId); } else {
      s.add(propId);
      try {
        const { data } = await axios.get(`${API}/properties/${propId}`, { withCredentials: true });
        setPropertyDetails(prev => ({ ...prev, [propId]: data }));
      } catch {}
    }
    setExpandedIds(s);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingProperty) {
        await axios.put(`${API}/properties/${editingProperty.id}`, formData, { withCredentials: true });
      } else {
        await axios.post(`${API}/properties`, formData, { withCredentials: true });
      }
      toast.success(editingProperty ? 'Aggiornato' : 'Creato');
      setDialogOpen(false); resetForm(); fetchAll();
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore'); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Eliminare?')) return;
    try { await axios.delete(`${API}/properties/${id}`, { withCredentials: true }); toast.success('Eliminato'); fetchAll(); } catch { toast.error('Errore'); }
  };

  const resetForm = () => { setFormData({ property_code: '', address: '', property_type: 'Appartamento', number_of_rooms: 1, capacity: 1, landlord_id: '', rental_amount: 0, additional_charges: '', province: 'PD', phone: '' }); setEditingProperty(null); };

  const openEdit = (p) => {
    setEditingProperty(p);
    setFormData({ property_code: p.property_code, address: p.address, property_type: p.property_type || 'Appartamento', number_of_rooms: p.number_of_rooms, capacity: p.capacity, landlord_id: p.landlord_id, rental_amount: p.rental_amount, additional_charges: p.additional_charges || '', province: p.province || 'PD', phone: p.phone || '' });
    setDialogOpen(true);
  };

  // Room operations
  const handleAddRoom = async (e) => {
    e.preventDefault();
    try {
      // Auto-derive per-person rent for double rooms (UI hint only — backend stores total)
      await axios.post(`${API}/rooms`, { ...roomForm, property_id: roomForProperty }, { withCredentials: true });
      toast.success('Stanza aggiunta');
      setAddRoomOpen(false); setRoomForm({ room_number: '', room_type: 'single', monthly_rent: 0 });
      const { data } = await axios.get(`${API}/properties/${roomForProperty}`, { withCredentials: true });
      setPropertyDetails(prev => ({ ...prev, [roomForProperty]: data }));
      fetchAll();
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore'); }
  };

  const handleDeleteRoom = async (roomId, propId) => {
    if (!window.confirm('Eliminare stanza?')) return;
    try {
      await axios.delete(`${API}/rooms/${roomId}`, { withCredentials: true });
      toast.success('Stanza eliminata');
      const { data } = await axios.get(`${API}/properties/${propId}`, { withCredentials: true });
      setPropertyDetails(prev => ({ ...prev, [propId]: data }));
      fetchAll();
    } catch { toast.error('Errore'); }
  };

  const handleAssign = async () => {
    if (!assignTenantId || !assignRoom) return;
    try {
      const fd = new FormData(); fd.append('tenant_id', assignTenantId);
      await axios.post(`${API}/rooms/${assignRoom.id}/assign`, fd, { withCredentials: true });
      toast.success('Inquilino assegnato');
      setAssignOpen(false); setAssignTenantId(''); setAssignSearch('');
      const { data } = await axios.get(`${API}/properties/${assignRoom.property_id}`, { withCredentials: true });
      setPropertyDetails(prev => ({ ...prev, [assignRoom.property_id]: data }));
      fetchAll();
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore'); }
  };

  const handleUnassign = async (roomId, propId) => {
    try {
      await axios.post(`${API}/rooms/${roomId}/unassign`, {}, { withCredentials: true });
      toast.success('Inquilino rimosso');
      const { data } = await axios.get(`${API}/properties/${propId}`, { withCredentials: true });
      setPropertyDetails(prev => ({ ...prev, [propId]: data }));
      fetchAll();
    } catch { toast.error('Errore'); }
  };

  const handleImageUpload = async (e, type, id, propId) => {
    const file = e.target.files[0];
    if (!file) return;
    // Client-side validation (server enforces too)
    const allowed = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!allowed.includes(file.type)) {
      toast.error('Formato non supportato. Usa JPG, PNG o WEBP.');
      e.target.value = '';
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      toast.error('File troppo grande. Massimo 5MB.');
      e.target.value = '';
      return;
    }
    const fd = new FormData(); fd.append('file', file);
    try {
      await axios.post(`${API}/${type}/${id}/images`, fd, { withCredentials: true });
      toast.success('Immagine caricata');
      const { data } = await axios.get(`${API}/properties/${propId}`, { withCredentials: true });
      setPropertyDetails(prev => ({ ...prev, [propId]: data }));
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore upload');
    }
  };

  const openGallery = (propId, images, index = 0) => {
    if (!images?.length) return;
    setGallery({ propertyId: propId, images, index });
  };
  const closeGallery = () => setGallery(null);
  const nextPhoto = () => setGallery(g => g ? { ...g, index: (g.index + 1) % g.images.length } : g);
  const prevPhoto = () => setGallery(g => g ? { ...g, index: (g.index - 1 + g.images.length) % g.images.length } : g);
  const deleteCurrentPhoto = async () => {
    if (!gallery) return;
    const url = gallery.images[gallery.index];
    if (!window.confirm('Eliminare questa foto?')) return;
    try {
      await axios.delete(`${API}/properties/${gallery.propertyId}/images`, { params: { url }, withCredentials: true });
      toast.success('Foto eliminata');
      const { data } = await axios.get(`${API}/properties/${gallery.propertyId}`, { withCredentials: true });
      setPropertyDetails(prev => ({ ...prev, [gallery.propertyId]: data }));
      const remaining = data.images || [];
      if (remaining.length === 0) { setGallery(null); }
      else { setGallery(g => ({ propertyId: g.propertyId, images: remaining, index: Math.min(g.index, remaining.length - 1) })); }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore eliminazione');
    }
  };

  const filtered = properties.filter(p =>
    (p.address?.toLowerCase().includes(searchTerm.toLowerCase()) ||
     p.property_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
     p.landlord_name?.toLowerCase().includes(searchTerm.toLowerCase()))
    && (!showOnlyAvailable || (p.vacant_rooms_count || 0) > 0)
  );

  // Build a flat list of empty rooms across all properties for the "Stanze Libere" view
  const emptyRooms = (() => {
    const list = [];
    Object.values(propertyDetails).forEach(p => {
      (p.rooms || []).forEach(r => {
        if (!r.tenant_id && !r.tenant_name) {
          list.push({ ...r, property_address: p.address, property_code: p.property_code, property_id: p.id });
        }
      });
    });
    return list;
  })();

  if (loading) return <div className="flex items-center justify-center p-12"><div className="luxury-spinner h-10 w-10" /></div>;

  return (
    <div data-testid="properties-page" className="luxury-fade-in">
      <div className="mb-8 flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="luxury-title mb-2">Immobili</h1>
          <p className="luxury-subtitle">Gestisci immobili, stanze e inquilini</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(o) => { setDialogOpen(o); if (!o) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="btn-luxury" data-testid="add-property-button"><Plus size={18} className="mr-2" />Aggiungi Immobile</Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto luxury-modal w-[95vw] sm:w-auto" style={{ background: '#FFFBF5' }}>
            <DialogHeader><DialogTitle>{editingProperty ? 'Modifica' : 'Nuovo'} Immobile</DialogTitle></DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {editingProperty && <div><Label>Codice</Label><Input value={formData.property_code} disabled className="luxury-input bg-gray-50" /></div>}
                <div>
                  <Label>Tipo *</Label>
                  <Select value={formData.property_type} onValueChange={v => setFormData({ ...formData, property_type: v })}>
                    <SelectTrigger data-testid="property-type-select"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Appartamento">Appartamento</SelectItem>
                      <SelectItem value="Studio">Studio</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                {!editingProperty && <div />}
                <div className="col-span-2"><Label>Indirizzo *</Label><Input value={formData.address} onChange={e => setFormData({ ...formData, address: e.target.value })} required className="luxury-input" /></div>
                <div>
                  <Label>Provincia</Label>
                  <Combobox options={PROVINCES} value={formData.province} onChange={v => setFormData({ ...formData, province: v })} placeholder="PD - Padova" dataTestid="property-province" />
                </div>
                <div><Label>Telefono</Label><Input value={formData.phone} onChange={e => setFormData({ ...formData, phone: e.target.value })} className="luxury-input" placeholder="+39 333 1234567" data-testid="property-phone" /></div>
                <div>
                  <Label>Proprietario *</Label>
                  <Select value={formData.landlord_id} onValueChange={v => setFormData({ ...formData, landlord_id: v })}>
                    <SelectTrigger><SelectValue placeholder="Seleziona" /></SelectTrigger>
                    <SelectContent>{landlords.map(l => <SelectItem key={l.id} value={l.id}>{l.full_name}</SelectItem>)}</SelectContent>
                  </Select>
                </div>
                <div><Label>N. Stanze</Label><Input type="number" min="1" value={formData.number_of_rooms} onChange={e => setFormData({ ...formData, number_of_rooms: parseInt(e.target.value) || 1 })} className="luxury-input" /></div>
                <div><Label>Capacita</Label><Input type="number" min="1" value={formData.capacity} onChange={e => setFormData({ ...formData, capacity: parseInt(e.target.value) || 1 })} className="luxury-input" /></div>
                <div><Label>Affitto Mensile</Label><Input type="number" step="0.01" value={formData.rental_amount} onChange={e => setFormData({ ...formData, rental_amount: parseFloat(e.target.value) || 0 })} className="luxury-input" /></div>
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="rounded-xl">Annulla</Button>
                <Button type="submit" className="btn-luxury">{editingProperty ? 'Aggiorna' : 'Crea'}</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Search */}
      <div className="luxury-card p-4 mb-6 flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[260px]">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2" size={18} style={{ color: '#B8860B' }} />
          <Input placeholder="Cerca per indirizzo, codice o proprietario..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="pl-11 luxury-input" />
        </div>
        <button type="button" onClick={() => setShowOnlyAvailable(v => !v)}
          className="px-3 py-2 rounded-full text-xs font-medium transition-all whitespace-nowrap"
          style={{ background: showOnlyAvailable ? '#9F1239' : 'rgba(184,134,11,0.08)', color: showOnlyAvailable ? 'white' : '#8B7355' }}
          data-testid="filter-available-rooms">
          {showOnlyAvailable ? '✓ ' : ''}Solo immobili con stanze libere ({properties.reduce((s, p) => s + (p.vacant_rooms_count || 0), 0)})
        </button>
      </div>

      {/* Property Cards */}
      {filtered.length === 0 ? (
        <div className="luxury-card p-14 text-center"><Home className="mx-auto mb-4" size={48} style={{ color: 'rgba(184,134,11,0.3)' }} /><p style={{ color: '#8B7355' }}>Nessun immobile</p></div>
      ) : (
        <div className="space-y-4">
          {filtered.map(property => {
            const isExp = expandedIds.has(property.id);
            const detail = propertyDetails[property.id];
            return (
              <div key={property.id} className="luxury-card overflow-hidden" data-testid={`property-card-${property.id}`}>
                <div className="px-6 py-4 flex items-center justify-between cursor-pointer hover:bg-rose-50/20 transition-colors" onClick={() => toggleExpand(property.id)}>
                  <div className="flex items-center gap-4">
                    <div className="p-2.5 rounded-xl" style={{ background: 'linear-gradient(135deg, #9F1239, #BE123C)' }}><Home size={20} className="text-white" /></div>
                    <div>
                      <h3 className="font-semibold text-lg" style={{ color: '#2C1810' }}>{property.address}</h3>
                      <p className="text-sm" style={{ color: '#8B7355' }}>{property.property_code} | {property.landlord_name} | {property.property_type}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="flex gap-5 text-sm">
                      <div className="text-center"><p className="text-[10px] uppercase" style={{ color: '#8B7355' }}>Stanze</p><p className="font-bold">{property.total_rooms_count || 0}</p></div>
                      <div className="text-center"><p className="text-[10px] uppercase" style={{ color: '#8B7355' }}>Singole</p><p className="font-bold" style={{ color: '#2563EB' }}>{property.single_rooms_count || 0}</p></div>
                      <div className="text-center"><p className="text-[10px] uppercase" style={{ color: '#8B7355' }}>Doppie</p><p className="font-bold" style={{ color: '#7C3AED' }}>{property.double_rooms_count || 0}</p></div>
                      <div className="text-center"><p className="text-[10px] uppercase" style={{ color: '#8B7355' }}>Occupate</p><p className="font-bold" style={{ color: '#059669' }}>{property.occupied_rooms_count || 0}</p></div>
                      <div className="text-center"><p className="text-[10px] uppercase" style={{ color: '#8B7355' }}>Libere</p><p className="font-bold" style={{ color: '#DC2626' }}>{property.vacant_rooms_count || 0}</p></div>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button variant="ghost" size="sm" className="rounded-lg hover:bg-amber-50" onClick={(e) => { e.stopPropagation(); openEdit(property); }} data-testid={`edit-property-${property.id}`}><Edit size={16} style={{ color: '#B8860B' }} /></Button>
                      <Button variant="ghost" size="sm" className="rounded-lg hover:bg-red-50" onClick={(e) => { e.stopPropagation(); handleDelete(property.id); }} data-testid={`delete-property-${property.id}`}><Trash2 size={16} className="text-red-500" /></Button>
                      <button data-testid={`expand-property-${property.id}`} aria-label={isExp ? 'Comprimi' : 'Espandi'} className="p-1 rounded-lg hover:bg-rose-50/40" onClick={(e) => { e.stopPropagation(); toggleExpand(property.id); }}>
                        {isExp ? <ChevronUp size={18} style={{ color: '#8B7355' }} /> : <ChevronDown size={18} style={{ color: '#8B7355' }} />}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Expanded: Rooms */}
                {isExp && (
                  <div style={{ borderTop: '1px solid rgba(184,134,11,0.1)' }}>
                    {/* Property images */}
                    {detail?.images?.length > 0 && (
                      <div className="px-6 py-3 flex gap-2 overflow-x-auto" style={{ background: 'rgba(184,134,11,0.02)' }} data-testid={`property-gallery-${property.id}`}>
                        {detail.images.map((img, i) => (
                          <button
                            key={i}
                            type="button"
                            onClick={() => openGallery(property.id, detail.images, i)}
                            className="relative group shrink-0 rounded-lg overflow-hidden hover:ring-2 hover:ring-amber-500 transition-all"
                            data-testid={`property-photo-thumb-${property.id}-${i}`}
                            title="Clicca per aprire la galleria"
                          >
                            <img src={`${process.env.REACT_APP_BACKEND_URL}${img}`} alt="" className="h-16 w-24 object-cover" />
                            {i === 0 && detail.images.length > 1 && (
                              <span className="absolute bottom-1 right-1 text-[10px] px-1.5 py-0.5 rounded-full text-white font-semibold" style={{ background: 'rgba(0,0,0,0.6)' }}>
                                +{detail.images.length - 1}
                              </span>
                            )}
                          </button>
                        ))}
                      </div>
                    )}
                    {/* Actions bar */}
                    <div className="px-6 py-3 flex items-center gap-2" style={{ borderBottom: '1px solid rgba(184,134,11,0.08)' }}>
                      <Button size="sm" className="btn-luxury text-xs" onClick={() => { setRoomForProperty(property.id); setAddRoomOpen(true); }} data-testid={`add-room-${property.id}`}>
                        <Plus size={14} className="mr-1" /> Aggiungi Stanza
                      </Button>
                      <label className="cursor-pointer">
                        <input type="file" className="hidden" accept="image/jpeg,image/jpg,image/png,image/webp" onChange={e => handleImageUpload(e, 'properties', property.id, property.id)} data-testid={`upload-property-image-${property.id}`} />
                        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium" style={{ background: 'rgba(184,134,11,0.08)', color: '#8B7355' }}>
                          <ImageIcon size={13} /> Aggiungi Foto
                        </span>
                      </label>
                    </div>

                    {/* Room list */}
                    {!detail ? (
                      <div className="p-6 text-center"><div className="luxury-spinner h-6 w-6 mx-auto" /></div>
                    ) : detail.rooms?.length === 0 ? (
                      <div className="p-6 text-center" style={{ color: '#8B7355' }}>Nessuna stanza. Clicca "Aggiungi Stanza" sopra.</div>
                    ) : (
                      <div className="divide-y" style={{ borderColor: 'rgba(184,134,11,0.06)' }}>
                        {detail.rooms.map(room => (
                          <div key={room.id} className="px-6 py-3 flex items-center justify-between" data-testid={`room-${room.id}`}>
                            <div className="flex items-center gap-3">
                              <DoorOpen size={16} style={{ color: room.status === 'occupied' ? '#059669' : '#94A3B8' }} />
                              <div>
                                <span className="font-semibold text-sm" style={{ color: '#2C1810' }}>Stanza {room.room_number}</span>
                                <span className="text-xs ml-2" style={{ color: '#8B7355' }}>({room.room_type === 'single' ? 'Singola' : 'Doppia'})</span>
                                {room.monthly_rent > 0 && (
                                  <span className="text-xs ml-2" style={{ color: '#059669' }}>
                                    &euro;{room.monthly_rent}
                                    {room.room_type === 'double' && (
                                      <span className="ml-1" style={{ color: '#7C3AED' }}>(&euro;{(room.monthly_rent / 2).toFixed(0)} a persona)</span>
                                    )}
                                  </span>
                                )}
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              {room.tenant_name ? (
                                <>
                                  <Link to={`/tenants/${room.tenant_id || ''}`} className="px-2 py-1 rounded-full text-xs font-medium hover:underline" style={{ background: '#ECFDF5', color: '#059669' }} data-testid={`tenant-link-${room.id}`}>
                                    <Users size={12} className="inline mr-1" />{room.tenant_name}
                                  </Link>
                                  <Button variant="ghost" size="sm" className="h-7 w-7 p-0 rounded-lg hover:bg-red-50" onClick={() => handleUnassign(room.id, property.id)} title="Rimuovi inquilino" data-testid={`unassign-room-${room.id}`}>
                                    <UserMinus size={14} className="text-red-400" />
                                  </Button>
                                </>
                              ) : (
                                <Button variant="ghost" size="sm" className="rounded-lg hover:bg-emerald-50 text-xs gap-1" onClick={() => { setAssignRoom(room); setAssignOpen(true); }} data-testid={`assign-room-${room.id}`}>
                                  <UserPlus size={14} style={{ color: '#059669' }} /> Assegna
                                </Button>
                              )}
                              <label className="cursor-pointer">
                                <input type="file" className="hidden" accept="image/jpeg,image/jpg,image/png,image/webp" onChange={e => handleImageUpload(e, 'rooms', room.id, property.id)} data-testid={`upload-room-image-${room.id}`} />
                                <span className="inline-flex items-center justify-center h-7 w-7 rounded-lg hover:bg-amber-50"><ImageIcon size={13} style={{ color: '#B8860B' }} /></span>
                              </label>
                              <Button variant="ghost" size="sm" className="h-7 w-7 p-0 rounded-lg hover:bg-red-50" onClick={() => handleDeleteRoom(room.id, property.id)} data-testid={`delete-room-${room.id}`}>
                                <Trash2 size={13} className="text-red-400" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Add Room Dialog */}
      <Dialog open={addRoomOpen} onOpenChange={setAddRoomOpen}>
        <DialogContent className="luxury-modal" style={{ background: '#FFFBF5' }}>
          <DialogHeader><DialogTitle>Nuova Stanza</DialogTitle></DialogHeader>
          <form onSubmit={handleAddRoom} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Numero Stanza *</Label><Input value={roomForm.room_number} onChange={e => setRoomForm({ ...roomForm, room_number: e.target.value })} required className="luxury-input" /></div>
              <div>
                <Label>Tipo</Label>
                <Select value={roomForm.room_type} onValueChange={v => setRoomForm({ ...roomForm, room_type: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="single">Singola</SelectItem><SelectItem value="double">Doppia</SelectItem></SelectContent>
                </Select>
              </div>
              <div className="col-span-2">
                <Label>Affitto Totale (€)</Label>
                <Input type="number" step="0.01" value={roomForm.monthly_rent} onChange={e => setRoomForm({ ...roomForm, monthly_rent: parseFloat(e.target.value) || 0 })} className="luxury-input" />
                {roomForm.room_type === 'double' && roomForm.monthly_rent > 0 && (
                  <p className="text-xs mt-1" style={{ color: '#7C3AED' }}>
                    Stanza doppia: &euro;{(roomForm.monthly_rent / 2).toFixed(0)} a persona
                  </p>
                )}
              </div>
            </div>
            <div className="flex justify-end gap-3"><Button type="button" variant="outline" onClick={() => setAddRoomOpen(false)} className="rounded-xl">Annulla</Button><Button type="submit" className="btn-luxury">Crea</Button></div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Assign Tenant Dialog */}
      <Dialog open={assignOpen} onOpenChange={setAssignOpen}>
        <DialogContent className="luxury-modal" style={{ background: '#FFFBF5' }}>
          <DialogHeader><DialogTitle>Assegna Inquilino a Stanza {assignRoom?.room_number}</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <Input placeholder="Cerca inquilino per nome..." value={assignSearch} onChange={e => setAssignSearch(e.target.value)} className="luxury-input" autoFocus data-testid="assign-tenant-search" />
            <div className="max-h-60 overflow-y-auto space-y-1 rounded-xl p-2" style={{ background: 'white', border: '1px solid rgba(184,134,11,0.15)' }} data-testid="assign-tenant-list">
              {tenants.filter(t => !assignSearch || t.full_name?.toLowerCase().includes(assignSearch.toLowerCase())).length === 0 && (
                <p className="text-xs text-center py-4" style={{ color: '#8B7355' }}>Nessun inquilino trovato. Crea un inquilino prima.</p>
              )}
              {tenants
                .filter(t => !assignSearch || t.full_name?.toLowerCase().includes(assignSearch.toLowerCase()))
                .sort((a, b) => (a.room_id ? 1 : 0) - (b.room_id ? 1 : 0))
                .map(t => (
                <button key={t.id} type="button" onClick={() => setAssignTenantId(t.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all flex items-center justify-between gap-2 ${assignTenantId === t.id ? 'font-bold' : ''}`}
                  style={{ background: assignTenantId === t.id ? 'rgba(159,18,57,0.08)' : 'transparent', color: assignTenantId === t.id ? '#9F1239' : '#4A3B31' }}
                  data-testid={`assign-tenant-option-${t.id}`}>
                  <span>{t.full_name} {t.nationality ? <span className="text-xs" style={{ color: '#8B7355' }}>({t.nationality})</span> : null}</span>
                  {t.room_id && <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: 'rgba(217,119,6,0.12)', color: '#D97706' }}>Già assegnato</span>}
                </button>
              ))}
            </div>
            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => setAssignOpen(false)} className="rounded-xl">Annulla</Button>
              <Button onClick={handleAssign} className="btn-luxury" disabled={!assignTenantId} data-testid="assign-tenant-confirm">Assegna</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Photo Gallery Lightbox */}
      {gallery && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center"
          style={{ background: 'rgba(12,10,9,0.92)' }}
          onClick={closeGallery}
          data-testid="property-gallery-lightbox"
        >
          {/* Close */}
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); closeGallery(); }}
            className="absolute top-5 right-5 h-10 w-10 flex items-center justify-center rounded-full text-white hover:bg-white/10 transition"
            data-testid="gallery-close"
            aria-label="Chiudi"
          >
            <X size={22} />
          </button>

          {/* Counter */}
          <div className="absolute top-6 left-6 text-white/80 text-sm font-medium" data-testid="gallery-counter">
            {gallery.index + 1} / {gallery.images.length}
          </div>

          {/* Delete */}
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); deleteCurrentPhoto(); }}
            className="absolute top-5 right-20 h-10 px-3 flex items-center gap-1.5 rounded-full text-white text-xs font-medium hover:bg-red-500/90 transition"
            style={{ background: 'rgba(220,38,38,0.7)' }}
            data-testid="gallery-delete"
          >
            <Trash2 size={14} /> Elimina
          </button>

          {/* Prev */}
          {gallery.images.length > 1 && (
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); prevPhoto(); }}
              className="absolute left-5 md:left-10 h-12 w-12 flex items-center justify-center rounded-full text-white hover:bg-white/15 transition"
              data-testid="gallery-prev"
              aria-label="Precedente"
            >
              <ChevronLeft size={28} />
            </button>
          )}

          {/* Image */}
          <img
            src={`${process.env.REACT_APP_BACKEND_URL}${gallery.images[gallery.index]}`}
            alt=""
            className="max-h-[88vh] max-w-[88vw] object-contain rounded-lg shadow-2xl"
            onClick={(e) => e.stopPropagation()}
            data-testid="gallery-main-image"
          />

          {/* Next */}
          {gallery.images.length > 1 && (
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); nextPhoto(); }}
              className="absolute right-5 md:right-10 h-12 w-12 flex items-center justify-center rounded-full text-white hover:bg-white/15 transition"
              data-testid="gallery-next"
              aria-label="Successiva"
            >
              <ChevronRight size={28} />
            </button>
          )}

          {/* Thumbnail strip */}
          {gallery.images.length > 1 && (
            <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex gap-2 px-3 py-2 rounded-xl max-w-[92vw] overflow-x-auto" style={{ background: 'rgba(0,0,0,0.5)' }}>
              {gallery.images.map((img, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={(e) => { e.stopPropagation(); setGallery(g => ({ ...g, index: i })); }}
                  className={`shrink-0 rounded-md overflow-hidden transition ${i === gallery.index ? 'ring-2 ring-amber-400' : 'opacity-60 hover:opacity-100'}`}
                  data-testid={`gallery-thumb-${i}`}
                >
                  <img src={`${process.env.REACT_APP_BACKEND_URL}${img}`} alt="" className="h-12 w-16 object-cover" />
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Properties;
