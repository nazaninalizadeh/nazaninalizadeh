import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Mail, Phone, Building2, DollarSign } from 'lucide-react';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const LandlordDetail = () => {
  const { id } = useParams();
  const [landlord, setLandlord] = useState(null);
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLandlordDetails();
  }, [id]);

  const fetchLandlordDetails = async () => {
    try {
      const [landlordRes, propertiesRes] = await Promise.all([
        axios.get(`${API_URL}/landlords/${id}`, { withCredentials: true }),
        axios.get(`${API_URL}/properties`, { withCredentials: true }),
      ]);

      setLandlord(landlordRes.data);
      setProperties(propertiesRes.data.filter(p => p.landlord_id === id));
    } catch (error) {
      toast.error('Failed to load landlord details');
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

  if (!landlord) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-600">Landlord not found</p>
        <Link to="/landlords">
          <Button className="mt-4">Back to Landlords</Button>
        </Link>
      </div>
    );
  }

  const totalMonthlyIncome = properties.reduce((sum, p) => sum + p.rental_amount, 0);

  return (
    <div data-testid="landlord-detail-page">
      <Link to="/landlords">
        <Button variant="ghost" className="mb-6" data-testid="back-to-landlords">
          <ArrowLeft size={18} className="mr-2" />
          Back to Landlords
        </Button>
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Landlord Profile */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <h2 className="text-2xl font-semibold font-heading text-slate-900 mb-6" data-testid="landlord-name">
              {landlord.full_name}
            </h2>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <p className="text-xs text-slate-500 mb-1">ID Number</p>
                <p className="text-slate-900 font-medium">{landlord.id_number}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1">Bank Details</p>
                <p className="text-slate-900 font-medium">{landlord.bank_details}</p>
              </div>
            </div>

            <div className="mt-6 pt-6 border-t border-slate-200">
              <h3 className="text-sm font-semibold text-slate-900 mb-4">Contact Information</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-3">
                  <Mail size={18} className="text-slate-400" />
                  <span className="text-slate-900">{landlord.email}</span>
                </div>
                <div className="flex items-center gap-3">
                  <Phone size={18} className="text-slate-400" />
                  <span className="text-slate-900">{landlord.phone}</span>
                </div>
                <div className="flex items-center gap-3">
                  <Phone size={18} className="text-slate-400" />
                  <span className="text-slate-900">{landlord.whatsapp} (WhatsApp)</span>
                </div>
              </div>
            </div>

            {landlord.notes && (
              <div className="mt-6 pt-6 border-t border-slate-200">
                <h3 className="text-sm font-semibold text-slate-900 mb-2">Notes</h3>
                <p className="text-slate-600">{landlord.notes}</p>
              </div>
            )}
          </div>

          {/* Properties */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <h3 className="text-lg font-semibold font-heading text-slate-900 mb-4 flex items-center gap-2">
              <Building2 size={20} />
              Properties ({properties.length})
            </h3>
            {properties.length === 0 ? (
              <p className="text-slate-500 text-sm">No properties found</p>
            ) : (
              <div className="space-y-3">
                {properties.map((property) => (
                  <div key={property.id} className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <p className="font-medium text-slate-900">{property.property_code}</p>
                        <p className="text-sm text-slate-600">{property.address}</p>
                      </div>
                      <span className={`px-2 py-1 rounded-md text-xs font-medium ${
                        property.occupancy_status === 'occupied' ? 'bg-green-100 text-green-700' :
                        'bg-slate-100 text-slate-700'
                      }`}>
                        {property.occupancy_status}
                      </span>
                    </div>
                    <div className="grid grid-cols-3 gap-4 mt-3">
                      <div>
                        <p className="text-xs text-slate-500">Type</p>
                        <p className="text-sm text-slate-900">{property.property_type}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500">Tenants</p>
                        <p className="text-sm text-slate-900">{property.current_tenants_count}/{property.capacity}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500">Rent</p>
                        <p className="text-sm font-medium text-slate-900">${property.rental_amount.toFixed(2)}/mo</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Income Summary */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <h3 className="text-lg font-semibold font-heading text-slate-900 mb-6">Income Summary</h3>
            <div className="space-y-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <div className="flex items-center gap-3 mb-2">
                  <Building2 size={18} className="text-rose-700" />
                  <p className="text-xs text-rose-700 font-semibold uppercase">Properties</p>
                </div>
                <p className="text-2xl font-semibold text-rose-900">
                  {properties.length}
                </p>
              </div>

              <div className="p-4 bg-green-50 rounded-lg">
                <div className="flex items-center gap-3 mb-2">
                  <DollarSign size={18} className="text-green-700" />
                  <p className="text-xs text-green-700 font-semibold uppercase">Monthly Income</p>
                </div>
                <p className="text-2xl font-semibold text-green-900">
                  ${totalMonthlyIncome.toFixed(2)}
                </p>
              </div>

              <div className="p-4 bg-purple-50 rounded-lg">
                <div className="flex items-center gap-3 mb-2">
                  <Building2 size={18} className="text-purple-700" />
                  <p className="text-xs text-purple-700 font-semibold uppercase">Occupied</p>
                </div>
                <p className="text-2xl font-semibold text-purple-900">
                  {properties.filter(p => p.occupancy_status === 'occupied').length}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LandlordDetail;
