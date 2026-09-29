import React, { useState } from 'react';
import { TrendingUp, Save, Loader2 } from 'lucide-react';
import { api } from '../api/client';
import type { OutcomeData, Outcome } from '../types';

interface Props {
  campaignId: number;
  onOutcomeRecorded: (outcome: Outcome) => void;
}

export default function OutcomeForm({ campaignId, onOutcomeRecorded }: Props) {
  const [form, setForm] = useState<OutcomeData>({
    impressions: undefined,
    clicks: undefined,
    conversions: undefined,
    spend: undefined,
    revenue: undefined,
    notes: '',
    what_happened: '',
    lesson_learned: '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleChange = (field: keyof OutcomeData, value: any) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError(null);
      const outcome = await api.recordOutcome(campaignId, form);
      setSuccess(true);
      onOutcomeRecorded(outcome);
    } catch (err: any) {
      setError(err.message || 'Failed to record outcome');
    } finally {
      setSaving(false);
    }
  };

  // Calculate preview metrics
  const previewMetrics = {
    ctr: form.impressions && form.impressions > 0 && form.clicks != null ? ((form.clicks / form.impressions) * 100).toFixed(2) : null,
    cvr: form.clicks && form.clicks > 0 && form.conversions != null ? ((form.conversions / form.clicks) * 100).toFixed(2) : null,
    cpa: form.conversions && form.conversions > 0 && form.spend != null ? (form.spend / form.conversions).toFixed(2) : null,
    roas: form.spend && form.spend > 0 && form.revenue != null ? (form.revenue / form.spend).toFixed(2) : null,
  };

  if (success) {
    return (
      <div className="card p-6 bg-emerald-50 border-emerald-200">
        <div className="flex items-center gap-3">
          <TrendingUp className="w-6 h-6 text-emerald-600" />
          <div>
            <p className="font-semibold text-emerald-800">Outcome Recorded — DevAd Learned!</p>
            <p className="text-sm text-emerald-600 mt-1">
              This experience has been stored in Hindsight and will inform future campaigns.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <div className="p-6 border-b border-gray-100">
        <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-gray-400" />
          Record Outcome
        </h2>
        <p className="text-sm text-gray-500 mt-1">
          Enter campaign results to help DevAd learn from this experience.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="p-6 space-y-5">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          <div>
            <label className="label">Impressions</label>
            <input
              className="input"
              type="number"
              placeholder="0"
              value={form.impressions || ''}
              onChange={(e) => handleChange('impressions', e.target.value ? parseInt(e.target.value) : undefined)}
            />
          </div>
          <div>
            <label className="label">Clicks</label>
            <input
              className="input"
              type="number"
              placeholder="0"
              value={form.clicks || ''}
              onChange={(e) => handleChange('clicks', e.target.value ? parseInt(e.target.value) : undefined)}
            />
          </div>
          <div>
            <label className="label">Conversions</label>
            <input
              className="input"
              type="number"
              placeholder="0"
              value={form.conversions || ''}
              onChange={(e) => handleChange('conversions', e.target.value ? parseInt(e.target.value) : undefined)}
            />
          </div>
          <div>
            <label className="label">Spend ($)</label>
            <input
              className="input"
              type="number"
              step="0.01"
              placeholder="0.00"
              value={form.spend || ''}
              onChange={(e) => handleChange('spend', e.target.value ? parseFloat(e.target.value) : undefined)}
            />
          </div>
          <div>
            <label className="label">Revenue ($)</label>
            <input
              className="input"
              type="number"
              step="0.01"
              placeholder="0.00"
              value={form.revenue || ''}
              onChange={(e) => handleChange('revenue', e.target.value ? parseFloat(e.target.value) : undefined)}
            />
          </div>
        </div>

        {/* Calculated metrics preview */}
        {(previewMetrics.ctr || previewMetrics.cvr || previewMetrics.cpa || previewMetrics.roas) && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {previewMetrics.ctr && (
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <p className="text-lg font-bold text-blue-700">{previewMetrics.ctr}%</p>
                <p className="text-xs text-blue-600">CTR</p>
              </div>
            )}
            {previewMetrics.cvr && (
              <div className="text-center p-3 bg-emerald-50 rounded-lg">
                <p className="text-lg font-bold text-emerald-700">{previewMetrics.cvr}%</p>
                <p className="text-xs text-emerald-600">CVR</p>
              </div>
            )}
            {previewMetrics.cpa && (
              <div className="text-center p-3 bg-amber-50 rounded-lg">
                <p className="text-lg font-bold text-amber-700">${previewMetrics.cpa}</p>
                <p className="text-xs text-amber-600">CPA</p>
              </div>
            )}
            {previewMetrics.roas && (
              <div className="text-center p-3 bg-purple-50 rounded-lg">
                <p className="text-lg font-bold text-purple-700">{previewMetrics.roas}x</p>
                <p className="text-xs text-purple-600">ROAS</p>
              </div>
            )}
          </div>
        )}

        <div>
          <label className="label">Campaign Notes</label>
          <textarea
            className="input min-h-[60px]"
            placeholder="What happened with this campaign?"
            value={form.notes}
            onChange={(e) => handleChange('notes', e.target.value)}
          />
        </div>

        <div>
          <label className="label">What Happened?</label>
          <textarea
            className="input min-h-[60px]"
            placeholder="Describe the campaign performance and context..."
            value={form.what_happened}
            onChange={(e) => handleChange('what_happened', e.target.value)}
          />
        </div>

        <div>
          <label className="label">What Did You Learn?</label>
          <textarea
            className="input min-h-[60px]"
            placeholder="Key takeaways from this campaign..."
            value={form.lesson_learned}
            onChange={(e) => handleChange('lesson_learned', e.target.value)}
          />
        </div>

        {error && (
          <div className="p-3 bg-red-50 rounded-lg">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        <button type="submit" disabled={saving} className="btn-primary w-full gap-2">
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          Record Outcome & Learn
        </button>
      </form>
    </div>
  );
}
