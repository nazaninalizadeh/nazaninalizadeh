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
    <div data-testid="landlords-page" className="luxury-fade-in">
      <div className="mb-10 flex items-center justify-between">
        <div>
          <h1 className="luxury-title mb-2" data-testid="landlords-title">
            Proprietari
          </h1>
          <p className="luxury-subtitle">Gestisci i profili e gli immobili dei proprietari</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="btn-luxury" data-testid="add-landlord-button">
              <Plus size={18} className="mr-2" />
              Aggiungi Proprietario
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl luxury-modal">
            <DialogHeader>
              <DialogTitle data-testid="landlord-dialog-title">
                {editingLandlord ? 'Modifica Proprietario' : 'Nuovo Proprietario'}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4" data-testid="landlord-form">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="full_name">Nome Completo *</Label>
                  <Input
                    id="full_name"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    required
                    className="luxury-input"
                    data-testid="landlord-name-input"
                  />
                </div>
                <div>
                  <Label htmlFor="id_number">Numero Documento *</Label>
                  <Input
                    id="id_number"
                    value={formData.id_number}
                    onChange={(e) => setFormData({ ...formData, id_number: e.target.value })}
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
                    className="luxury-input"
                  />
                </div>
                <div>
                  <Label htmlFor="bank_details">Dati Bancari *</Label>
                  <Input
                    id="bank_details"
                    value={formData.bank_details}
                    onChange={(e) => setFormData({ ...formData, bank_details: e.target.value })}
                    required
                    className="luxury-input"
                  />
                </div>
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
                <Button type="submit" className="btn-luxury" data-testid="save-landlord-button">
                  {editingLandlord ? 'Aggiorna' : 'Crea'} Proprietario
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
              placeholder="Cerca per nome o email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-11 luxury-input"
              data-testid="search-landlord-input"
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
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Email</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Telefono</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Immobili</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Dati Bancari</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider text-right">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredLandlords.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-10" style={{ color: '#8B7355' }}>
                    Nessun proprietario trovato
                  </TableCell>
                </TableRow>
              ) : (
                filteredLandlords.map((landlord) => (
                  <TableRow key={landlord.id} className="hover:bg-rose-50/30 transition-colors" data-testid={`landlord-row-${landlord.id}`}>
                    <TableCell className="font-medium" style={{ color: '#2C1810' }}>{landlord.full_name}</TableCell>
                    <TableCell style={{ color: '#4A3B31' }}>{landlord.email}</TableCell>
                    <TableCell style={{ color: '#4A3B31' }}>{landlord.phone}</TableCell>
                    <TableCell style={{ color: '#4A3B31' }}>{landlord.properties_count}</TableCell>
                    <TableCell style={{ color: '#4A3B31' }}>{landlord.bank_details}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Link to={`/landlords/${landlord.id}`}>
                          <Button variant="ghost" size="sm" className="rounded-lg hover:bg-rose-50" data-testid={`view-landlord-${landlord.id}`}>
                            <Eye size={16} style={{ color: '#9F1239' }} />
                          </Button>
                        </Link>
                        <Button variant="ghost" size="sm" className="rounded-lg hover:bg-amber-50" onClick={() => openEditDialog(landlord)} data-testid={`edit-landlord-${landlord.id}`}>
                          <Edit size={16} style={{ color: '#B8860B' }} />
                        </Button>
                        <Button variant="ghost" size="sm" className="rounded-lg hover:bg-red-50" onClick={() => handleDelete(landlord.id)} data-testid={`delete-landlord-${landlord.id}`}>
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

export default Landlords;
