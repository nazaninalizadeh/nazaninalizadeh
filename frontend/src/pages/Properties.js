import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Plus, Search, Edit, Trash2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { Label } from '../components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Properties = () => {
  const [properties, setProperties] = useState([]);
  const [landlords, setLandlords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingProperty, setEditingProperty] = useState(null);
  const [formData, setFormData] = useState({
    property_code: '',
    address: '',
    property_type: '',
    number_of_rooms: 1,
    capacity: 1,
    landlord_id: '',
    rental_amount: 0,
    deposit_amount: 0,
    additional_charges: '',
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [propertiesRes, landlordsRes] = await Promise.all([
        axios.get(`${API_URL}/properties`, { withCredentials: true }),
        axios.get(`${API_URL}/landlords`, { withCredentials: true }),
      ]);
      setProperties(propertiesRes.data);
      setLandlords(landlordsRes.data);
    } catch (error) {
      toast.error('Failed to load properties');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingProperty) {
        await axios.put(`${API_URL}/properties/${editingProperty.id}`, formData, {
          withCredentials: true,
        });
        toast.success('Property updated successfully');
      } else {
        await axios.post(`${API_URL}/properties`, formData, {
          withCredentials: true,
        });
        toast.success('Property created successfully');
      }
      setDialogOpen(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error('Failed to save property');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this property?')) return;
    try {
      await axios.delete(`${API_URL}/properties/${id}`, {
        withCredentials: true,
      });
      toast.success('Property deleted successfully');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete property');
    }
  };

  const resetForm = () => {
    setFormData({
      property_code: '',
      address: '',
      property_type: '',
      number_of_rooms: 1,
      capacity: 1,
      landlord_id: '',
      rental_amount: 0,
      deposit_amount: 0,
      additional_charges: '',
    });
    setEditingProperty(null);
  };

  const openEditDialog = (property) => {
    setEditingProperty(property);
    setFormData({
      property_code: property.property_code,
      address: property.address,
      property_type: property.property_type,
      number_of_rooms: property.number_of_rooms,
      capacity: property.capacity,
      landlord_id: property.landlord_id,
      rental_amount: property.rental_amount,
      deposit_amount: property.deposit_amount,
      additional_charges: property.additional_charges || '',
    });
    setDialogOpen(true);
  };

  const filteredProperties = properties.filter((property) =>
    property.property_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
    property.address.toLowerCase().includes(searchTerm.toLowerCase()) ||
    property.landlord_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div data-testid="properties-page" className="luxury-fade-in">
      <div className="mb-10 flex items-center justify-between">
        <div>
          <h1 className="luxury-title mb-2" data-testid="properties-title">
            Immobili
          </h1>
          <p className="luxury-subtitle">Gestisci i tuoi immobili in affitto</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="btn-luxury" data-testid="add-property-button">
              <Plus size={18} className="mr-2" />
              Aggiungi Immobile
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl luxury-modal">
            <DialogHeader>
              <DialogTitle data-testid="property-dialog-title">
                {editingProperty ? 'Modifica Immobile' : 'Nuovo Immobile'}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4" data-testid="property-form">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="property_code">Codice Immobile *</Label>
                  <Input id="property_code" value={formData.property_code} onChange={(e) => setFormData({ ...formData, property_code: e.target.value })} required className="luxury-input" data-testid="property-code-input" />
                </div>
                <div>
                  <Label htmlFor="property_type">Tipo Immobile *</Label>
                  <Input id="property_type" value={formData.property_type} onChange={(e) => setFormData({ ...formData, property_type: e.target.value })} placeholder="Appartamento, Casa, Villa, ecc." required className="luxury-input" />
                </div>
                <div className="col-span-2">
                  <Label htmlFor="address">Indirizzo *</Label>
                  <Input id="address" value={formData.address} onChange={(e) => setFormData({ ...formData, address: e.target.value })} required className="luxury-input" />
                </div>
                <div>
                  <Label htmlFor="landlord_id">Proprietario *</Label>
                  <Select value={formData.landlord_id} onValueChange={(value) => setFormData({ ...formData, landlord_id: value })} required>
                    <SelectTrigger data-testid="landlord-select"><SelectValue placeholder="Seleziona proprietario" /></SelectTrigger>
                    <SelectContent>{landlords.map((landlord) => (<SelectItem key={landlord.id} value={landlord.id}>{landlord.full_name}</SelectItem>))}</SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="number_of_rooms">Numero Stanze *</Label>
                  <Input id="number_of_rooms" type="number" min="1" value={formData.number_of_rooms} onChange={(e) => setFormData({ ...formData, number_of_rooms: parseInt(e.target.value) })} required className="luxury-input" />
                </div>
                <div>
                  <Label htmlFor="capacity">Capacit&agrave; *</Label>
                  <Input id="capacity" type="number" min="1" value={formData.capacity} onChange={(e) => setFormData({ ...formData, capacity: parseInt(e.target.value) })} required className="luxury-input" />
                </div>
                <div>
                  <Label htmlFor="rental_amount">Importo Affitto *</Label>
                  <Input id="rental_amount" type="number" step="0.01" value={formData.rental_amount} onChange={(e) => setFormData({ ...formData, rental_amount: parseFloat(e.target.value) })} required className="luxury-input" />
                </div>
                <div>
                  <Label htmlFor="deposit_amount">Importo Deposito *</Label>
                  <Input id="deposit_amount" type="number" step="0.01" value={formData.deposit_amount} onChange={(e) => setFormData({ ...formData, deposit_amount: parseFloat(e.target.value) })} required className="luxury-input" />
                </div>
              </div>
              <div>
                <Label htmlFor="additional_charges">Costi Aggiuntivi</Label>
                <Input id="additional_charges" value={formData.additional_charges} onChange={(e) => setFormData({ ...formData, additional_charges: e.target.value })} placeholder="Es. Utenze, Manutenzione, ecc." className="luxury-input" />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="rounded-xl" style={{ borderColor: 'rgba(184, 134, 11, 0.2)' }}>Annulla</Button>
                <Button type="submit" className="btn-luxury" data-testid="save-property-button">{editingProperty ? 'Aggiorna' : 'Crea'} Immobile</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="luxury-card overflow-hidden">
        <div className="p-5" style={{ borderBottom: '1px solid rgba(184, 134, 11, 0.12)' }}>
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 transform -translate-y-1/2" size={18} style={{ color: '#B8860B' }} />
            <Input placeholder="Cerca per codice, indirizzo o proprietario..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-11 luxury-input" data-testid="search-property-input" />
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center p-12"><div className="luxury-spinner h-10 w-10"></div></div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow style={{ background: 'linear-gradient(135deg, #9F1239 0%, #BE123C 100%)' }}>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Codice</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Indirizzo</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Tipo</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Proprietario</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Stato</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Inquilini</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Affitto</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider text-right">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredProperties.length === 0 ? (
                <TableRow><TableCell colSpan={8} className="text-center py-10" style={{ color: '#8B7355' }}>Nessun immobile trovato</TableCell></TableRow>
              ) : (
                filteredProperties.map((property) => (
                  <TableRow key={property.id} className="hover:bg-rose-50/30 transition-colors" data-testid={`property-row-${property.id}`}>
                    <TableCell className="font-medium" style={{ color: '#2C1810' }}>{property.property_code}</TableCell>
                    <TableCell style={{ color: '#4A3B31' }}>{property.address}</TableCell>
                    <TableCell style={{ color: '#4A3B31' }}>{property.property_type}</TableCell>
                    <TableCell style={{ color: '#4A3B31' }}>{property.landlord_name}</TableCell>
                    <TableCell>
                      <span className={`luxury-badge ${property.occupancy_status === 'occupied' ? 'badge-success' : ''}`} style={property.occupancy_status !== 'occupied' ? { background: '#f1f5f9', color: '#64748b' } : {}}>
                        {property.occupancy_status === 'occupied' ? 'Occupato' : 'Libero'}
                      </span>
                    </TableCell>
                    <TableCell style={{ color: '#4A3B31' }}>{property.current_tenants_count}/{property.capacity}</TableCell>
                    <TableCell className="font-medium" style={{ color: '#2C1810' }}>&euro;{property.rental_amount.toFixed(2)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button variant="ghost" size="sm" className="rounded-lg hover:bg-amber-50" onClick={() => openEditDialog(property)} data-testid={`edit-property-${property.id}`}><Edit size={16} style={{ color: '#B8860B' }} /></Button>
                        <Button variant="ghost" size="sm" className="rounded-lg hover:bg-red-50" onClick={() => handleDelete(property.id)} data-testid={`delete-property-${property.id}`}><Trash2 size={16} className="text-red-500" /></Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
};

export default Properties;
