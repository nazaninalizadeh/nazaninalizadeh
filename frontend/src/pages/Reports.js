import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { FileText, Download, TrendingUp, DollarSign, Building2, Users } from 'lucide-react';
import { Button } from '../components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Reports = () => {
  const [reportType, setReportType] = useState('monthly_income');
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);

  const generateReport = async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(
        `${API_URL}/reports/generate`,
        { report_type: reportType },
        { withCredentials: true }
      );
      setReportData(data);
      toast.success('Report generated successfully');
    } catch (error) {
      toast.error('Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  const renderReportContent = () => {
    if (!reportData) return null;

    switch (reportData.report_type) {
      case 'monthly_income':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-green-50 p-6 rounded-lg border border-green-200">
                <div className="flex items-center gap-3 mb-2">
                  <TrendingUp className="text-green-700" size={24} />
                  <p className="text-sm font-semibold text-green-700 uppercase">Total Monthly Income</p>
                </div>
                <p className="text-3xl font-bold text-green-900">
                  ${reportData.total_monthly_income?.toFixed(2)}
                </p>
              </div>
              <div className="bg-blue-50 p-6 rounded-lg border border-rose-200">
                <div className="flex items-center gap-3 mb-2">
                  <FileText className="text-rose-700" size={24} />
                  <p className="text-sm font-semibold text-rose-700 uppercase">Active Contracts</p>
                </div>
                <p className="text-3xl font-bold text-rose-900">{reportData.active_contracts}</p>
              </div>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h3 className="text-lg font-semibold mb-4">Income by Landlord</h3>
              <div className="space-y-3">
                {reportData.landlord_breakdown?.map((landlord, index) => (
                  <div key={index} className="flex justify-between items-center p-4 bg-slate-50 rounded-lg">
                    <div>
                      <p className="font-medium text-slate-900">{landlord.landlord_name}</p>
                      <p className="text-sm text-slate-600">{landlord.properties} properties</p>
                    </div>
                    <p className="text-lg font-semibold text-slate-900">
                      ${landlord.monthly_income?.toFixed(2)}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case 'outstanding_payments':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-red-50 p-6 rounded-lg border border-red-200">
                <div className="flex items-center gap-3 mb-2">
                  <DollarSign className="text-red-700" size={24} />
                  <p className="text-sm font-semibold text-red-700 uppercase">Total Outstanding</p>
                </div>
                <p className="text-3xl font-bold text-red-900">
                  ${reportData.total_outstanding?.toFixed(2)}
                </p>
              </div>
              <div className="bg-orange-50 p-6 rounded-lg border border-orange-200">
                <div className="flex items-center gap-3 mb-2">
                  <FileText className="text-orange-700" size={24} />
                  <p className="text-sm font-semibold text-orange-700 uppercase">Unpaid Invoices</p>
                </div>
                <p className="text-3xl font-bold text-orange-900">{reportData.unpaid_invoices_count}</p>
              </div>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h3 className="text-lg font-semibold mb-4">Outstanding by Tenant</h3>
              <div className="space-y-3">
                {reportData.tenant_breakdown?.map((tenant, index) => (
                  <div key={index} className="flex justify-between items-center p-4 bg-slate-50 rounded-lg">
                    <div>
                      <p className="font-medium text-slate-900">{tenant.tenant_name}</p>
                      <p className="text-sm text-slate-600">{tenant.invoices} unpaid invoices</p>
                    </div>
                    <p className="text-lg font-semibold text-red-600">
                      ${tenant.total_amount?.toFixed(2)}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case 'occupancy':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-blue-50 p-6 rounded-lg border border-rose-200">
                <div className="flex items-center gap-3 mb-2">
                  <Building2 className="text-rose-700" size={24} />
                  <p className="text-sm font-semibold text-rose-700 uppercase">Total Properties</p>
                </div>
                <p className="text-3xl font-bold text-rose-900">{reportData.total_properties}</p>
              </div>
              <div className="bg-green-50 p-6 rounded-lg border border-green-200">
                <div className="flex items-center gap-3 mb-2">
                  <Building2 className="text-green-700" size={24} />
                  <p className="text-sm font-semibold text-green-700 uppercase">Occupied</p>
                </div>
                <p className="text-3xl font-bold text-green-900">{reportData.occupied}</p>
              </div>
              <div className="bg-purple-50 p-6 rounded-lg border border-purple-200">
                <div className="flex items-center gap-3 mb-2">
                  <TrendingUp className="text-purple-700" size={24} />
                  <p className="text-sm font-semibold text-purple-700 uppercase">Occupancy Rate</p>
                </div>
                <p className="text-3xl font-bold text-purple-900">{reportData.occupancy_rate}%</p>
              </div>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h3 className="text-lg font-semibold mb-4">Property Details</h3>
              <div className="space-y-3">
                {reportData.properties_breakdown?.map((property, index) => (
                  <div key={index} className="flex justify-between items-center p-4 bg-slate-50 rounded-lg">
                    <div>
                      <p className="font-medium text-slate-900">{property.property_code}</p>
                      <p className="text-sm text-slate-600">{property.address}</p>
                    </div>
                    <div className="text-right">
                      <span className={`px-2 py-1 rounded-md text-xs font-medium ${
                        property.status === 'occupied' ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-700'
                      }`}>
                        {property.status}
                      </span>
                      <p className="text-sm text-slate-600 mt-1">
                        {property.tenants}/{property.capacity} tenants
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case 'deposit_summary':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-blue-50 p-6 rounded-lg border border-rose-200">
                <div className="flex items-center gap-3 mb-2">
                  <DollarSign className="text-rose-700" size={24} />
                  <p className="text-sm font-semibold text-rose-700 uppercase">Total Deposits</p>
                </div>
                <p className="text-3xl font-bold text-rose-900">
                  ${reportData.total_deposits?.toFixed(2)}
                </p>
              </div>
              <div className="bg-green-50 p-6 rounded-lg border border-green-200">
                <div className="flex items-center gap-3 mb-2">
                  <DollarSign className="text-green-700" size={24} />
                  <p className="text-sm font-semibold text-green-700 uppercase">Total Paid</p>
                </div>
                <p className="text-3xl font-bold text-green-900">
                  ${reportData.total_paid?.toFixed(2)}
                </p>
              </div>
              <div className="bg-orange-50 p-6 rounded-lg border border-orange-200">
                <div className="flex items-center gap-3 mb-2">
                  <DollarSign className="text-orange-700" size={24} />
                  <p className="text-sm font-semibold text-orange-700 uppercase">Outstanding</p>
                </div>
                <p className="text-3xl font-bold text-orange-900">
                  ${reportData.outstanding?.toFixed(2)}
                </p>
              </div>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <div className="flex items-center gap-3">
                <Users className="text-rose-700" size={24} />
                <div>
                  <p className="text-sm font-semibold text-slate-700">Total Tenants</p>
                  <p className="text-2xl font-bold text-slate-900">{reportData.tenant_count}</p>
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div data-testid="reports-page" className="luxury-fade-in">
      <div className="mb-10">
        <h1 className="luxury-title mb-2" data-testid="reports-title">
          Report
        </h1>
        <p className="luxury-subtitle">Genera e visualizza report finanziari e operativi</p>
      </div>

      <div className="luxury-card p-6 mb-6">
        <div className="flex items-end gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-slate-700 mb-2">Report Type</label>
            <Select value={reportType} onValueChange={setReportType}>
              <SelectTrigger data-testid="report-type-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="monthly_income">Monthly Income Report</SelectItem>
                <SelectItem value="outstanding_payments">Outstanding Payments</SelectItem>
                <SelectItem value="occupancy">Occupancy Report</SelectItem>
                <SelectItem value="deposit_summary">Deposit Summary</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Button
            onClick={generateReport}
            disabled={loading}
            className="bg-rose-700 hover:bg-rose-800"
            data-testid="generate-report-button"
          >
            {loading ? 'Generating...' : 'Generate Report'}
          </Button>
        </div>
      </div>

      {reportData && (
        <div className="space-y-6">
          <div className="luxury-card p-6">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-xl font-semibold font-heading" style={{ color: '#9F1239' }}>
                  {reportType.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                </h2>
                <p className="text-sm text-slate-600 mt-1">
                  Generated on: {new Date(reportData.generated_at).toLocaleString()}
                </p>
              </div>
            </div>

            {renderReportContent()}
          </div>
        </div>
      )}

      {!reportData && !loading && (
        <div className="luxury-card p-14 text-center">
          <FileText className="mx-auto mb-4" size={64} style={{ color: 'rgba(184, 134, 11, 0.3)' }} />
          <h3 className="text-lg font-semibold mb-2" style={{ color: '#2C1810' }}>Nessun Report Generato</h3>
          <p style={{ color: '#8B7355' }}>Seleziona un tipo di report e clicca "Genera Report" per visualizzare i dati</p>
        </div>
      )}
    </div>
  );
};

export default Reports;
