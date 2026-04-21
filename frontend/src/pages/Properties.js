import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { Plus, Search, Edit, Trash2, Home, DoorOpen, Users, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Properties = () => {
  const [properties, setProperties] = useState([]);
  const [landlords, setLandlords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingProperty, setEditingProperty] = useState(null);
  const [expandedIds, setExpandedIds] = useState(new Set());
  const [propertyDetails, setPropertyDetails] = useState({});
  const [formData, setFormData] = useState({
    property_code: '', address: '', property_type: '', number_of_rooms: 1,
    capacity: 1, landlord_id: '', rental_amount: 0, deposit_amount: 0, additional_charges: '',
  });

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const [p, l] = await Promise.all([
        axios.get(`${API_URL}/properties`, { withCredentials: true }),
        axios.get(`${API_URL}/landlords`, { withCredentials: true }),
      ]);
      setProperties(p.data);
      setLandlords(l.data);
    } catch { toast.error('Errore nel caricamento'); }
    setLoading(false);
  };

  const toggleExpand = async (propId) => {
    const newSet = new Set(expandedIds);
    if (newSet.has(propId)) {
      newSet.delete(propId);
    } else {
      newSet.add(propId);
      if (!propertyDetails[propId]) {
        try {
          const { data } = await axios.get(`${API_URL}/properties/${propId}`, { withCredentials: true });
          setPropertyDetails(prev => ({ ...prev, [propId]: data }));
        } catch { toast.error('Errore nel caricamento dettagli'); }
      }
    }
    setExpandedIds(newSet);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingProperty) {
        await axios.put(`${API_URL}/properties/${editingProperty.id}`, formData, { withCredentials: true });
        toast.success('Immobile aggiornato');
      } else {
        await axios.post(`${API_URL}/properties`, formData, { withCredentials: true });
        toast.success('Immobile creato');
      }
      setDialogOpen(false);
      resetForm();
      fetchData();
    } catch { toast.error('Errore nel salvataggio'); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Eliminare questo immobile?')) return;
    try {
      await axios.delete(`${API_URL}/properties/${id}`, { withCredentials: true });
      toast.success('Immobile eliminato');
      fetchData();
    } catch { toast.error('Errore'); }
  };

  const resetForm = () => {
    setFormData({ property_code: '', address: '', property_type: '', number_of_rooms: 1, capacity: 1, landlord_id: '', rental_amount: 0, deposit_amount: 0, additional_charges: '' });
    setEditingProperty(null);
  };

  const openEditDialog = (property) => {
    setEditingProperty(property);
    setFormData({
      property_code: property.property_code, address: property.address,
      property_type: property.property_type, number_of_rooms: property.number_of_rooms,
      capacity: property.capacity, landlord_id: property.landlord_id,
      rental_amount: property.rental_amount, deposit_amount: property.deposit_amount,
      additional_charges: property.additional_charges || '',
    });
    setDialogOpen(true);
  };

  const filteredProperties = properties.filter(p =>
    p.property_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.address?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.landlord_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) return <div className="flex items-center justify-center p-12"><div className="luxury-spinner h-10 w-10" /></div>;

  return (
    <div data-testid="properties-page" className="luxury-fade-in">
      <div className="mb-8 flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="luxury-title mb-2" data-testid="properties-title">Immobili</h1>
          <p className="luxury-subtitle">Gestisci immobili, stanze e inquilini assegnati</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="btn-luxury" data-testid="add-property-button"><Plus size={18} className="mr-2" />Aggiungi Immobile</Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl luxury-modal">
            <DialogHeader><DialogTitle>{editingProperty ? 'Modifica Immobile' : 'Nuovo Immobile'}</DialogTitle></DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div><Label>Codice *</Label><Input value={formData.property_code} onChange={e => setFormData({ ...formData, property_code: e.target.value })} required className="luxury-input" /></div>
                <div><Label>Tipo *</Label><Input value={formData.property_type} onChange={e => setFormData({ ...formData, property_type: e.target.value })} placeholder="Appartamento, Casa..." required className="luxury-input" /></div>
                <div className="col-span-2"><Label>Indirizzo *</Label><Input value={formData.address} onChange={e => setFormData({ ...formData, address: e.target.value })} required className="luxury-input" /></div>
                <div>
                  <Label>Proprietario *</Label>
                  <Select value={formData.landlord_id} onValueChange={v => setFormData({ ...formData, landlord_id: v })}>
                    <SelectTrigger><SelectValue placeholder="Seleziona proprietario" /></SelectTrigger>
                    <SelectContent>{landlords.map(l => <SelectItem key={l.id} value={l.id}>{l.full_name}</SelectItem>)}</SelectContent>
                  </Select>
                </div>
                <div><Label>N. Stanze *</Label><Input type="number" min="1" value={formData.number_of_rooms} onChange={e => setFormData({ ...formData, number_of_rooms: parseInt(e.target.value) })} required className="luxury-input" /></div>
                <div><Label>Capacita *</Label><Input type="number" min="1" value={formData.capacity} onChange={e => setFormData({ ...formData, capacity: parseInt(e.target.value) })} required className="luxury-input" /></div>
                <div><Label>Affitto Mensile *</Label><Input type="number" step="0.01" value={formData.rental_amount} onChange={e => setFormData({ ...formData, rental_amount: parseFloat(e.target.value) })} required className="luxury-input" /></div>
                <div><Label>Deposito *</Label><Input type="number" step="0.01" value={formData.deposit_amount} onChange={e => setFormData({ ...formData, deposit_amount: parseFloat(e.target.value) })} required className="luxury-input" /></div>
              </div>
              <div><Label>Costi Aggiuntivi</Label><Input value={formData.additional_charges} onChange={e => setFormData({ ...formData, additional_charges: e.target.value })} className="luxury-input" placeholder="Utenze, manutenzione..." /></div>
              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="rounded-xl">Annulla</Button>
                <Button type="submit" className="btn-luxury">{editingProperty ? 'Aggiorna' : 'Crea'}</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Search */}
      <div className="luxury-card p-4 mb-6">
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2" size={18} style={{ color: '#B8860B' }} />
          <Input placeholder="Cerca per codice, indirizzo o proprietario..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="pl-11 luxury-input" />
        </div>
      </div>

      {/* Property Cards */}
      {filteredProperties.length === 0 ? (
        <div className="luxury-card p-14 text-center">
          <Home className="mx-auto mb-4" size={48} style={{ color: 'rgba(184,134,11,0.3)' }} />
          <p style={{ color: '#8B7355' }}>Nessun immobile trovato</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredProperties.map(property => {
            const isExpanded = expandedIds.has(property.id);
            const detail = propertyDetails[property.id];
            return (
              <div key={property.id} className="luxury-card overflow-hidden" data-testid={`property-card-${property.id}`}>
                {/* Property Header */}
                <div
                  className="px-6 py-4 flex items-center justify-between cursor-pointer hover:bg-rose-50/20 transition-colors"
                  onClick={() => toggleExpand(property.id)}
                >
                  <div className="flex items-center gap-4">
                    <div className="p-2.5 rounded-xl" style={{ background: 'linear-gradient(135deg, #9F1239 0%, #BE123C 100%)' }}>
                      <Home size={20} className="text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-lg" style={{ color: '#2C1810' }}>{property.address}</h3>
                      <p className="text-sm" style={{ color: '#8B7355' }}>
                        Codice: {property.property_code} | Proprietario: {property.landlord_name} | {property.property_type}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-6 text-sm" style={{ color: '#4A3B31' }}>
                      <div className="text-center">
                        <p className="text-xs uppercase" style={{ color: '#8B7355' }}>Stanze</p>
                        <p className="font-bold">{property.total_rooms_count || 0}</p>
                      </div>
                      <div className="text-center">
                        <p className="text-xs uppercase" style={{ color: '#8B7355' }}>Occupate</p>
                        <p className="font-bold" style={{ color: '#059669' }}>{property.occupied_rooms_count || 0}</p>
                      </div>
                      <div className="text-center">
                        <p className="text-xs uppercase" style={{ color: '#8B7355' }}>Libere</p>
                        <p className="font-bold" style={{ color: '#DC2626' }}>{property.vacant_rooms_count || 0}</p>
                      </div>
                      <div className="text-center">
                        <p className="text-xs uppercase" style={{ color: '#8B7355' }}>Affitto</p>
                        <p className="font-bold">&euro;{property.rental_amount?.toFixed(0)}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="sm" className="rounded-lg hover:bg-amber-50" onClick={(e) => { e.stopPropagation(); openEditDialog(property); }}>
                        <Edit size={16} style={{ color: '#B8860B' }} />
                      </Button>
                      <Button variant="ghost" size="sm" className="rounded-lg hover:bg-red-50" onClick={(e) => { e.stopPropagation(); handleDelete(property.id); }}>
                        <Trash2 size={16} className="text-red-500" />
                      </Button>
                      {isExpanded ? <ChevronUp size={18} style={{ color: '#8B7355' }} /> : <ChevronDown size={18} style={{ color: '#8B7355' }} />}
                    </div>
                  </div>
                </div>

                {/* Expanded Detail: Rooms + Tenants */}
                {isExpanded && (
                  <div style={{ borderTop: '1px solid rgba(184,134,11,0.1)' }}>
                    {!detail ? (
                      <div className="p-6 text-center"><div className="luxury-spinner h-8 w-8 mx-auto" /></div>
                    ) : detail.rooms?.length === 0 ? (
                      <div className="p-6 text-center" style={{ color: '#8B7355' }}>
                        Nessuna stanza creata per questo immobile. Vai a <Link to="/rooms" className="underline" style={{ color: '#9F1239' }}>Stanze</Link> per aggiungerne.
                      </div>
                    ) : (
                      <div className="divide-y" style={{ borderColor: 'rgba(184,134,11,0.08)' }}>
                        {detail.rooms.map(room => (
                          <div key={room.id} className="px-6 py-3 flex items-center justify-between" data-testid={`property-room-${room.id}`}>
                            <div className="flex items-center gap-3">
                              <DoorOpen size={16} style={{ color: room.status === 'occupied' ? '#059669' : '#94A3B8' }} />
                              <div>
                                <span className="font-semibold text-sm" style={{ color: '#2C1810' }}>
                                  Stanza {room.room_number}
                                </span>
                                <span className="text-xs ml-2" style={{ color: '#8B7355' }}>
                                  ({room.room_type === 'single' ? 'Singola' : 'Doppia'})
                                </span>
                              </div>
                            </div>
                            <div className="flex items-center gap-3">
                              {room.tenant_name ? (
                                <Link to={`/tenants/${room.tenant_id || ''}`} className="flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium hover:underline" style={{ background: '#ECFDF5', color: '#059669' }}>
                                  <Users size={14} />
                                  {room.tenant_name}
                                </Link>
                              ) : (
                                <span className="px-3 py-1 rounded-full text-xs" style={{ background: '#f1f5f9', color: '#94A3B8' }}>
                                  Vuota
                                </span>
                              )}
                            </div>
                          </div>
                        ))}
                        {/* Tenants summary */}
                        {detail.tenants?.length > 0 && (
                          <div className="px-6 py-3" style={{ background: 'rgba(184,134,11,0.03)' }}>
                            <p className="text-xs font-semibold uppercase" style={{ color: '#8B7355' }}>
                              Totale inquilini: {detail.tenants.length}
                            </p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default Properties;
