import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Plus, Download, Trash2, Receipt } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { toast } from 'sonner';
import { fmtDate } from '../lib/format';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const Preavviso = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(blankForm());

  function blankForm() {
    return {
      recipient_name: '',
      recipient_address: '',
      recipient_cf_piva: '',
      body_text: '',
      due_date: new Date().toISOString().split('T')[0],
      imponibile: 0,
      vat_rate: 22,
      rimborso_label: 'Rimborso spese vostra quota registrazione contratto',
      rimborso_amount: 0,
      rimborso_note: '',
      rimborso_tax_note: '(esente iva art 15)',
    };
  }

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      const { data } = await axios.get(`${API}/invoices`, { withCredentials: true });
      setItems(data.filter((i) => i.document_type === 'preavviso'));
    } catch (err) {
      toast.error('Errore caricamento preavvisi');
    } finally {
      setLoading(false);
    }
  };

  const totalLive = (() => {
    const i = parseFloat(form.imponibile) || 0;
    const v = parseFloat(form.vat_rate) || 0;
    const r = parseFloat(form.rimborso_amount) || 0;
    return i + (i * v / 100) + r;
  })();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        tenant_id: '', property_id: '', contract_id: '',
        invoice_type: 'rent',
        document_type: 'preavviso',
        amount: totalLive,
        due_date: form.due_date,
        description: form.body_text || 'Preavviso fatturazione',
        body_text: form.body_text,
        imponibile: parseFloat(form.imponibile) || 0,
        vat_rate: parseFloat(form.vat_rate) || 0,
        rimborso_label: form.rimborso_label,
        rimborso_amount: parseFloat(form.rimborso_amount) || 0,
        rimborso_note: form.rimborso_note,
        rimborso_tax_note: form.rimborso_tax_note,
        recipient_name: form.recipient_name,
        recipient_address: form.recipient_address,
        recipient_cf_piva: form.recipient_cf_piva,
      };
      await axios.post(`${API}/invoices`, payload, { withCredentials: true });
      toast.success('Preavviso creato');
      setOpen(false);
      setForm(blankForm());
      fetchAll();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore creazione');
    }
  };

  const handleDownload = async (id) => {
    try {
      const r = await axios.get(`${API}/invoices/${id}/pdf`, { responseType: 'blob', withCredentials: true });
      const url = window.URL.createObjectURL(new Blob([r.data], { type: 'application/pdf' }));
      const a = document.createElement('a');
      a.href = url; a.download = `preavviso_${id}.pdf`; a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) { toast.error('Errore download'); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Eliminare questo preavviso?')) return;
    try {
      await axios.delete(`${API}/invoices/${id}`, { withCredentials: true });
      toast.success('Preavviso eliminato');
      fetchAll();
    } catch (err) { toast.error('Errore eliminazione'); }
  };

  if (loading) return <div className="text-center py-12" style={{ color: '#64748B' }}>Caricamento...</div>;

  return (
    <div data-testid="preavviso-page">
      <div className="mb-10 flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="luxury-title text-4xl mb-1" style={{ color: '#0B8A3E' }}>Preavviso di Fatturazione</h1>
          <p className="text-sm" style={{ color: '#64748B' }}>Documenti di preavviso per clienti commerciali</p>
        </div>
        <Dialog open={open} onOpenChange={(o) => { setOpen(o); if (!o) setForm(blankForm()); }}>
          <DialogTrigger asChild>
            <Button className="btn-luxury" data-testid="add-preavviso-button"><Plus size={18} className="mr-2" />Nuovo Preavviso</Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto luxury-modal w-[95vw] sm:w-auto">
            <DialogHeader><DialogTitle>Nuovo Preavviso di Fatturazione</DialogTitle></DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="col-span-1 sm:col-span-2">
                  <Label>Destinatario (Spett.le) *</Label>
                  <Input value={form.recipient_name} onChange={(e) => setForm({ ...form, recipient_name: e.target.value })} required className="luxury-input" placeholder="ELEISON Societa' Cooperativa Sociale" data-testid="preavviso-recipient-name" />
                </div>
                <div>
                  <Label>Indirizzo Destinatario</Label>
                  <Input value={form.recipient_address} onChange={(e) => setForm({ ...form, recipient_address: e.target.value })} className="luxury-input" placeholder="Via Giorgio Pulle' 15/17 Padova" data-testid="preavviso-recipient-address" />
                </div>
                <div>
                  <Label>C.F. / P.IVA</Label>
                  <Input value={form.recipient_cf_piva} onChange={(e) => setForm({ ...form, recipient_cf_piva: e.target.value })} className="luxury-input" placeholder="05028740289" data-testid="preavviso-recipient-cf" />
                </div>
                <div className="col-span-1 sm:col-span-2">
                  <Label>Causale / Descrizione *</Label>
                  <Input value={form.body_text} onChange={(e) => setForm({ ...form, body_text: e.target.value })} required className="luxury-input" placeholder="Ricerca appartamento in locazione situato a Padova Via Mozart" data-testid="preavviso-body" />
                </div>
                <div>
                  <Label>Data Preavviso *</Label>
                  <Input type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} required className="luxury-input" data-testid="preavviso-date" />
                </div>
              </div>
              <div className="rounded-xl p-4 space-y-3" style={{ background: 'rgba(217,42,42,0.04)', border: '1px solid rgba(217,42,42,0.15)' }}>
                <h4 className="text-sm font-semibold" style={{ color: '#0B8A3E' }}>Importi</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div><Label>Imponibile (€)</Label><Input type="number" step="0.01" value={form.imponibile} onChange={(e) => setForm({ ...form, imponibile: parseFloat(e.target.value) || 0 })} className="luxury-input" data-testid="preavviso-imponibile" /></div>
                  <div><Label>IVA (%)</Label><Input type="number" step="1" value={form.vat_rate} onChange={(e) => setForm({ ...form, vat_rate: parseFloat(e.target.value) || 0 })} className="luxury-input" data-testid="preavviso-vat" /></div>
                  <div className="col-span-1 sm:col-span-2"><Label>Voce Rimborso</Label><Input value={form.rimborso_label} onChange={(e) => setForm({ ...form, rimborso_label: e.target.value })} className="luxury-input" data-testid="preavviso-rimborso-label" /></div>
                  <div><Label>Importo Rimborso (€)</Label><Input type="number" step="0.01" value={form.rimborso_amount} onChange={(e) => setForm({ ...form, rimborso_amount: parseFloat(e.target.value) || 0 })} className="luxury-input" data-testid="preavviso-rimborso-amount" /></div>
                  <div><Label>Nota IVA</Label><Input value={form.rimborso_tax_note} onChange={(e) => setForm({ ...form, rimborso_tax_note: e.target.value })} className="luxury-input" data-testid="preavviso-rimborso-tax-note" /></div>
                  <div className="col-span-1 sm:col-span-2"><Label>Nota aggiuntiva</Label><Input value={form.rimborso_note} onChange={(e) => setForm({ ...form, rimborso_note: e.target.value })} className="luxury-input" data-testid="preavviso-rimborso-note" /></div>
                </div>
                <div className="flex items-center justify-between pt-2 border-t" style={{ borderColor: 'rgba(217,42,42,0.15)' }}>
                  <span className="text-sm font-semibold" style={{ color: '#0F172A' }}>TOTALE FATTURA</span>
                  <span className="text-lg font-bold" style={{ color: '#0B8A3E' }} data-testid="preavviso-total">€{totalLive.toFixed(2)}</span>
                </div>
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => { setOpen(false); setForm(blankForm()); }} className="rounded-xl">Annulla</Button>
                <Button type="submit" className="btn-luxury">Crea Preavviso</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="luxury-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Numero</TableHead>
              <TableHead>Destinatario</TableHead>
              <TableHead>Causale</TableHead>
              <TableHead>Data</TableHead>
              <TableHead className="text-right">Totale</TableHead>
              <TableHead className="text-right">Azioni</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.length === 0 ? (
              <TableRow><TableCell colSpan={6} className="text-center py-12" style={{ color: '#64748B' }}>
                <Receipt size={36} className="mx-auto mb-3 opacity-30" />Nessun preavviso. Clicca su "Nuovo Preavviso" per iniziare.
              </TableCell></TableRow>
            ) : items.map((p) => (
              <TableRow key={p.id} data-testid={`preavviso-row-${p.id}`}>
                <TableCell className="font-mono">{p.invoice_number}</TableCell>
                <TableCell className="font-semibold">{p.recipient_name || p.tenant_name}</TableCell>
                <TableCell className="text-sm max-w-[280px] truncate">{p.body_text || p.description}</TableCell>
                <TableCell>{formatItDate(p.due_date || p.issue_date)}</TableCell>
                <TableCell className="text-right font-bold" style={{ color: '#0B8A3E' }}>€{(p.amount || 0).toFixed(2)}</TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-2">
                    <Button size="sm" variant="outline" onClick={() => handleDownload(p.id)} data-testid={`preavviso-download-${p.id}`}><Download size={14} /></Button>
                    <Button size="sm" variant="outline" onClick={() => handleDelete(p.id)} style={{ color: '#0B8A3E', borderColor: '#0B8A3E' }} data-testid={`preavviso-delete-${p.id}`}><Trash2 size={14} /></Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};

export default Preavviso;
