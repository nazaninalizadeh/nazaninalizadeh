import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Plus, Search, Download, Edit } from 'lucide-react';
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
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Contracts = () => {
  const [contracts, setContracts] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    tenant_id: '',
    property_id: '',
    start_date: '',
    end_date: '',
    rent_amount: 0,
    deposit_amount: 0,
    terms: 'This rental agreement is entered into on the specified start date and will remain in effect until the end date. The tenant agrees to pay the monthly rent on time and maintain the property in good condition.',
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [contractsRes, tenantsRes, propertiesRes] = await Promise.all([
        axios.get(`${API_URL}/contracts`, { withCredentials: true }),
        axios.get(`${API_URL}/tenants`, { withCredentials: true }),
        axios.get(`${API_URL}/properties`, { withCredentials: true }),
      ]);
      setContracts(contractsRes.data);
      setTenants(tenantsRes.data);
      setProperties(propertiesRes.data);
    } catch (error) {
      toast.error('Failed to load contracts');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/contracts`, formData, {
        withCredentials: true,
      });
      toast.success('Contract created successfully');
      setDialogOpen(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error('Failed to create contract');
    }
  };

  const handleStatusChange = async (contractId, newStatus) => {
    try {
      await axios.put(
        `${API_URL}/contracts/${contractId}/status?status=${newStatus}`,
        {},
        { withCredentials: true }
      );
      toast.success('Contract status updated');
      fetchData();
    } catch (error) {
      toast.error('Failed to update status');
    }
  };

  const downloadPDF = async (contractId) => {
    try {
      const response = await axios.get(`${API_URL}/contracts/${contractId}/pdf`, {
        withCredentials: true,
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `contract_${contractId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Contract PDF downloaded');
    } catch (error) {
      toast.error('Failed to download PDF');
    }
  };

  const resetForm = () => {
    setFormData({
      tenant_id: '',
      property_id: '',
      start_date: '',
      end_date: '',
      rent_amount: 0,
      deposit_amount: 0,
      terms: 'This rental agreement is entered into on the specified start date and will remain in effect until the end date. The tenant agrees to pay the monthly rent on time and maintain the property in good condition.',
    });
  };

  const filteredContracts = contracts.filter((contract) =>
    contract.contract_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contract.tenant_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contract.property_address.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div data-testid="contracts-page">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-semibold font-heading text-slate-900 mb-2" data-testid="contracts-title">
            Contracts
          </h1>
          <p className="text-slate-600">Manage rental contracts and agreements</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="bg-blue-700 hover:bg-blue-800" data-testid="add-contract-button">
              <Plus size={18} className="mr-2" />
              Create Contract
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle data-testid="contract-dialog-title">Create New Contract</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4" data-testid="contract-form">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="tenant_id">Tenant *</Label>
                  <Select
                    value={formData.tenant_id}
                    onValueChange={(value) => setFormData({ ...formData, tenant_id: value })}
                    required
                  >
                    <SelectTrigger data-testid="tenant-select">
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
                    <SelectTrigger data-testid="property-select">
                      <SelectValue placeholder="Select property" />
                    </SelectTrigger>
                    <SelectContent>
                      {properties.map((property) => (
                        <SelectItem key={property.id} value={property.id}>
                          {property.property_code} - {property.address}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="start_date">Start Date *</Label>
                  <Input
                    id="start_date"
                    type="date"
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="end_date">End Date *</Label>
                  <Input
                    id="end_date"
                    type="date"
                    value={formData.end_date}
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="rent_amount">Monthly Rent *</Label>
                  <Input
                    id="rent_amount"
                    type="number"
                    step="0.01"
                    value={formData.rent_amount}
                    onChange={(e) => setFormData({ ...formData, rent_amount: parseFloat(e.target.value) })}
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
                <Label htmlFor="terms">Terms and Conditions *</Label>
                <Textarea
                  id="terms"
                  value={formData.terms}
                  onChange={(e) => setFormData({ ...formData, terms: e.target.value })}
                  rows={6}
                  required
                />
              </div>
              <div className="flex justify-end gap-3">
                <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }}>
                  Cancel
                </Button>
                <Button type="submit" className="bg-blue-700 hover:bg-blue-800" data-testid="save-contract-button">
                  Create Contract
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
              placeholder="Search by contract number, tenant, or property..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
              data-testid="search-contract-input"
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
                <TableHead>Contract Number</TableHead>
                <TableHead>Tenant</TableHead>
                <TableHead>Property</TableHead>
                <TableHead>Start Date</TableHead>
                <TableHead>End Date</TableHead>
                <TableHead>Rent</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredContracts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8 text-slate-500">
                    No contracts found
                  </TableCell>
                </TableRow>
              ) : (
                filteredContracts.map((contract) => (
                  <TableRow key={contract.id} data-testid={`contract-row-${contract.id}`}>
                    <TableCell className="font-medium font-mono text-sm">{contract.contract_number}</TableCell>
                    <TableCell>{contract.tenant_name}</TableCell>
                    <TableCell className="max-w-[200px] truncate">{contract.property_address}</TableCell>
                    <TableCell>{contract.start_date}</TableCell>
                    <TableCell>{contract.end_date}</TableCell>
                    <TableCell>${contract.rent_amount.toFixed(2)}</TableCell>
                    <TableCell>
                      <Select
                        value={contract.status}
                        onValueChange={(value) => handleStatusChange(contract.id, value)}
                      >
                        <SelectTrigger className="w-[120px]" data-testid={`status-select-${contract.id}`}>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="active">Active</SelectItem>
                          <SelectItem value="expired">Expired</SelectItem>
                          <SelectItem value="cancelled">Cancelled</SelectItem>
                          <SelectItem value="renewed">Renewed</SelectItem>
                        </SelectContent>
                      </Select>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => downloadPDF(contract.id)}
                        data-testid={`download-contract-${contract.id}`}
                      >
                        <Download size={16} />
                      </Button>
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

export default Contracts;
