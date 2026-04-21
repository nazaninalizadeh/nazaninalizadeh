import React, { useState, useRef } from 'react';
import axios from 'axios';
import { Upload, Download, Sheet, AlertCircle, CheckCircle2, Loader2, X } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const DataExchange = () => {
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [importType, setImportType] = useState('tenants');
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const fileInputRef = useRef(null);

  const handleExport = async (type) => {
    try {
      const response = await axios.get(`${API}/data/export/${type}`, {
        withCredentials: true,
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `${type}_export.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success('File esportato con successo');
    } catch (err) {
      toast.error('Errore durante l\'esportazione');
    }
  };

  const handleTemplate = async (type) => {
    try {
      const response = await axios.get(`${API}/data/templates/${type}`, {
        withCredentials: true,
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `template_${type}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success('Template scaricato');
    } catch (err) {
      toast.error('Errore nel download del template');
    }
  };

  const handleImport = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const allowed = ['.xlsx', '.xls', '.csv'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!allowed.includes(ext)) {
      toast.error('Formato non supportato. Usa .xlsx o .csv');
      return;
    }

    setImporting(true);
    setImportResult(null);

    const fd = new FormData();
    fd.append('file', file);

    try {
      const { data } = await axios.post(`${API}/data/import/${importType}`, fd, { withCredentials: true });
      setImportResult(data);
      if (data.success_count > 0) {
        toast.success(data.message);
      } else if (data.error_count > 0) {
        toast.error('Importazione con errori');
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore durante l\'importazione');
    }
    setImporting(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const openImport = (type) => {
    setImportType(type);
    setImportResult(null);
    setImportDialogOpen(true);
  };

  const sections = [
    {
      title: 'Inquilini',
      icon: <Sheet size={22} style={{ color: '#9F1239' }} />,
      description: 'Importa ed esporta dati degli inquilini',
      actions: [
        { label: 'Esporta Inquilini', icon: <Download size={15} />, onClick: () => handleExport('tenants'), variant: 'export' },
        { label: 'Importa Inquilini', icon: <Upload size={15} />, onClick: () => openImport('tenants'), variant: 'import' },
        { label: 'Scarica Template', icon: <Download size={15} />, onClick: () => handleTemplate('tenants'), variant: 'template' },
      ],
    },
    {
      title: 'Pagamenti',
      icon: <Sheet size={22} style={{ color: '#059669' }} />,
      description: 'Importa ed esporta registrazioni pagamenti',
      actions: [
        { label: 'Esporta Pagamenti', icon: <Download size={15} />, onClick: () => handleExport('payments'), variant: 'export' },
        { label: 'Importa Pagamenti', icon: <Upload size={15} />, onClick: () => openImport('payments'), variant: 'import' },
        { label: 'Scarica Template', icon: <Download size={15} />, onClick: () => handleTemplate('payments'), variant: 'template' },
      ],
    },
    {
      title: 'Occupazione',
      icon: <Sheet size={22} style={{ color: '#B8860B' }} />,
      description: 'Esporta dati occupazione immobili e stanze',
      actions: [
        { label: 'Esporta Occupazione', icon: <Download size={15} />, onClick: () => handleExport('occupancy'), variant: 'export' },
      ],
    },
  ];

  const variantStyles = {
    export: { background: 'linear-gradient(135deg, #9F1239 0%, #BE123C 100%)', color: 'white' },
    import: { background: 'rgba(5,150,105,0.1)', color: '#059669', border: '1px solid rgba(5,150,105,0.3)' },
    template: { background: 'rgba(184,134,11,0.08)', color: '#8B7355', border: '1px solid rgba(184,134,11,0.2)' },
  };

  return (
    <div data-testid="data-exchange-page" className="luxury-fade-in">
      <div className="mb-8">
        <h1 className="luxury-title mb-2" data-testid="data-exchange-title">Gestione Dati</h1>
        <p className="luxury-subtitle">Importa ed esporta dati in formato Excel e CSV</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {sections.map((section) => (
          <div key={section.title} className="luxury-card p-6">
            <div className="flex items-center gap-3 mb-4">
              {section.icon}
              <div>
                <h3 className="font-semibold" style={{ color: '#2C1810' }}>{section.title}</h3>
                <p className="text-xs" style={{ color: '#8B7355' }}>{section.description}</p>
              </div>
            </div>
            <div className="space-y-2">
              {section.actions.map((action) => (
                <button
                  key={action.label}
                  onClick={action.onClick}
                  className="w-full flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all hover:shadow-md"
                  style={variantStyles[action.variant]}
                  data-testid={`${action.variant}-${section.title.toLowerCase()}-btn`}
                >
                  {action.icon}
                  {action.label}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Import Dialog */}
      <Dialog open={importDialogOpen} onOpenChange={setImportDialogOpen}>
        <DialogContent className="max-w-lg luxury-modal">
          <DialogHeader>
            <DialogTitle>
              Importa {importType === 'tenants' ? 'Inquilini' : 'Pagamenti'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="p-4 rounded-xl" style={{ background: 'rgba(184,134,11,0.04)', border: '1px solid rgba(184,134,11,0.1)' }}>
              <p className="text-sm" style={{ color: '#4A3B31' }}>
                Carica un file Excel (.xlsx) o CSV (.csv) con i dati da importare.
                Puoi scaricare il template di esempio per la struttura corretta.
              </p>
            </div>

            <div className="flex gap-3">
              <Button
                variant="outline"
                className="rounded-xl flex-1"
                onClick={() => handleTemplate(importType)}
              >
                <Download size={15} className="mr-2" />
                Scarica Template
              </Button>
              <label className="flex-1">
                <input
                  type="file"
                  ref={fileInputRef}
                  className="hidden"
                  accept=".xlsx,.xls,.csv"
                  onChange={handleImport}
                />
                <span className="btn-luxury rounded-xl flex items-center justify-center gap-2 px-4 py-2 text-sm cursor-pointer w-full h-9">
                  {importing ? <Loader2 size={15} className="animate-spin" /> : <Upload size={15} />}
                  {importing ? 'Importazione...' : 'Carica File'}
                </span>
              </label>
            </div>

            {/* Import Result */}
            {importResult && (
              <div className="space-y-3">
                <div className="flex items-center gap-3 p-3 rounded-xl" style={{
                  background: importResult.success_count > 0 ? 'rgba(5,150,105,0.05)' : 'rgba(220,38,38,0.05)',
                  border: `1px solid ${importResult.success_count > 0 ? 'rgba(5,150,105,0.2)' : 'rgba(220,38,38,0.2)'}`,
                }}>
                  {importResult.success_count > 0 ?
                    <CheckCircle2 size={18} style={{ color: '#059669' }} /> :
                    <AlertCircle size={18} style={{ color: '#DC2626' }} />
                  }
                  <span className="text-sm font-medium" style={{ color: importResult.success_count > 0 ? '#059669' : '#DC2626' }}>
                    {importResult.message}
                  </span>
                </div>

                {importResult.errors?.length > 0 && (
                  <div className="max-h-48 overflow-y-auto space-y-1">
                    <p className="text-xs font-semibold" style={{ color: '#DC2626' }}>Errori:</p>
                    {importResult.errors.map((err, i) => (
                      <div key={i} className="flex items-start gap-2 p-2 rounded-lg text-xs" style={{ background: 'rgba(220,38,38,0.03)' }}>
                        <X size={12} className="text-red-400 mt-0.5 shrink-0" />
                        <span style={{ color: '#4A3B31' }}>
                          <strong>Riga {err.row}:</strong> {err.error}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DataExchange;
