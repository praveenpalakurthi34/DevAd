import React, { useState } from 'react';
import { Sparkles, Upload, Image as ImageIcon } from 'lucide-react';
import type { CampaignCreateData } from '../types';

interface Props {
  onSubmit: (data: CampaignCreateData) => void;
  memoryMode: boolean;
}

const PLATFORMS = ['Instagram Feed', 'Instagram Stories', 'Facebook Feed', 'LinkedIn'];
const OBJECTIVES = ['Conversions', 'Brand Awareness', 'Traffic', 'Engagement', 'Lead Generation', 'App Installs'];
const FORMATS = ['Static image ad', 'Static carousel ad'];

export default function CampaignForm({ onSubmit, memoryMode }: Props) {
  const [productImage, setProductImage] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [form, setForm] = useState<CampaignCreateData>({
    brand: '',
    product: '',
    audience: '',
    platform: 'Instagram Feed',
    objective: 'Conversions',
    offer: '',
    budget: undefined,
    creative_format: 'Static image ad',
    brand_voice: '',
    brief_context: '',
    memory_mode: memoryMode,
    product_image: undefined,
  });

  const handleChange = (field: keyof CampaignCreateData, value: any) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ ...form, product_image: productImage || undefined, memory_mode: memoryMode });
  };

  const canSubmit = Boolean(form.brand && form.product && form.audience && form.platform && form.objective && form.creative_format && productImage);

  return (
    <form onSubmit={handleSubmit} className="card p-6 space-y-5">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <div>
          <label className="label">Product / Brand *</label>
          <input
            className="input"
            placeholder="e.g. Pulse Hydration"
            value={form.product}
            onChange={(e) => handleChange('product', e.target.value)}
            required
          />
        </div>
        <div>
          <label className="label">Brand Name *</label>
          <input
            className="input"
            placeholder="e.g. Pulse"
            value={form.brand}
            onChange={(e) => handleChange('brand', e.target.value)}
            required
          />
        </div>
      </div>

      <div>
        <label className="label">Target Audience *</label>
        <input
          className="input"
          placeholder="e.g. College-age fitness enthusiasts"
          value={form.audience}
          onChange={(e) => handleChange('audience', e.target.value)}
          required
        />
      </div>

      <div>
        <label className="label">Product Image * <span className="text-gray-400 font-normal">(JPG, PNG, WebP • max 10 MB)</span></label>
        <label className="flex items-center gap-3 border-2 border-dashed border-gray-200 rounded-xl p-4 cursor-pointer hover:border-brand-300 hover:bg-brand-50/30 transition-colors">
          <div className="w-11 h-11 rounded-lg bg-brand-50 flex items-center justify-center">
            <Upload className="w-5 h-5 text-brand-600" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-gray-800">Upload the actual product photo</p>
            <p className="text-xs text-gray-500">DevAd preserves this exact product photo in every zero-cost creative.</p>
          </div>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0] || null;
              setProductImage(file);
              setPreviewUrl(file ? URL.createObjectURL(file) : null);
            }}
            required
          />
        </label>
        {productImage && (
          <div className="mt-3 flex items-center gap-3">
            {previewUrl ? <img src={previewUrl} alt="Product preview" className="w-16 h-16 object-contain rounded-lg border bg-white" /> : <ImageIcon className="w-5 h-5" />}
            <div><p className="text-sm font-medium text-gray-800">{productImage.name}</p><p className="text-xs text-gray-500">{(productImage.size / 1024 / 1024).toFixed(2)} MB</p></div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <div>
          <label className="label">Platform *</label>
          <select
            className="input"
            value={form.platform}
            onChange={(e) => handleChange('platform', e.target.value)}
          >
            {PLATFORMS.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Campaign Objective *</label>
          <select
            className="input"
            value={form.objective}
            onChange={(e) => handleChange('objective', e.target.value)}
          >
            {OBJECTIVES.map((o) => <option key={o} value={o}>{o}</option>)}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <div>
          <label className="label">Offer</label>
          <input
            className="input"
            placeholder="e.g. 20% launch discount"
            value={form.offer}
            onChange={(e) => handleChange('offer', e.target.value)}
          />
        </div>
        <div>
          <label className="label">Budget</label>
          <input
            className="input"
            type="number"
            placeholder="e.g. 5000"
            value={form.budget || ''}
            onChange={(e) => handleChange('budget', e.target.value ? Number(e.target.value) : undefined)}
          />
        </div>
      </div>

      <div>
        <label className="label">Creative Format *</label>
        <select
          className="input"
          value={form.creative_format}
          onChange={(e) => handleChange('creative_format', e.target.value)}
        >
          {FORMATS.map((f) => <option key={f} value={f}>{f}</option>)}
        </select>
      </div>

      <div>
        <label className="label">Brand Voice</label>
        <input
          className="input"
          placeholder="e.g. Energetic, direct, authentic"
          value={form.brand_voice}
          onChange={(e) => handleChange('brand_voice', e.target.value)}
        />
      </div>

      <div>
        <label className="label">Additional Context</label>
        <textarea
          className="input min-h-[80px]"
          placeholder="Any additional context for the campaign..."
          value={form.brief_context}
          onChange={(e) => handleChange('brief_context', e.target.value)}
        />
      </div>

      <button type="submit" disabled={!canSubmit} className="btn-primary w-full gap-2 py-3 text-base">
        <Sparkles className="w-5 h-5" />
        Generate Campaign
      </button>
    </form>
  );
}
