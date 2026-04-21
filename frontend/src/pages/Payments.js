import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Plus, Search, CreditCard } from 'lucide-react';
import { Link } from 'react-router-dom';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const Payments = () => {
  const [payments, setPayments] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    tenant_id: '', invoice_id: '', amount: '', payment_method: 'contanti', payment_date: new Date().toISOString().slice(0, 10), notes: ''
  });

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      const [p, t, i] = await Promise.all([
        axios.get(`${API}/payments`, { withCredentials: true }),
        axios.get(`${API}/tenants`, { withCredentials: true }),
        axios.get(`${API}/invoices`, { withCredentials: true }),
      ]);
      setPayments(p.data);
      setTenants(t.data);
      setInvoices(i.data);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/payments`, {
        ...formData,
        amount: parseFloat(formData.amount),
      }, { withCredentials: true });
      setDialogOpen(false);
      setFormData({ tenant_id: '', invoice_id: '', amount: '', payment_method: 'contanti', payment_date: new Date().toISOString().slice(0, 10), notes: '' });
      fetchAll();
    } catch (err) { alert(err.response?.data?.detail || 'Errore'); }
  };

  // Get remaining balance for selected tenant
  const selectedTenant = tenants.find(t => t.id === formData.tenant_id);
  const tenantInvoices = invoices.filter(i => i.tenant_id === formData.tenant_id && i.payment_status !== 'paid');

  const filtered = payments.filter(p =>
    p.tenant_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.payment_method?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div data-testid="payments-page" className="luxury-fade-in">
      <div className="mb-10 flex items-center justify-between">
        <div>
          <h1 className="luxury-title mb-2">Pagamenti</h1>
          <p className="luxury-subtitle">Registra pagamenti parziali o completi</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="btn-luxury"><Plus size={18} className="mr-2" /> Registra Pagamento</Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg luxury-modal">
            <DialogHeader><DialogTitle>Nuovo Pagamento</DialogTitle></DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label>Inquilino *</Label>
                <Select value={formData.tenant_id} onValueChange={v => setFormData({ ...formData, tenant_id: v, invoice_id: '' })}>
                  <SelectTrigger><SelectValue placeholder="Seleziona inquilino" /></SelectTrigger>
                  <SelectContent>{tenants.map(t => <SelectItem key={t.id} value={t.id}>{t.full_name} {t.remaining_balance > 0 ? `(Saldo: \u20ac${t.remaining_balance.toFixed(2)})` : ''}</SelectItem>)}</SelectContent>
                </Select>
              </div>

              {selectedTenant && selectedTenant.remaining_balance > 0 && (
                <div className="p-3 rounded-xl" style={{ background: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.15)' }}>
                  <p className="text-sm"><strong>Saldo residuo:</strong> <span style={{ color: '#DC2626' }}>&euro;{selectedTenant.remaining_balance.toFixed(2)}</span></p>
                </div>
              )}

              {tenantInvoices.length > 0 && (
                <div>
                  <Label>Collegare a fattura (opzionale)</Label>
                  <Select value={formData.invoice_id || 'none'} onValueChange={v => setFormData({ ...formData, invoice_id: v === 'none' ? '' : v })}>
                    <SelectTrigger><SelectValue placeholder="Nessuna fattura" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Nessuna</SelectItem>
                      {tenantInvoices.map(i => <SelectItem key={i.id} value={i.id}>{i.invoice_number} - &euro;{i.amount} ({i.payment_status})</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Importo *</Label>
                  <Input type="number" step="0.01" value={formData.amount} onChange={e => setFormData({ ...formData, amount: e.target.value })} required className="luxury-input" placeholder="0.00" />
                </div>
                <div>
                  <Label>Metodo *</Label>
                  <Select value={formData.payment_method} onValueChange={v => setFormData({ ...formData, payment_method: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="contanti">Contanti</SelectItem>
                      <SelectItem value="bonifico">Bonifico</SelectItem>
                      <SelectItem value="carta">Carta</SelectItem>
                      <SelectItem value="assegno">Assegno</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div><Label>Data *</Label><Input type="date" value={formData.payment_date} onChange={e => setFormData({ ...formData, payment_date: e.target.value })} required className="luxury-input" /></div>
              <div><Label>Note</Label><Input value={formData.notes} onChange={e => setFormData({ ...formData, notes: e.target.value })} className="luxury-input notes-text" placeholder="Note opzionali..." /></div>
              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)} className="rounded-xl">Annulla</Button>
                <Button type="submit" className="btn-luxury">Registra Pagamento</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="luxury-card overflow-hidden">
        <div className="p-5" style={{ borderBottom: '1px solid rgba(184,134,11,0.12)' }}>
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2" size={18} style={{ color: '#B8860B' }} />
            <Input placeholder="Cerca pagamenti..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="pl-11 luxury-input" />
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center p-12"><div className="luxury-spinner h-10 w-10" /></div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow style={{ background: 'linear-gradient(135deg, #9F1239 0%, #BE123C 100%)' }}>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Data</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Inquilino</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Importo</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Metodo</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Note</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.length === 0 ? (
                <TableRow><TableCell colSpan={5} className="text-center py-10" style={{ color: '#8B7355' }}>Nessun pagamento trovato</TableCell></TableRow>
              ) : filtered.map(p => (
                <TableRow key={p.id} className="hover:bg-rose-50/30 transition-colors">
                  <TableCell style={{ color: '#4A3B31' }}>{p.payment_date}</TableCell>
                  <TableCell>
                    {p.tenant_id ? <Link to={`/tenants/${p.tenant_id}`} className="font-medium underline" style={{ color: '#9F1239' }}>{p.tenant_name}</Link> : p.tenant_name}
                  </TableCell>
                  <TableCell className="font-bold" style={{ color: '#059669' }}>&euro;{p.amount?.toFixed(2)}</TableCell>
                  <TableCell className="capitalize" style={{ color: '#4A3B31' }}>{p.payment_method}</TableCell>
                  <TableCell className="notes-text" style={{ color: '#8B7355' }}>{p.notes || '-'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
};

export default Payments;
