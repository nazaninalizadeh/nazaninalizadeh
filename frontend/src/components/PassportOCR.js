import React, { useState, useRef } from 'react';
import axios from 'axios';
import { Upload, FileText, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const PassportOCR = ({ onExtracted }) => {
  const [loading, setLoading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileSelect = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Show preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreviewUrl(reader.result);
    };
    reader.readAsDataURL(file);

    // Upload and extract
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const { data } = await axios.post(
        `${API_URL}/tenants/extract-passport`,
        formData,
        {
          withCredentials: true,
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      toast.success('Passport information extracted successfully!');
      if (onExtracted) {
        onExtracted(data);
      }
    } catch (error) {
      toast.error('Failed to extract passport information');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4" data-testid="passport-ocr-component">
      <div>
        <Label>Upload Passport Image</Label>
        <div
          className="mt-2 border-2 border-dashed border-slate-300 rounded-lg p-6 text-center cursor-pointer hover:border-blue-500 transition-colors"
          onClick={() => fileInputRef.current?.click()}
        >
          {previewUrl ? (
            <div className="space-y-3">
              <img
                src={previewUrl}
                alt="Passport preview"
                className="max-h-48 mx-auto rounded-lg"
              />
              {loading && (
                <div className="flex items-center justify-center gap-2 text-rose-700">
                  <Loader2 className="animate-spin" size={20} />
                  <span>Extracting information...</span>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              <Upload className="mx-auto text-slate-400" size={48} />
              <div>
                <p className="text-sm font-medium text-slate-700">Click to upload passport image</p>
                <p className="text-xs text-slate-500 mt-1">PNG, JPG, JPEG up to 10MB</p>
              </div>
            </div>
          )}
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          className="hidden"
          data-testid="passport-file-input"
        />
      </div>

      {loading && (
        <div className="p-4 bg-blue-50 rounded-lg border border-rose-200">
          <div className="flex items-center gap-3">
            <FileText className="text-rose-700" size={20} />
            <div>
              <p className="text-sm font-medium text-rose-900">Processing Passport</p>
              <p className="text-xs text-rose-700">Using AI to extract information...</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PassportOCR;
