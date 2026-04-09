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
    <div data-testid="tenants-page" className="luxury-fade-in">
      <div className="mb-10 flex items-center justify-between">
        <div>
          <h1 className="luxury-title mb-2" data-testid="tenants-title">
            Inquilini
          </h1>
          <p className="luxury-subtitle">Gestisci i profili e le informazioni degli inquilini</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="btn-luxury" data-testid="add-tenant-button">
              <Plus size={18} className="mr-2" />
              Aggiungi Inquilino
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto luxury-modal">
            <DialogHeader>
              <DialogTitle data-testid="tenant-dialog-title">
                {editingTenant ? 'Modifica Inquilino' : 'Nuovo Inquilino'}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4" data-testid="tenant-form">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="full_name">Nome Completo *</Label>
                  <Input
                    id="full_name"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    required
                    className="luxury-input"
                    data-testid="tenant-name-input"
                  />
                </div>
                <div>
                  <Label htmlFor="passport_number">Numero Passaporto *</Label>
                  <Input
                    id="passport_number"
                    value={formData.passport_number}
                    onChange={(e) => setFormData({ ...formData, passport_number: e.target.value })}
                    required
                    className="luxury-input"
                    data-testid="tenant-passport-input"
                  />
                </div>
                <div>
                  <Label htmlFor="nationality">Nazionalit&agrave; *</Label>
                  <Input
                    id="nationality"
                    value={formData.nationality}
                    onChange={(e) => setFormData({ ...formData, nationality: e.target.value })}
                    required
                    className="luxury-input"
                  />
                </div>
                <div>
                  <Label htmlFor="date_of_birth">Data di Nascita *</Label>
                  <Input
                    id="date_of_birth"
                    type="date"
                    value={formData.date_of_birth}
                    onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                    required
                    className="luxury-input"
                  />
                </div>
                <div>
                  <Label htmlFor="passport_issue_date">Data Rilascio Passaporto *</Label>
                  <Input
                    id="passport_issue_date"
                    type="date"
                    value={formData.passport_issue_date}
                    onChange={(e) => setFormData({ ...formData, passport_issue_date: e.target.value })}
                    required
                    className="luxury-input"
                  />
                </div>
                <div>
                  <Label htmlFor="passport_expiry_date">Data Scadenza Passaporto *</Label>
                  <Input
                    id="passport_expiry_date"
                    type="date"
                    value={formData.passport_expiry_date}
                    onChange={(e) => setFormData({ ...formData, passport_expiry_date: e.target.value })}
                    required
                    className="luxury-input"
                  />
                </div>
                <div>
                  <Label htmlFor="phone">Telefono *</Label>
                  <Input
                    id="phone"
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    required
                    className="luxury-input"
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
                    className="luxury-input"
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
                    className="luxury-input"
                  />
                </div>
                <div>
                  <Label htmlFor="occupation">Professione *</Label>
                  <Input
                    id="occupation"
                    value={formData.occupation}
                    onChange={(e) => setFormData({ ...formData, occupation: e.target.value })}
                    required
                    className="luxury-input"
                  />
                </div>
                <div>
                  <Label htmlFor="deposit_amount">Importo Deposito *</Label>
                  <Input
                    id="deposit_amount"
                    type="number"
                    step="0.01"
                    value={formData.deposit_amount}
                    onChange={(e) => setFormData({ ...formData, deposit_amount: parseFloat(e.target.value) })}
                    required
                    className="luxury-input"
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="address">Indirizzo *</Label>
                <Input
                  id="address"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  required
                  className="luxury-input"
                />
              </div>
              <div>
                <Label htmlFor="notes">Note</Label>
                <Input
                  id="notes"
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="luxury-input notes-text"
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="rounded-xl" style={{ borderColor: 'rgba(184, 134, 11, 0.2)' }}>
                  Annulla
                </Button>
                <Button type="submit" className="btn-luxury" data-testid="save-tenant-button">
                  {editingTenant ? 'Aggiorna' : 'Crea'} Inquilino
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="luxury-card overflow-hidden">
        <div className="p-5" style={{ borderBottom: '1px solid rgba(184, 134, 11, 0.12)' }}>
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 transform -translate-y-1/2" size={18} style={{ color: '#B8860B' }} />
            <Input
              placeholder="Cerca per nome, passaporto o email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-11 luxury-input"
              data-testid="search-tenant-input"
            />
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center p-12">
            <div className="luxury-spinner h-10 w-10"></div>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow style={{ background: 'linear-gradient(135deg, #9F1239 0%, #BE123C 100%)' }}>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Nome</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Passaporto</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Nazionalit&agrave;</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Email</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Telefono</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Deposito</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider text-right">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredTenants.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-10" style={{ color: '#8B7355' }}>
                    Nessun inquilino trovato
                  </TableCell>
                </TableRow>
              ) : (
                filteredTenants.map((tenant) => (
                  <TableRow key={tenant.id} className="hover:bg-rose-50/30 transition-colors" data-testid={`tenant-row-${tenant.id}`}>
                    <TableCell className="font-medium" style={{ color: '#2C1810' }}>{tenant.full_name}</TableCell>
                    <TableCell style={{ color: '#4A3B31' }}>{tenant.passport_number}</TableCell>
                    <TableCell style={{ color: '#4A3B31' }}>{tenant.nationality}</TableCell>
                    <TableCell style={{ color: '#4A3B31' }}>{tenant.email}</TableCell>
                    <TableCell style={{ color: '#4A3B31' }}>{tenant.phone}</TableCell>
                    <TableCell className="font-medium" style={{ color: '#2C1810' }}>&euro;{tenant.deposit_amount.toFixed(2)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Link to={`/tenants/${tenant.id}`}>
                          <Button variant="ghost" size="sm" className="rounded-lg hover:bg-rose-50" data-testid={`view-tenant-${tenant.id}`}>
                            <Eye size={16} style={{ color: '#9F1239' }} />
                          </Button>
                        </Link>
                        <Button variant="ghost" size="sm" className="rounded-lg hover:bg-amber-50" onClick={() => openEditDialog(tenant)} data-testid={`edit-tenant-${tenant.id}`}>
                          <Edit size={16} style={{ color: '#B8860B' }} />
                        </Button>
                        <Button variant="ghost" size="sm" className="rounded-lg hover:bg-red-50" onClick={() => handleDelete(tenant.id)} data-testid={`delete-tenant-${tenant.id}`}>
                          <Trash2 size={16} className="text-red-500" />
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
