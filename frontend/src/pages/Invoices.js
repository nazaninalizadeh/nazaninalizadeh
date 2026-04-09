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
    amount: 0,
    due_date: '',
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
      await axios.post(`${API_URL}/invoices`, formData, {
        withCredentials: true,
      });
      toast.success('Invoice created successfully');
      setDialogOpen(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error('Failed to create invoice');
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
      amount: 0,
      due_date: '',
      description: '',
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
                  <Label htmlFor="tenant_id">Tenant *</Label>
                  <Select
                    value={formData.tenant_id}
                    onValueChange={(value) => setFormData({ ...formData, tenant_id: value })}
                    required
                  >
                    <SelectTrigger data-testid="invoice-tenant-select">
                      <SelectValue placeholder="Select tenant" />
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
                  <Label htmlFor="property_id">Property *</Label>
                  <Select
                    value={formData.property_id}
                    onValueChange={(value) => setFormData({ ...formData, property_id: value })}
                    required
                  >
                    <SelectTrigger data-testid="invoice-property-select">
                      <SelectValue placeholder="Select property" />
                    </SelectTrigger>
                    <SelectContent>
                      {properties.map((property) => (
                        <SelectItem key={property.id} value={property.id}>
                          {property.property_code}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="contract_id">Contract *</Label>
                  <Select
                    value={formData.contract_id}
                    onValueChange={(value) => setFormData({ ...formData, contract_id: value })}
                    required
                  >
                    <SelectTrigger data-testid="invoice-contract-select">
                      <SelectValue placeholder="Select contract" />
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
                  <Label htmlFor="invoice_type">Invoice Type *</Label>
                  <Select
                    value={formData.invoice_type}
                    onValueChange={(value) => setFormData({ ...formData, invoice_type: value })}
                    required
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="rent">Rent</SelectItem>
                      <SelectItem value="deposit">Deposit</SelectItem>
                      <SelectItem value="penalty">Penalty</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="amount">Amount *</Label>
                  <Input
                    id="amount"
                    type="number"
                    step="0.01"
                    value={formData.amount}
                    onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="due_date">Due Date *</Label>
                  <Input
                    id="due_date"
                    type="date"
                    value={formData.due_date}
                    onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                    required
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="description">Description *</Label>
                <Input
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  required
                />
              </div>
              <div className="flex justify-end gap-3">
                <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }}>
                  Cancel
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
                    <TableCell>{invoice.due_date}</TableCell>
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
