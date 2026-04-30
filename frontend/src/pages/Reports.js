import React, { useState } from 'react';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { FileText, Download, BarChart3 } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const Reports = () => {
  const [reportType, setReportType] = useState('monthly');
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);

  const generateReport = async () => {
    setLoading(true);
    try {
      const { data } = await axios.get(`${API}/reports/generate?report_type=${reportType}`, { withCredentials: true });
      setReportData(data);
    } catch { alert('Errore nella generazione'); }
    setLoading(false);
  };

  const downloadPDF = async () => {
    try {
      const response = await axios.get(`${API}/reports/pdf?report_type=${reportType}`, {
        withCredentials: true, responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `report_${reportType}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch { alert('Errore download PDF'); }
  };

  const s = reportData?.summary;

  return (
    <div data-testid="reports-page" className="luxury-fade-in">
      <div className="mb-10">
        <h1 className="luxury-title mb-2">Report</h1>
        <p className="luxury-subtitle">Genera report finanziari e operativi</p>
      </div>

      <div className="luxury-card p-6 mb-6">
        <div className="flex items-center gap-4 flex-wrap">
          <Select value={reportType} onValueChange={setReportType}>
            <SelectTrigger className="w-[200px]"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="weekly">Settimanale</SelectItem>
              <SelectItem value="monthly">Mensile</SelectItem>
              <SelectItem value="yearly">Annuale</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={generateReport} disabled={loading} className="btn-luxury">
            {loading ? 'Generazione...' : 'Genera Report'}
          </Button>
          {reportData && (
            <Button onClick={downloadPDF} variant="outline" className="rounded-xl" style={{ borderColor: 'rgba(217,42,42,0.2)' }}>
              <Download size={16} className="mr-2" /> Scarica PDF
            </Button>
          )}
        </div>
      </div>

      {reportData && s && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            {[
              { label: 'Pagamenti Ricevuti', value: `\u20ac${s.total_payments_received?.toLocaleString()}`, color: '#059669' },
              { label: 'N. Pagamenti', value: s.payment_count, color: '#2563EB' },
              { label: 'Fatture Non Pagate', value: s.unpaid_invoices, color: '#DC2626' },
              { label: 'Fatture Scadute', value: s.overdue_invoices, color: '#D97706' },
              { label: 'Tasso Occupazione', value: `${s.occupancy_rate}%`, color: '#7C3AED' },
              { label: 'Stanze Occupate', value: s.occupied_rooms, color: '#059669' },
              { label: 'Stanze Libere', value: s.vacant_rooms, color: '#DC2626' },
              { label: 'Pagamenti Parziali', value: s.partial_payments, color: '#D97706' },
            ].map(card => (
              <div key={card.label} className="luxury-card p-5">
                <p className="text-xs uppercase tracking-wide mb-1" style={{ color: '#64748B' }}>{card.label}</p>
                <p className="text-2xl font-bold" style={{ color: card.color }}>{card.value}</p>
              </div>
            ))}
          </div>

          {reportData.tenant_balances?.length > 0 && (
            <div className="luxury-card p-7">
              <h3 className="text-lg font-semibold font-heading mb-4" style={{ color: '#0B8A3E' }}>Saldi Inquilini</h3>
              <div className="space-y-2">
                {reportData.tenant_balances.map((t, i) => (
                  <div key={i} className="flex justify-between py-3 px-4 rounded-xl" style={{ background: 'rgba(250,247,240,0.5)', border: '1px solid rgba(217,42,42,0.08)' }}>
                    <span style={{ color: '#0F172A' }}>{t.name}</span>
                    <span className="font-bold" style={{ color: '#DC2626' }}>&euro;{t.balance?.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {!reportData && !loading && (
        <div className="luxury-card p-14 text-center">
          <BarChart3 className="mx-auto mb-4" size={64} style={{ color: 'rgba(217,42,42,0.3)' }} />
          <h3 className="text-lg font-semibold mb-2" style={{ color: '#0F172A' }}>Nessun Report</h3>
          <p style={{ color: '#64748B' }}>Seleziona un tipo e clicca "Genera Report"</p>
        </div>
      )}
    </div>
  );
};

export default Reports;
