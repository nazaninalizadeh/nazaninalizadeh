import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { Plus, Search, Eye, Edit, Trash2, ScanLine, Upload } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';

import { Combobox } from '../components/Combobox';
import { COUNTRIES } from '../lib/it_dictionaries';
import { ITALIAN_CITIES } from '../lib/it_cities';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Landlords = () => {
  const [landlords, setLandlords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingLandlord, setEditingLandlord] = useState(null);
  const [formData, setFormData] = useState({
    surname: '', name: '', codice_fiscale: '', phone: '', email: '',
    id_type: '', id_number: '', bank_details: '', notes: '',
    date_of_birth: '', place_of_birth: '', province_of_birth: '', country_of_birth: 'Italia',
    residence: '', signature_url: '',
  });
  const ocrRef = useRef(null);
  const ownerDocRef = useRef(null);
  const sigRef = useRef(null);

  const handleOwnerOcr = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    try {
      toast.info('Scansione documento proprietario...');
      const { data } = await axios.post(`${API_URL}/ocr/scan`, fd, { withCredentials: true });
      if (data.status === 'completed' && data.extracted_data) {
        const d = data.extracted_data;
        // Use OCR's explicit surname / name when present, never swap.
        const surname = d.surname || (d.full_name ? d.full_name.split(' ')[0] : '');
        const name = d.name || (d.full_name ? d.full_name.split(' ').slice(1).join(' ') : '');
        setFormData(prev => ({
          ...prev,
          surname: surname || prev.surname,
          name: name || prev.name,
          codice_fiscale: d.codice_fiscale || prev.codice_fiscale,
          id_number: d.passport_number || prev.id_number,
          id_type: d.document_type === 'passport' ? 'Passaporto' : d.document_type === 'id_card' ? "Carta d'identita" : prev.id_type,
          date_of_birth: d.date_of_birth || prev.date_of_birth,
          place_of_birth: d.place_of_birth || prev.place_of_birth,
          province_of_birth: d.province_of_birth || prev.province_of_birth,
          country_of_birth: d.country_of_birth || prev.country_of_birth || 'Italia',
          residence: d.residence || prev.residence,
        }));
        toast.success('Dati estratti dal documento!');
      } else {
        toast.error(data.error || 'Scansione fallita');
      }
    } catch (err) { toast.error('Errore OCR: ' + (err.response?.data?.detail || err.message)); }
    if (ocrRef.current) ocrRef.current.value = '';
  };

  const handleSignatureUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const allowed = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
    if (!allowed.includes(file.type)) { toast.error('Solo PNG/JPG/WEBP'); return; }
    if (file.size > 5 * 1024 * 1024) { toast.error('Max 5MB'); return; }
    const fd = new FormData();
    fd.append('file', file);
    fd.append('transparent', 'true');  // Ask backend to attempt background removal
    try {
      const { data } = await axios.post(`${API_URL}/landlords/signature`, fd, { withCredentials: true });
      setFormData(prev => ({ ...prev, signature_url: data.url }));
      toast.success('Firma caricata');
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore upload firma'); }
    if (sigRef.current) sigRef.current.value = '';
  };

  const handleOwnerDocUpload = async (e, landlordId) => {
    const file = e.target.files[0];
    if (!file || !landlordId) return;
    const fd = new FormData();
    fd.append('owner_id', landlordId);
    fd.append('file', file);
    try {
      await axios.post(`${API_URL}/owner-documents/upload`, fd, { withCredentials: true });
      toast.success('Documento proprietario caricato');
    } catch { toast.error('Errore upload'); }
    if (ownerDocRef.current) ownerDocRef.current.value = '';
  };

  useEffect(() => { fetchLandlords(); }, []);

  const fetchLandlords = async () => {
    try {
      const { data } = await axios.get(`${API_URL}/landlords`, { withCredentials: true });
      setLandlords(data);
    } catch { toast.error('Errore'); }
    setLoading(false);
  };

  const resetForm = () => {
    setFormData({ surname: '', name: '', codice_fiscale: '', phone: '', email: '', id_type: '', id_number: '', bank_details: '', notes: '', date_of_birth: '', place_of_birth: '', province_of_birth: '', country_of_birth: 'Italia', residence: '', signature_url: '' });
    setEditingLandlord(null);
  };

  const openEditDialog = (ll) => {
    setEditingLandlord(ll);
    const [surname = '', ...nameParts] = (ll.full_name || '').split(' ');
    setFormData({
      surname: ll.surname || surname, name: ll.name || nameParts.join(' '),
      codice_fiscale: ll.codice_fiscale || '',
      phone: ll.phone || '', email: ll.email || '',
      id_type: ll.id_type || '', id_number: ll.id_number || '',
      bank_details: ll.bank_details || '', notes: ll.notes || '',
      date_of_birth: ll.date_of_birth || '',
      place_of_birth: ll.place_of_birth || '',
      province_of_birth: ll.province_of_birth || '',
      country_of_birth: ll.country_of_birth || 'Italia',
      residence: ll.residence || '',
      signature_url: ll.signature_url || '',
    });
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = { ...formData, full_name: `${formData.surname} ${formData.name}`.trim() };
      if (editingLandlord) {
        await axios.put(`${API_URL}/landlords/${editingLandlord.id}`, payload, { withCredentials: true });
        toast.success('Proprietario aggiornato');
      } else {
        await axios.post(`${API_URL}/landlords`, payload, { withCredentials: true });
        toast.success('Proprietario creato');
      }
      setDialogOpen(false); resetForm(); fetchLandlords();
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore'); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Eliminare?')) return;
    try {
      await axios.delete(`${API_URL}/landlords/${id}`, { withCredentials: true });
      toast.success('Eliminato');
      fetchLandlords();
    } catch { toast.error('Errore'); }
  };

  const filtered = landlords.filter(l =>
    l.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    l.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    l.codice_fiscale?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div data-testid="landlords-page" className="luxury-fade-in">
      <div className="mb-10 flex items-center justify-between">
        <div>
          <h1 className="luxury-title mb-2">Proprietari</h1>
          <p className="luxury-subtitle">Gestisci proprietari, immobili e occupazione</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(o) => { setDialogOpen(o); if (!o) resetForm(); }}>
          <DialogTrigger asChild><Button className="btn-luxury"><Plus size={18} className="mr-2" />Aggiungi Proprietario</Button></DialogTrigger>
          <DialogContent className="max-w-2xl luxury-modal">
            <DialogHeader><DialogTitle>{editingLandlord ? 'Modifica' : 'Nuovo'} Proprietario</DialogTitle></DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* OCR for owner */}
              <div className="pb-3 mb-2" style={{ borderBottom: '1px solid rgba(184,134,11,0.12)' }}>
                <label data-testid="owner-ocr-button">
                  <input type="file" ref={ocrRef} className="hidden" accept="image/jpeg,image/png,image/webp,application/pdf" onChange={handleOwnerOcr} />
                  <span className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm cursor-pointer hover:shadow-md" style={{ background: '#9F1239', color: 'white' }}>
                    <ScanLine size={16} /> Scansiona Documento (OCR)
                  </span>
                </label>
                <p className="text-xs mt-2" style={{ color: '#8B7355' }}>Scansiona documento del proprietario per compilare automaticamente</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div><Label>Cognome *</Label><Input value={formData.surname} onChange={e => setFormData({ ...formData, surname: e.target.value })} required className="luxury-input" data-testid="owner-surname-input" /></div>
                <div><Label>Nome *</Label><Input value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} required className="luxury-input" data-testid="owner-name-input" /></div>
                <div><Label>Codice Fiscale</Label><Input value={formData.codice_fiscale} onChange={e => setFormData({ ...formData, codice_fiscale: e.target.value })} className="luxury-input" /></div>
                <div><Label>Tipo Doc. ID</Label><Input value={formData.id_type} onChange={e => setFormData({ ...formData, id_type: e.target.value })} className="luxury-input" placeholder="Carta d'identita..." /></div>
                <div><Label>Numero Documento *</Label><Input value={formData.id_number} onChange={e => setFormData({ ...formData, id_number: e.target.value })} required className="luxury-input" /></div>
                <div><Label>Data di Nascita</Label><Input type="date" value={formData.date_of_birth} onChange={e => setFormData({ ...formData, date_of_birth: e.target.value })} className="luxury-input" /></div>
                <div>
                  <Label>Luogo di Nascita</Label>
                  <Combobox
                    options={ITALIAN_CITIES}
                    value={formData.place_of_birth}
                    onChange={v => {
                      // When a city from the IT list is picked, auto-fill the province sigla.
                      const match = ITALIAN_CITIES.find(([c]) => c.toLowerCase() === v.toLowerCase());
                      setFormData({ ...formData, place_of_birth: v, province_of_birth: match ? match[1] : formData.province_of_birth });
                    }}
                    placeholder="Es: Padova, Roma..."
                    dataTestid="owner-place-of-birth"
                  />
                </div>
                <div><Label>Provincia di Nascita</Label><Input value={formData.province_of_birth} onChange={e => setFormData({ ...formData, province_of_birth: e.target.value.toUpperCase() })} className="luxury-input" placeholder="PD" maxLength={2} /></div>
                <div>
                  <Label>Paese di Nascita</Label>
                  <Combobox options={COUNTRIES} value={formData.country_of_birth} onChange={v => setFormData({ ...formData, country_of_birth: v })} placeholder="Es: Italia..." />
                </div>
                <div><Label>Telefono *</Label><Input value={formData.phone} onChange={e => setFormData({ ...formData, phone: e.target.value })} required className="luxury-input" data-testid="owner-phone-input" /></div>
                <div><Label>Email *</Label><Input type="email" value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })} required className="luxury-input" /></div>
                <div className="col-span-2"><Label>Indirizzo di Residenza</Label><Input value={formData.residence} onChange={e => setFormData({ ...formData, residence: e.target.value })} className="luxury-input" placeholder="Via, civico, città, provincia, CAP" /></div>
                <div className="col-span-2"><Label>Dati Bancari *</Label><Input value={formData.bank_details} onChange={e => setFormData({ ...formData, bank_details: e.target.value })} required className="luxury-input" /></div>
              </div>

              {/* Signature upload */}
              <div className="pt-3 mt-2" style={{ borderTop: '1px solid rgba(184,134,11,0.12)' }}>
                <Label>Firma del Proprietario</Label>
                <div className="flex items-center gap-3 mt-1">
                  <label>
                    <input type="file" ref={sigRef} className="hidden" accept="image/png,image/jpeg,image/jpg,image/webp" onChange={handleSignatureUpload} data-testid="owner-signature-upload" />
                    <span className="inline-flex items-center gap-2 px-3 py-2 rounded-lg text-xs cursor-pointer hover:shadow-sm" style={{ background: 'rgba(184,134,11,0.08)', color: '#8B7355' }}>
                      <Upload size={14} /> Carica firma (PNG transparente)
                    </span>
                  </label>
                  {formData.signature_url && (
                    <img src={`${process.env.REACT_APP_BACKEND_URL}${formData.signature_url}`} alt="Firma" className="h-12 max-w-[200px] object-contain" style={{ background: 'rgba(0,0,0,0.03)', borderRadius: 6 }} />
                  )}
                </div>
                <p className="text-xs mt-1" style={{ color: '#8B7355' }}>Verrà usata in Hospitality e contratti. Lo sfondo bianco viene rimosso automaticamente.</p>
              </div>
              <div><Label>Note</Label><Input value={formData.notes} onChange={e => setFormData({ ...formData, notes: e.target.value })} className="luxury-input notes-text" /></div>
              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="rounded-xl">Annulla</Button>
                <Button type="submit" className="btn-luxury">{editingLandlord ? 'Aggiorna' : 'Crea'}</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="luxury-card overflow-hidden">
        <div className="p-5" style={{ borderBottom: '1px solid rgba(184,134,11,0.12)' }}>
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2" size={18} style={{ color: '#B8860B' }} />
            <Input placeholder="Cerca proprietario..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="pl-11 luxury-input" />
          </div>
        </div>
        {loading ? (
          <div className="flex items-center justify-center p-12"><div className="luxury-spinner h-10 w-10" /></div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow style={{ background: 'linear-gradient(135deg, #9F1239 0%, #BE123C 100%)' }}>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Nome</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Codice Fiscale</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Email</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Immobili</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Stanze Occ./Tot.</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider">Libere</TableHead>
                <TableHead className="text-white font-semibold text-xs uppercase tracking-wider text-right">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.length === 0 ? (
                <TableRow><TableCell colSpan={7} className="text-center py-10" style={{ color: '#8B7355' }}>Nessun proprietario</TableCell></TableRow>
              ) : filtered.map(ll => (
                <TableRow key={ll.id} className="hover:bg-rose-50/30 transition-colors">
                  <TableCell className="font-medium" style={{ color: '#2C1810' }}>{ll.full_name}</TableCell>
                  <TableCell className="font-mono text-xs" style={{ color: '#4A3B31' }}>{ll.codice_fiscale || '-'}</TableCell>
                  <TableCell style={{ color: '#4A3B31' }}>{ll.email}</TableCell>
                  <TableCell className="font-medium" style={{ color: '#2C1810' }}>{ll.properties_count}</TableCell>
                  <TableCell>
                    <span style={{ color: '#059669' }}>{ll.occupied_rooms || 0}</span>/<span style={{ color: '#2C1810' }}>{ll.total_rooms || 0}</span>
                  </TableCell>
                  <TableCell>
                    <span className="font-bold" style={{ color: (ll.vacant_rooms || 0) > 0 ? '#DC2626' : '#059669' }}>{ll.vacant_rooms || 0}</span>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      <Link to={`/landlords/${ll.id}`}><Button variant="ghost" size="sm" className="rounded-lg hover:bg-rose-50"><Eye size={16} style={{ color: '#9F1239' }} /></Button></Link>
                      <label className="cursor-pointer">
                        <input type="file" className="hidden" onChange={e => handleOwnerDocUpload(e, ll.id)} accept=".pdf,.jpg,.jpeg,.png" />
                        <span className="inline-flex items-center justify-center rounded-lg h-8 w-8 hover:bg-emerald-50 transition-colors"><Upload size={16} style={{ color: '#059669' }} /></span>
                      </label>
                      <Button variant="ghost" size="sm" className="rounded-lg hover:bg-amber-50" onClick={() => openEditDialog(ll)}><Edit size={16} style={{ color: '#B8860B' }} /></Button>
                      <Button variant="ghost" size="sm" className="rounded-lg hover:bg-red-50" onClick={() => handleDelete(ll.id)}><Trash2 size={16} className="text-red-500" /></Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
};

export default Landlords;
