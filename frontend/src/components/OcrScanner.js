import React, { useState, useRef } from 'react';
import axios from 'axios';
import { ScanLine, Loader2, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const OcrScanner = ({ onDataExtracted }) => {
  const [open, setOpen] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, processing, completed, failed
  const [preview, setPreview] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const fileInputRef = useRef(null);

  const handleFileSelect = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const allowed = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg', 'application/pdf'];
    if (!allowed.includes(file.type)) {
      toast.error('Formato non supportato. Usa JPEG, PNG, WebP o PDF.');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      toast.error('File troppo grande. Massimo 10MB.');
      return;
    }

    // PDFs cannot be previewed inline easily — show a placeholder
    setPreview(file.type === 'application/pdf' ? null : URL.createObjectURL(file));
    setOpen(true);
    setScanning(true);
    setStatus('processing');
    setResult(null);
    setErrorMsg('');

    const fd = new FormData();
    fd.append('file', file);

    try {
      const { data } = await axios.post(`${API}/ocr/scan`, fd, { withCredentials: true });

      if (data.status === 'completed' && data.extracted_data) {
        setResult(data.extracted_data);
        setStatus('completed');
        toast.success('Documento scansionato con successo!');
      } else {
        setStatus('failed');
        setErrorMsg(data.error || 'Scansione fallita');
        toast.error(data.error || 'Scansione fallita');
      }
    } catch (err) {
      setStatus('failed');
      const msg = err.response?.data?.detail || 'Errore durante la scansione';
      setErrorMsg(msg);
      toast.error(msg);
    }
    setScanning(false);
  };

  const handleApply = () => {
    if (result && onDataExtracted) {
      onDataExtracted({
        full_name: result.full_name || '',
        // Also pass surname/name (split by first space) so forms with separate fields can use them.
        surname: result.full_name ? result.full_name.split(' ')[0] : '',
        name: result.full_name ? result.full_name.split(' ').slice(1).join(' ') : '',
        passport_number: result.passport_number || '',
        nationality: result.nationality || '',
        date_of_birth: result.date_of_birth || '',
        place_of_birth: result.place_of_birth || '',
        country_of_birth: result.country_of_birth || '',
        passport_issue_date: result.issue_date || '',
        passport_expiry_date: result.expiry_date || '',
        codice_fiscale: result.codice_fiscale || '',
        id_type: result.document_type === 'id_card' ? "Carta d'identita" : result.document_type === 'passport' ? 'Passaporto' : '',
        id_number: result.document_type !== 'passport' ? result.passport_number || '' : '',
      });
      toast.success('Dati applicati al modulo');
    }
    setOpen(false);
    setResult(null);
    setStatus('idle');
    setPreview(null);
  };

  const handleClose = () => {
    setOpen(false);
    setResult(null);
    setStatus('idle');
    setPreview(null);
  };

  const fieldLabels = {
    full_name: 'Nome Completo',
    passport_number: 'N. Documento',
    nationality: 'Nazionalita',
    date_of_birth: 'Data di Nascita',
    gender: 'Sesso',
    place_of_birth: 'Luogo di Nascita',
    issue_date: 'Data Rilascio',
    expiry_date: 'Data Scadenza',
    document_type: 'Tipo Documento',
    issuing_authority: 'Autorita Emittente',
    codice_fiscale: 'Codice Fiscale',
    confidence: 'Affidabilita',
  };

  return (
    <>
      <label data-testid="ocr-scan-button">
        <input
          type="file"
          ref={fileInputRef}
          className="hidden"
          accept="image/jpeg,image/png,image/webp,application/pdf"
          onChange={handleFileSelect}
        />
        <span className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm cursor-pointer transition-all hover:shadow-md"
          style={{
            background: 'linear-gradient(135deg, #9F1239 0%, #BE123C 100%)',
            color: 'white',
          }}>
          <ScanLine size={16} />
          Scansiona Documento (OCR)
        </span>
      </label>

      <Dialog open={open} onOpenChange={handleClose}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto luxury-modal">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ScanLine size={20} style={{ color: '#9F1239' }} />
              Scansione OCR Documento
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            {/* Preview */}
            {preview && (
              <div className="rounded-xl overflow-hidden border" style={{ borderColor: 'rgba(184,134,11,0.15)' }}>
                <img src={preview} alt="Document preview" className="w-full max-h-64 object-contain bg-gray-50" />
              </div>
            )}

            {/* Status */}
            <div className="flex items-center gap-3 p-4 rounded-xl" style={{
              background: status === 'processing' ? 'rgba(184,134,11,0.05)' :
                status === 'completed' ? 'rgba(5,150,105,0.05)' :
                  status === 'failed' ? 'rgba(220,38,38,0.05)' : 'transparent'
            }}>
              {status === 'processing' && (
                <>
                  <Loader2 size={20} className="animate-spin" style={{ color: '#B8860B' }} />
                  <span style={{ color: '#8B7355' }}>Analisi del documento in corso...</span>
                </>
              )}
              {status === 'completed' && (
                <>
                  <CheckCircle2 size={20} style={{ color: '#059669' }} />
                  <span style={{ color: '#059669' }}>Scansione completata - Controlla i dati estratti</span>
                </>
              )}
              {status === 'failed' && (
                <>
                  <XCircle size={20} style={{ color: '#DC2626' }} />
                  <span style={{ color: '#DC2626' }}>{errorMsg || 'Scansione fallita - Riprova con un\'immagine piu chiara'}</span>
                </>
              )}
            </div>

            {/* Extracted Data */}
            {result && (
              <div className="space-y-2">
                <h4 className="text-sm font-semibold" style={{ color: '#4A3B31' }}>Dati Estratti:</h4>
                {result.confidence && result.confidence !== 'high' && (
                  <div className="flex items-center gap-2 p-2 rounded-lg" style={{ background: 'rgba(217,119,6,0.08)' }}>
                    <AlertTriangle size={14} style={{ color: '#D97706' }} />
                    <span className="text-xs" style={{ color: '#D97706' }}>
                      Affidabilita: {result.confidence === 'medium' ? 'Media' : 'Bassa'} - Verifica i dati prima di salvare
                    </span>
                  </div>
                )}
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(result).map(([key, value]) => {
                    if (!value || key === 'confidence') return null;
                    return (
                      <div key={key} className="p-2 rounded-lg" style={{ background: 'rgba(250,247,240,0.5)', border: '1px solid rgba(184,134,11,0.1)' }}>
                        <p className="text-[10px] uppercase tracking-wide" style={{ color: '#8B7355' }}>
                          {fieldLabels[key] || key}
                        </p>
                        <p className="text-sm font-medium" style={{ color: '#2C1810' }}>{value}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-2">
              <Button variant="outline" onClick={handleClose} className="rounded-xl">Chiudi</Button>
              {status === 'completed' && result && (
                <Button onClick={handleApply} className="btn-luxury" data-testid="ocr-apply-button">
                  Applica Dati al Modulo
                </Button>
              )}
              {status === 'failed' && (
                <Button onClick={() => fileInputRef.current?.click()} className="btn-luxury">
                  Riprova
                </Button>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default OcrScanner;
