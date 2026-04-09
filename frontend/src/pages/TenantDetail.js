import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Mail, Phone, Calendar, DollarSign, FileText, Receipt } from 'lucide-react';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const TenantDetail = () => {
  const { id } = useParams();
  const [tenant, setTenant] = useState(null);
  const [contracts, setContracts] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTenantDetails();
  }, [id]);

  const fetchTenantDetails = async () => {
    try {
      const [tenantRes, contractsRes, invoicesRes, paymentsRes] = await Promise.all([
        axios.get(`${API_URL}/tenants/${id}`, { withCredentials: true }),
        axios.get(`${API_URL}/contracts`, { withCredentials: true }),
        axios.get(`${API_URL}/invoices`, { withCredentials: true }),
        axios.get(`${API_URL}/payments/tenant/${id}`, { withCredentials: true }),
      ]);

      setTenant(tenantRes.data);
      setContracts(contractsRes.data.filter(c => c.tenant_id === id));
      setInvoices(invoicesRes.data.filter(i => i.tenant_id === id));
      setPayments(paymentsRes.data);
    } catch (error) {
      toast.error('Failed to load tenant details');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-700 border-r-transparent" />
      </div>
    );
  }

  if (!tenant) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-600">Tenant not found</p>
        <Link to="/tenants">
          <Button className="mt-4">Back to Tenants</Button>
        </Link>
      </div>
    );
  }

  return (
    <div data-testid="tenant-detail-page" className="luxury-fade-in">
      <Link to="/tenants">
        <Button variant="ghost" className="mb-6 rounded-xl" style={{ color: '#9F1239' }} data-testid="back-to-tenants">
          <ArrowLeft size={18} className="mr-2" />
          Torna agli Inquilini
        </Button>
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tenant Profile */}
        <div className="lg:col-span-2 space-y-6">
          <div className="luxury-card p-7">
            <h2 className="text-2xl font-semibold font-heading mb-6" style={{ color: '#9F1239' }} data-testid="tenant-name">
              {tenant.full_name}
            </h2>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <p className="text-xs text-slate-500 mb-1">Passport Number</p>
                <p className="text-slate-900 font-medium">{tenant.passport_number}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1">Nationality</p>
                <p className="text-slate-900 font-medium">{tenant.nationality}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1">Date of Birth</p>
                <p className="text-slate-900">{tenant.date_of_birth}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1">Passport Issue Date</p>
                <p className="text-slate-900">{tenant.passport_issue_date}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1">Passport Expiry Date</p>
                <p className="text-slate-900">{tenant.passport_expiry_date}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1">Occupation</p>
                <p className="text-slate-900">{tenant.occupation}</p>
              </div>
            </div>

            <div className="mt-6 pt-6 border-t border-slate-200">
              <h3 className="text-sm font-semibold text-slate-900 mb-4">Contact Information</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-3">
                  <Mail size={18} className="text-slate-400" />
                  <span className="text-slate-900">{tenant.email}</span>
                </div>
                <div className="flex items-center gap-3">
                  <Phone size={18} className="text-slate-400" />
                  <span className="text-slate-900">{tenant.phone}</span>
                </div>
              </div>
              <div className="mt-4">
                <p className="text-xs text-slate-500 mb-1">Address</p>
                <p className="text-slate-900">{tenant.address}</p>
              </div>
            </div>

            {tenant.notes && (
              <div className="mt-6 pt-6 border-t border-slate-200">
                <h3 className="text-sm font-semibold text-slate-900 mb-2">Notes</h3>
                <p className="text-slate-600">{tenant.notes}</p>
              </div>
            )}
          </div>

          {/* Contracts */}
          <div className="luxury-card p-7">
            <h3 className="text-lg font-semibold font-heading mb-4 flex items-center gap-2" style={{ color: '#9F1239' }}>
              <FileText size={20} />
              Contratti
            </h3>
            {contracts.length === 0 ? (
              <p className="text-slate-500 text-sm">No contracts found</p>
            ) : (
              <div className="space-y-3">
                {contracts.map((contract) => (
                  <div key={contract.id} className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                    <div className="flex justify-between items-start mb-2">
                      <p className="font-medium text-slate-900">{contract.contract_number}</p>
                      <span className={`px-2 py-1 rounded-md text-xs font-medium ${
                        contract.status === 'active' ? 'bg-green-100 text-green-700' :
                        contract.status === 'expired' ? 'bg-red-100 text-red-700' :
                        'bg-slate-100 text-slate-700'
                      }`}>
                        {contract.status}
                      </span>
                    </div>
                    <p className="text-sm text-slate-600 mb-1">{contract.property_address}</p>
                    <p className="text-sm text-slate-500">
                      {contract.start_date} to {contract.end_date}
                    </p>
                    <p className="text-sm font-medium text-slate-900 mt-2">
                      Rent: ${contract.rent_amount.toFixed(2)}/month
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Invoices */}
          <div className="luxury-card p-7">
            <h3 className="text-lg font-semibold font-heading mb-4 flex items-center gap-2" style={{ color: '#9F1239' }}>
              <Receipt size={20} />
              Fatture
            </h3>
            {invoices.length === 0 ? (
              <p className="text-slate-500 text-sm">No invoices found</p>
            ) : (
              <div className="space-y-3">
                {invoices.map((invoice) => (
                  <div key={invoice.id} className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                    <div className="flex justify-between items-start mb-2">
                      <p className="font-medium text-slate-900">{invoice.invoice_number}</p>
                      <span className={`px-2 py-1 rounded-md text-xs font-medium ${
                        invoice.payment_status === 'paid' ? 'bg-green-100 text-green-700' :
                        'bg-orange-100 text-orange-700'
                      }`}>
                        {invoice.payment_status}
                      </span>
                    </div>
                    <p className="text-sm text-slate-600 mb-1">{invoice.invoice_type}</p>
                    <p className="text-sm text-slate-500">Due: {invoice.due_date}</p>
                    <p className="text-sm font-medium text-slate-900 mt-2">
                      Amount: ${invoice.amount.toFixed(2)}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Financial Summary */}
        <div className="space-y-6">
          <div className="luxury-card p-7">
            <h3 className="text-lg font-semibold font-heading mb-6" style={{ color: '#9F1239' }}>Riepilogo Finanziario</h3>
            <div className="space-y-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <div className="flex items-center gap-3 mb-2">
                  <DollarSign size={18} className="text-rose-700" />
                  <p className="text-xs text-rose-700 font-semibold uppercase">Deposit Amount</p>
                </div>
                <p className="text-2xl font-semibold text-rose-900">
                  ${tenant.deposit_amount.toFixed(2)}
                </p>
              </div>

              <div className="p-4 bg-green-50 rounded-lg">
                <div className="flex items-center gap-3 mb-2">
                  <DollarSign size={18} className="text-green-700" />
                  <p className="text-xs text-green-700 font-semibold uppercase">Total Paid</p>
                </div>
                <p className="text-2xl font-semibold text-green-900">
                  ${tenant.total_paid.toFixed(2)}
                </p>
              </div>

              <div className="p-4 bg-orange-50 rounded-lg">
                <div className="flex items-center gap-3 mb-2">
                  <DollarSign size={18} className="text-orange-700" />
                  <p className="text-xs text-orange-700 font-semibold uppercase">Remaining Balance</p>
                </div>
                <p className="text-2xl font-semibold text-orange-900">
                  ${tenant.remaining_balance.toFixed(2)}
                </p>
              </div>
            </div>
          </div>

          {/* Recent Payments */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <h3 className="text-lg font-semibold font-heading text-slate-900 mb-4">Recent Payments</h3>
            {payments.length === 0 ? (
              <p className="text-slate-500 text-sm">No payments recorded</p>
            ) : (
              <div className="space-y-3">
                {payments.slice(0, 5).map((payment) => (
                  <div key={payment.id} className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-sm font-medium text-slate-900">
                          ${payment.amount.toFixed(2)}
                        </p>
                        <p className="text-xs text-slate-500">{payment.payment_method}</p>
                      </div>
                      <p className="text-xs text-slate-500">{payment.payment_date}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TenantDetail;
