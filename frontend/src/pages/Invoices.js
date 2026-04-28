import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Plus, Search, Download, DollarSign } from 'lucide-react';
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
import { fmtDate } from '../lib/format';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Invoices = () => {
  const [invoices, setInvoices] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [properties, setProperties] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [formData, setFormData] = useState({
    tenant_id: '',
    property_id: '',
    contract_id: '',
    invoice_type: 'rent',
    rent: 0,
    deposit: 0,
    agency_fee: 0,
    registration: 98,
    discount: 0,
    due_date: new Date().toISOString().split('T')[0],
    description: '',
  });
  const [paymentData, setPaymentData] = useState({
    amount: 0,
    payment_method: 'cash',
    payment_date: new Date().toISOString().split('T')[0],
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [invoicesRes, tenantsRes, propertiesRes, contractsRes] = await Promise.all([
        axios.get(`${API_URL}/invoices`, { withCredentials: true }),
        axios.get(`${API_URL}/tenants`, { withCredentials: true }),
        axios.get(`${API_URL}/properties`, { withCredentials: true }),
        axios.get(`${API_URL}/contracts`, { withCredentials: true }),
      ]);
      setInvoices(invoicesRes.data);
      setTenants(tenantsRes.data);
      setProperties(propertiesRes.data);
      setContracts(contractsRes.data);
    } catch (error) {
      toast.error('Failed to load invoices');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const total = (parseFloat(formData.rent) || 0)
        + (parseFloat(formData.deposit) || 0)
        + (parseFloat(formData.agency_fee) || 0)
        + (parseFloat(formData.registration) || 0)
        - (parseFloat(formData.discount) || 0);
      const desc = [
        formData.rent ? `Affitto: €${formData.rent}` : null,
        formData.deposit ? `Deposito: €${formData.deposit}` : null,
        formData.agency_fee ? `Spese agenzia: €${formData.agency_fee}` : null,
        formData.registration ? `Registrazione: €${formData.registration}` : null,
        formData.discount ? `Sconto: -€${formData.discount}` : null,
        formData.description,
      ].filter(Boolean).join(' | ');
      const payload = {
        tenant_id: formData.tenant_id,
        property_id: formData.property_id,
        contract_id: formData.contract_id,
        invoice_type: formData.invoice_type,
        amount: total,
        due_date: formData.due_date,
        description: desc || `Fattura del ${formData.due_date}`,
      };
      await axios.post(`${API_URL}/invoices`, payload, { withCredentials: true });
      toast.success('Fattura creata');
      setDialogOpen(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Errore creazione fattura');
    }
  };

  const handlePaymentSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(
        `${API_URL}/payments`,
        { ...paymentData, invoice_id: selectedInvoice.id },
        { withCredentials: true }
      );
      toast.success('Payment recorded successfully');
      setPaymentDialogOpen(false);
      setSelectedInvoice(null);
      resetPaymentForm();
      fetchData();
    } catch (error) {
      toast.error('Failed to record payment');
    }
  };

  const downloadPDF = async (invoiceId) => {
    try {
      const response = await axios.get(`${API_URL}/invoices/${invoiceId}/pdf`, {
        withCredentials: true,
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `invoice_${invoiceId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Invoice PDF downloaded');
    } catch (error) {
      toast.error('Failed to download PDF');
    }
  };

  const resetForm = () => {
    setFormData({
      tenant_id: '',
      property_id: '',
      contract_id: '',
      invoice_type: 'rent',
      rent: 0,
      deposit: 0,
      agency_fee: 0,
      registration: 98,
      discount: 0,
      due_date: new Date().toISOString().split('T')[0],
      description: '',
    });
  };

  // Auto-fill property/contract/owner + rent/deposit when tenant is selected
  const handleTenantChange = (tenantId) => {
    const tenant = tenants.find(t => t.id === tenantId);
    if (!tenant) { setFormData({ ...formData, tenant_id: tenantId }); return; }
    const contract = contracts.find(c => c.tenant_id === tenantId && c.status === 'active');
    const baseRent = tenant.room_type === 'double' ? (tenant.room_rent || 0) / 2 : (tenant.room_rent || 0);
    setFormData({
      ...formData,
      tenant_id: tenantId,
      property_id: tenant.property_id || formData.property_id,
      contract_id: contract?.id || '',
      rent: baseRent || (contract?.monthly_rent || 0),
      deposit: tenant.deposit_amount || ((contract?.monthly_rent || baseRent || 0) * 2),
      agency_fee: baseRent || (contract?.monthly_rent || 0),
    });
  };

  const resetPaymentForm = () => {
    setPaymentData({
      amount: 0,
      payment_method: 'cash',
      payment_date: new Date().toISOString().split('T')[0],
    });
  };

  const openPaymentDialog = (invoice) => {
    setSelectedInvoice(invoice);
    setPaymentData({
      amount: invoice.amount,
      payment_method: 'cash',
      payment_date: new Date().toISOString().split('T')[0],
    });
    setPaymentDialogOpen(true);
  };

  const filteredInvoices = invoices.filter((invoice) =>
    invoice.invoice_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    invoice.tenant_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    invoice.property_address.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div data-testid="invoices-page" className="luxury-fade-in">
      <div className="mb-10 flex items-center justify-between">
        <div>
          <h1 className="luxury-title mb-2" data-testid="invoices-title">
            Fatture
          </h1>
          <p className="luxury-subtitle">Gestisci fatture e pagamenti</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="btn-luxury" data-testid="add-invoice-button">
              <Plus size={18} className="mr-2" />
              Crea Fattura
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl luxury-modal">
            <DialogHeader>
              <DialogTitle data-testid="invoice-dialog-title">Crea Nuova Fattura</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4" data-testid="invoice-form">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="tenant_id">Inquilino *</Label>
                  <Select
                    value={formData.tenant_id}
                    onValueChange={handleTenantChange}
                    required
                  >
                    <SelectTrigger data-testid="invoice-tenant-select">
                      <SelectValue placeholder="Seleziona inquilino" />
                    </SelectTrigger>
                    <SelectContent>
                      {tenants.map((tenant) => (
                        <SelectItem key={tenant.id} value={tenant.id}>
                          {tenant.full_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="property_id">Immobile (auto)</Label>
                  <Select
                    value={formData.property_id}
                    onValueChange={(value) => setFormData({ ...formData, property_id: value })}
                  >
                    <SelectTrigger data-testid="invoice-property-select">
                      <SelectValue placeholder="Seleziona immobile" />
                    </SelectTrigger>
                    <SelectContent>
                      {properties.map((property) => (
                        <SelectItem key={property.id} value={property.id}>
                          {property.property_code} — {property.address}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="contract_id">Contratto (auto)</Label>
                  <Select
                    value={formData.contract_id}
                    onValueChange={(value) => setFormData({ ...formData, contract_id: value })}
                  >
                    <SelectTrigger data-testid="invoice-contract-select">
                      <SelectValue placeholder="Seleziona contratto" />
                    </SelectTrigger>
                    <SelectContent>
                      {contracts.map((contract) => (
                        <SelectItem key={contract.id} value={contract.id}>
                          {contract.contract_number}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="due_date">Data Fattura *</Label>
                  <Input
                    id="due_date"
                    type="date"
                    value={formData.due_date}
                    onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                    required
                  />
                </div>
              </div>

              {/* Dynamic invoice composition panel */}
              <div className="rounded-xl p-4 space-y-3" style={{ background: 'rgba(184,134,11,0.04)', border: '1px solid rgba(184,134,11,0.15)' }}>
                <h4 className="text-sm font-semibold" style={{ color: '#9F1239' }}>Voci della fattura</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label>Affitto (1 mese)</Label>
                    <Input type="number" step="0.01" value={formData.rent} onChange={(e) => setFormData({ ...formData, rent: parseFloat(e.target.value) || 0 })} className="luxury-input" data-testid="invoice-rent" />
                  </div>
                  <div>
                    <Label>Deposito (2 mesi)</Label>
                    <Input type="number" step="0.01" value={formData.deposit} onChange={(e) => setFormData({ ...formData, deposit: parseFloat(e.target.value) || 0 })} className="luxury-input" data-testid="invoice-deposit" />
                  </div>
                  <div>
                    <Label>Spese agenzia (1 mese)</Label>
                    <Input type="number" step="0.01" value={formData.agency_fee} onChange={(e) => setFormData({ ...formData, agency_fee: parseFloat(e.target.value) || 0 })} className="luxury-input" data-testid="invoice-agency" />
                  </div>
                  <div>
                    <Label>Registrazione</Label>
                    <Input type="number" step="0.01" value={formData.registration} onChange={(e) => setFormData({ ...formData, registration: parseFloat(e.target.value) || 0 })} className="luxury-input" data-testid="invoice-registration" />
                  </div>
                  <div className="col-span-2">
                    <Label>Sconto</Label>
                    <Input type="number" step="0.01" value={formData.discount} onChange={(e) => setFormData({ ...formData, discount: parseFloat(e.target.value) || 0 })} className="luxury-input" data-testid="invoice-discount" />
                  </div>
                </div>
                <div className="flex items-center justify-between pt-2 border-t" style={{ borderColor: 'rgba(184,134,11,0.15)' }}>
                  <span className="text-sm font-semibold" style={{ color: '#2C1810' }}>TOTALE</span>
                  <span className="text-lg font-bold" style={{ color: '#9F1239' }} data-testid="invoice-total">
                    €{(((parseFloat(formData.rent) || 0) + (parseFloat(formData.deposit) || 0) + (parseFloat(formData.agency_fee) || 0) + (parseFloat(formData.registration) || 0)) - (parseFloat(formData.discount) || 0)).toFixed(2)}
                  </span>
                </div>
              </div>

              <div>
                <Label htmlFor="description">Note (opzionale)</Label>
                <Input
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>
              <div className="flex justify-end gap-3">
                <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }}>
                  Annulla
                </Button>
                <Button type="submit" className="btn-luxury" data-testid="save-invoice-button">
                  Crea Fattura
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Dialog open={paymentDialogOpen} onOpenChange={setPaymentDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Record Payment</DialogTitle>
          </DialogHeader>
          {selectedInvoice && (
            <form onSubmit={handlePaymentSubmit} className="space-y-4" data-testid="payment-form">
              <div className="p-4 bg-slate-50 rounded-lg">
                <p className="text-sm text-slate-600">Invoice: {selectedInvoice.invoice_number}</p>
                <p className="text-lg font-semibold text-slate-900">Amount: ${selectedInvoice.amount.toFixed(2)}</p>
              </div>
              <div>
                <Label htmlFor="payment_amount">Payment Amount *</Label>
                <Input
                  id="payment_amount"
                  type="number"
                  step="0.01"
                  value={paymentData.amount}
                  onChange={(e) => setPaymentData({ ...paymentData, amount: parseFloat(e.target.value) })}
                  required
                />
              </div>
              <div>
                <Label htmlFor="payment_method">Payment Method *</Label>
                <Select
                  value={paymentData.payment_method}
                  onValueChange={(value) => setPaymentData({ ...paymentData, payment_method: value })}
                  required
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="cash">Cash</SelectItem>
                    <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                    <SelectItem value="check">Check</SelectItem>
                    <SelectItem value="credit_card">Credit Card</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="payment_date">Payment Date *</Label>
                <Input
                  id="payment_date"
                  type="date"
                  value={paymentData.payment_date}
                  onChange={(e) => setPaymentData({ ...paymentData, payment_date: e.target.value })}
                  required
                />
              </div>
              <div className="flex justify-end gap-3">
                <Button type="button" variant="outline" onClick={() => setPaymentDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" className="btn-luxury" data-testid="save-payment-button">
                  Registra Pagamento
                </Button>
              </div>
            </form>
          )}
        </DialogContent>
      </Dialog>

      <div className="luxury-card overflow-hidden">
        <div className="p-5" style={{ borderBottom: '1px solid rgba(184, 134, 11, 0.12)' }}>
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 transform -translate-y-1/2" size={18} style={{ color: '#B8860B' }} />
            <Input
              placeholder="Cerca per numero fattura, inquilino o immobile..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-11 luxury-input"
              data-testid="search-invoice-input"
            />
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center p-12"><div className="luxury-spinner h-10 w-10"></div></div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow style={{ background: 'linear-gradient(135deg, #9F1239 0%, #BE123C 100%)' }}>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">N. Fattura</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Inquilino</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Immobile</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Tipo</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Importo</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Scadenza</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Stato</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider text-right">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredInvoices.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8 text-slate-500">
                    No invoices found
                  </TableCell>
                </TableRow>
              ) : (
                filteredInvoices.map((invoice) => (
                  <TableRow key={invoice.id} data-testid={`invoice-row-${invoice.id}`}>
                    <TableCell className="font-medium font-mono text-sm">{invoice.invoice_number}</TableCell>
                    <TableCell>{invoice.tenant_name}</TableCell>
                    <TableCell className="max-w-[200px] truncate">{invoice.property_address}</TableCell>
                    <TableCell className="capitalize">{invoice.invoice_type}</TableCell>
                    <TableCell className="font-medium">${invoice.amount.toFixed(2)}</TableCell>
                    <TableCell>{fmtDate(invoice.due_date)}</TableCell>
                    <TableCell>
                      <span className={`luxury-badge ${
                        invoice.payment_status === 'paid' ? 'badge-success' : 'badge-warning'
                      }`}>
                        {invoice.payment_status === 'paid' ? 'Pagato' : 'Non Pagato'}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        {invoice.payment_status === 'unpaid' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openPaymentDialog(invoice)}
                            data-testid={`pay-invoice-${invoice.id}`}
                          >
                            <DollarSign size={16} className="text-green-600" />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => downloadPDF(invoice.id)}
                          data-testid={`download-invoice-${invoice.id}`}
                        >
                          <Download size={16} />
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

export default Invoices;
