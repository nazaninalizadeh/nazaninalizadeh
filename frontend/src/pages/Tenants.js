import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { Plus, Search, Eye, Edit, Trash2 } from 'lucide-react';
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
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Tenants = () => {
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingTenant, setEditingTenant] = useState(null);
  const [formData, setFormData] = useState({
    full_name: '',
    passport_number: '',
    nationality: '',
    date_of_birth: '',
    passport_issue_date: '',
    passport_expiry_date: '',
    phone: '',
    email: '',
    whatsapp: '',
    address: '',
    occupation: '',
    notes: '',
    deposit_amount: 0,
  });

  useEffect(() => {
    fetchTenants();
  }, []);

  const fetchTenants = async () => {
    try {
      const { data } = await axios.get(`${API_URL}/tenants`, {
        withCredentials: true,
      });
      setTenants(data);
    } catch (error) {
      toast.error('Impossibile caricare gli inquilini');
      console.error('Fetch tenants error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingTenant) {
        await axios.put(`${API_URL}/tenants/${editingTenant.id}`, formData, {
          withCredentials: true,
        });
        toast.success('Inquilino aggiornato con successo');
      } else {
        await axios.post(`${API_URL}/tenants`, formData, {
          withCredentials: true,
        });
        toast.success('Inquilino creato con successo');
      }
      setDialogOpen(false);
      resetForm();
      fetchTenants();
    } catch (error) {
      toast.error('Impossibile salvare l\'inquilino');
      console.error('Save tenant error:', error.response?.data || error);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Sei sicuro di voler eliminare questo inquilino?')) return;
    try {
      await axios.delete(`${API_URL}/tenants/${id}`, {
        withCredentials: true,
      });
      toast.success('Inquilino eliminato con successo');
      fetchTenants();
    } catch (error) {
      toast.error('Impossibile eliminare l\'inquilino');
      console.error('Delete tenant error:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      full_name: '',
      passport_number: '',
      nationality: '',
      date_of_birth: '',
      passport_issue_date: '',
      passport_expiry_date: '',
      phone: '',
      email: '',
      whatsapp: '',
      address: '',
      occupation: '',
      notes: '',
      deposit_amount: 0,
    });
    setEditingTenant(null);
  };

  const openEditDialog = (tenant) => {
    setEditingTenant(tenant);
    setFormData({
      full_name: tenant.full_name,
      passport_number: tenant.passport_number,
      nationality: tenant.nationality,
      date_of_birth: tenant.date_of_birth,
      passport_issue_date: tenant.passport_issue_date,
      passport_expiry_date: tenant.passport_expiry_date,
      phone: tenant.phone,
      email: tenant.email,
      whatsapp: tenant.whatsapp,
      address: tenant.address,
      occupation: tenant.occupation,
      notes: tenant.notes || '',
      deposit_amount: tenant.deposit_amount,
    });
    setDialogOpen(true);
  };

  const filteredTenants = tenants.filter((tenant) =>
    tenant.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    tenant.passport_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    tenant.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div data-testid="tenants-page">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-semibold font-heading text-slate-900 mb-2" data-testid="tenants-title">
            Tenants
          </h1>
          <p className="text-slate-600">Manage your tenant profiles and information</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="bg-rose-700 hover:bg-rose-800" data-testid="add-tenant-button">
              <Plus size={18} className="mr-2" />
              Add Tenant
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle data-testid="tenant-dialog-title">
                {editingTenant ? 'Edit Tenant' : 'Add New Tenant'}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4" data-testid="tenant-form">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="full_name">Full Name *</Label>
                  <Input
                    id="full_name"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    required
                    data-testid="tenant-name-input"
                  />
                </div>
                <div>
                  <Label htmlFor="passport_number">Passport Number *</Label>
                  <Input
                    id="passport_number"
                    value={formData.passport_number}
                    onChange={(e) => setFormData({ ...formData, passport_number: e.target.value })}
                    required
                    data-testid="tenant-passport-input"
                  />
                </div>
                <div>
                  <Label htmlFor="nationality">Nationality *</Label>
                  <Input
                    id="nationality"
                    value={formData.nationality}
                    onChange={(e) => setFormData({ ...formData, nationality: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="date_of_birth">Date of Birth *</Label>
                  <Input
                    id="date_of_birth"
                    type="date"
                    value={formData.date_of_birth}
                    onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="passport_issue_date">Passport Issue Date *</Label>
                  <Input
                    id="passport_issue_date"
                    type="date"
                    value={formData.passport_issue_date}
                    onChange={(e) => setFormData({ ...formData, passport_issue_date: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="passport_expiry_date">Passport Expiry Date *</Label>
                  <Input
                    id="passport_expiry_date"
                    type="date"
                    value={formData.passport_expiry_date}
                    onChange={(e) => setFormData({ ...formData, passport_expiry_date: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="phone">Phone *</Label>
                  <Input
                    id="phone"
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="email">Email *</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    required
                    data-testid="tenant-email-input"
                  />
                </div>
                <div>
                  <Label htmlFor="whatsapp">WhatsApp *</Label>
                  <Input
                    id="whatsapp"
                    value={formData.whatsapp}
                    onChange={(e) => setFormData({ ...formData, whatsapp: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="occupation">Occupation *</Label>
                  <Input
                    id="occupation"
                    value={formData.occupation}
                    onChange={(e) => setFormData({ ...formData, occupation: e.target.value })}
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
                <Label htmlFor="address">Address *</Label>
                <Input
                  id="address"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  required
                />
              </div>
              <div>
                <Label htmlFor="notes">Notes</Label>
                <Input
                  id="notes"
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                />
              </div>
              <div className="flex justify-end gap-3">
                <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }}>
                  Cancel
                </Button>
                <Button type="submit" className="bg-rose-700 hover:bg-rose-800" data-testid="save-tenant-button">
                  {editingTenant ? 'Update' : 'Create'} Tenant
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
              placeholder="Search by name, passport, or email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
              data-testid="search-tenant-input"
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
                <TableHead>Name</TableHead>
                <TableHead>Passport Number</TableHead>
                <TableHead>Nationality</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Phone</TableHead>
                <TableHead>Deposit</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredTenants.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8 text-slate-500">
                    No tenants found
                  </TableCell>
                </TableRow>
              ) : (
                filteredTenants.map((tenant) => (
                  <TableRow key={tenant.id} data-testid={`tenant-row-${tenant.id}`}>
                    <TableCell className="font-medium">{tenant.full_name}</TableCell>
                    <TableCell>{tenant.passport_number}</TableCell>
                    <TableCell>{tenant.nationality}</TableCell>
                    <TableCell>{tenant.email}</TableCell>
                    <TableCell>{tenant.phone}</TableCell>
                    <TableCell>${tenant.deposit_amount.toFixed(2)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Link to={`/tenants/${tenant.id}`}>
                          <Button variant="ghost" size="sm" data-testid={`view-tenant-${tenant.id}`}>
                            <Eye size={16} />
                          </Button>
                        </Link>
                        <Button variant="ghost" size="sm" onClick={() => openEditDialog(tenant)} data-testid={`edit-tenant-${tenant.id}`}>
                          <Edit size={16} />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDelete(tenant.id)} data-testid={`delete-tenant-${tenant.id}`}>
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

export default Tenants;
