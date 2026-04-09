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
    <div data-testid="properties-page">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-semibold font-heading text-slate-900 mb-2" data-testid="properties-title">
            Properties
          </h1>
          <p className="text-slate-600">Manage your rental properties</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="bg-blue-700 hover:bg-blue-800" data-testid="add-property-button">
              <Plus size={18} className="mr-2" />
              Add Property
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle data-testid="property-dialog-title">
                {editingProperty ? 'Edit Property' : 'Add New Property'}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4" data-testid="property-form">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="property_code">Property Code *</Label>
                  <Input
                    id="property_code"
                    value={formData.property_code}
                    onChange={(e) => setFormData({ ...formData, property_code: e.target.value })}
                    required
                    data-testid="property-code-input"
                  />
                </div>
                <div>
                  <Label htmlFor="property_type">Property Type *</Label>
                  <Input
                    id="property_type"
                    value={formData.property_type}
                    onChange={(e) => setFormData({ ...formData, property_type: e.target.value })}
                    placeholder="Apartment, House, Villa, etc."
                    required
                  />
                </div>
                <div className="col-span-2">
                  <Label htmlFor="address">Address *</Label>
                  <Input
                    id="address"
                    value={formData.address}
                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="landlord_id">Landlord *</Label>
                  <Select
                    value={formData.landlord_id}
                    onValueChange={(value) => setFormData({ ...formData, landlord_id: value })}
                    required
                  >
                    <SelectTrigger data-testid="landlord-select">
                      <SelectValue placeholder="Select landlord" />
                    </SelectTrigger>
                    <SelectContent>
                      {landlords.map((landlord) => (
                        <SelectItem key={landlord.id} value={landlord.id}>
                          {landlord.full_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="number_of_rooms">Number of Rooms *</Label>
                  <Input
                    id="number_of_rooms"
                    type="number"
                    min="1"
                    value={formData.number_of_rooms}
                    onChange={(e) => setFormData({ ...formData, number_of_rooms: parseInt(e.target.value) })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="capacity">Capacity *</Label>
                  <Input
                    id="capacity"
                    type="number"
                    min="1"
                    value={formData.capacity}
                    onChange={(e) => setFormData({ ...formData, capacity: parseInt(e.target.value) })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="rental_amount">Rental Amount *</Label>
                  <Input
                    id="rental_amount"
                    type="number"
                    step="0.01"
                    value={formData.rental_amount}
                    onChange={(e) => setFormData({ ...formData, rental_amount: parseFloat(e.target.value) })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="deposit_amount">Deposit Amount *</Label>
                  <Input
                    id="deposit_amount"
                    type="number"
                    step="0.01"
                    value={formData.deposit_amount}
                    onChange={(e) => setFormData({ ...formData, deposit_amount: parseFloat(e.target.value) })}
                    required
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="additional_charges">Additional Charges</Label>
                <Input
                  id="additional_charges"
                  value={formData.additional_charges}
                  onChange={(e) => setFormData({ ...formData, additional_charges: e.target.value })}
                  placeholder="e.g., Utilities, Maintenance, etc."
                />
              </div>
              <div className="flex justify-end gap-3">
                <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }}>
                  Cancel
                </Button>
                <Button type="submit" className="bg-blue-700 hover:bg-blue-800" data-testid="save-property-button">
                  {editingProperty ? 'Update' : 'Create'} Property
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm">
        <div className="p-4 border-b border-slate-200">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={18} />
            <Input
              placeholder="Search by code, address, or landlord..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
              data-testid="search-property-input"
            />
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center p-12">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-700 border-r-transparent" />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Code</TableHead>
                <TableHead>Address</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Landlord</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Tenants</TableHead>
                <TableHead>Rent</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredProperties.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8 text-slate-500">
                    No properties found
                  </TableCell>
                </TableRow>
              ) : (
                filteredProperties.map((property) => (
                  <TableRow key={property.id} data-testid={`property-row-${property.id}`}>
                    <TableCell className="font-medium">{property.property_code}</TableCell>
                    <TableCell>{property.address}</TableCell>
                    <TableCell>{property.property_type}</TableCell>
                    <TableCell>{property.landlord_name}</TableCell>
                    <TableCell>
                      <span className={`px-2 py-1 rounded-md text-xs font-medium ${
                        property.occupancy_status === 'occupied' ? 'bg-green-100 text-green-700' :
                        'bg-slate-100 text-slate-700'
                      }`}>
                        {property.occupancy_status}
                      </span>
                    </TableCell>
                    <TableCell>{property.current_tenants_count}/{property.capacity}</TableCell>
                    <TableCell>${property.rental_amount.toFixed(2)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button variant="ghost" size="sm" onClick={() => openEditDialog(property)} data-testid={`edit-property-${property.id}`}>
                          <Edit size={16} />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDelete(property.id)} data-testid={`delete-property-${property.id}`}>
                          <Trash2 size={16} className="text-red-600" />
                        </Button>
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
