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

const Landlords = () => {
  const [landlords, setLandlords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingLandlord, setEditingLandlord] = useState(null);
  const [formData, setFormData] = useState({
    full_name: '',
    phone: '',
    email: '',
    whatsapp: '',
    id_number: '',
    bank_details: '',
    notes: '',
  });

  useEffect(() => {
    fetchLandlords();
  }, []);

  const fetchLandlords = async () => {
    try {
      const { data } = await axios.get(`${API_URL}/landlords`, {
        withCredentials: true,
      });
      setLandlords(data);
    } catch (error) {
      if (error.response?.status === 401) {
        toast.error('Sessione scaduta. Effettua nuovamente il login.');
        setTimeout(() => window.location.href = '/login', 2000);
      } else {
        toast.error('Impossibile caricare i proprietari');
      }
      console.error('Fetch landlords error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingLandlord) {
        await axios.put(`${API_URL}/landlords/${editingLandlord.id}`, formData, {
          withCredentials: true,
        });
        toast.success('Proprietario aggiornato con successo');
      } else {
        await axios.post(`${API_URL}/landlords`, formData, {
          withCredentials: true,
        });
        toast.success('Proprietario creato con successo');
      }
      setDialogOpen(false);
      resetForm();
      fetchLandlords();
    } catch (error) {
      if (error.response?.status === 401) {
        toast.error('Sessione scaduta. Effettua nuovamente il login.');
        setTimeout(() => window.location.href = '/login', 2000);
      } else {
        toast.error('Impossibile salvare il proprietario');
      }
      console.error('Save landlord error:', error.response?.data || error);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Sei sicuro di voler eliminare questo proprietario?')) return;
    try {
      await axios.delete(`${API_URL}/landlords/${id}`, {
        withCredentials: true,
      });
      toast.success('Proprietario eliminato con successo');
      fetchLandlords();
    } catch (error) {
      if (error.response?.status === 401) {
        toast.error('Sessione scaduta. Effettua nuovamente il login.');
        setTimeout(() => window.location.href = '/login', 2000);
      } else {
        toast.error('Impossibile eliminare il proprietario');
      }
      console.error('Delete landlord error:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      full_name: '',
      phone: '',
      email: '',
      whatsapp: '',
      id_number: '',
      bank_details: '',
      notes: '',
    });
    setEditingLandlord(null);
  };

  const openEditDialog = (landlord) => {
    setEditingLandlord(landlord);
    setFormData({
      full_name: landlord.full_name,
      phone: landlord.phone,
      email: landlord.email,
      whatsapp: landlord.whatsapp,
      id_number: landlord.id_number,
      bank_details: landlord.bank_details,
      notes: landlord.notes || '',
    });
    setDialogOpen(true);
  };

  const filteredLandlords = landlords.filter((landlord) =>
    landlord.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    landlord.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div data-testid="landlords-page">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-semibold font-heading text-slate-900 mb-2" data-testid="landlords-title">
            Landlords
          </h1>
          <p className="text-slate-600">Manage your landlord profiles and properties</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="bg-rose-700 hover:bg-rose-800" data-testid="add-landlord-button">
              <Plus size={18} className="mr-2" />
              Add Landlord
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle data-testid="landlord-dialog-title">
                {editingLandlord ? 'Edit Landlord' : 'Add New Landlord'}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4" data-testid="landlord-form">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="full_name">Full Name *</Label>
                  <Input
                    id="full_name"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    required
                    data-testid="landlord-name-input"
                  />
                </div>
                <div>
                  <Label htmlFor="id_number">ID Number *</Label>
                  <Input
                    id="id_number"
                    value={formData.id_number}
                    onChange={(e) => setFormData({ ...formData, id_number: e.target.value })}
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
                    data-testid="landlord-email-input"
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
                  <Label htmlFor="bank_details">Bank Details *</Label>
                  <Input
                    id="bank_details"
                    value={formData.bank_details}
                    onChange={(e) => setFormData({ ...formData, bank_details: e.target.value })}
                    required
                  />
                </div>
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
                <Button type="submit" className="bg-rose-700 hover:bg-rose-800" data-testid="save-landlord-button">
                  {editingLandlord ? 'Update' : 'Create'} Landlord
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
              placeholder="Search by name or email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
              data-testid="search-landlord-input"
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
                <TableHead>Email</TableHead>
                <TableHead>Phone</TableHead>
                <TableHead>Properties</TableHead>
                <TableHead>Bank Details</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredLandlords.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-slate-500">
                    No landlords found
                  </TableCell>
                </TableRow>
              ) : (
                filteredLandlords.map((landlord) => (
                  <TableRow key={landlord.id} data-testid={`landlord-row-${landlord.id}`}>
                    <TableCell className="font-medium">{landlord.full_name}</TableCell>
                    <TableCell>{landlord.email}</TableCell>
                    <TableCell>{landlord.phone}</TableCell>
                    <TableCell>{landlord.properties_count}</TableCell>
                    <TableCell>{landlord.bank_details}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Link to={`/landlords/${landlord.id}`}>
                          <Button variant="ghost" size="sm" data-testid={`view-landlord-${landlord.id}`}>
                            <Eye size={16} />
                          </Button>
                        </Link>
                        <Button variant="ghost" size="sm" onClick={() => openEditDialog(landlord)} data-testid={`edit-landlord-${landlord.id}`}>
                          <Edit size={16} />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDelete(landlord.id)} data-testid={`delete-landlord-${landlord.id}`}>
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

export default Landlords;
