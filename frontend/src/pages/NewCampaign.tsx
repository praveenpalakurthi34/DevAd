import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Brain, Loader2 } from 'lucide-react';
import CampaignForm from '../components/CampaignForm';
import GenerationProgress from '../components/GenerationProgress';
import { api } from '../api/client';
import type { CampaignCreateData, GenerationJob } from '../types';

export default function NewCampaign() {
  const navigate = useNavigate();
  const [memoryMode, setMemoryMode] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [job, setJob] = useState<GenerationJob | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (data: CampaignCreateData) => {
    try {
      setError(null);
      setGenerating(true);

      // Upload the real product photo first. It becomes the exact product identity preserved in the generated poster.
      let product_image_path: string | undefined;
      if (data.product_image) {
        const uploaded = await api.uploadProductImage(data.product_image);
        product_image_path = uploaded.path;
      }
      const { product_image: _productImage, ...campaignPayload } = data;

      // Create campaign with the uploaded product reference.
      const campaign = await api.createCampaign({ ...campaignPayload, product_image_path, memory_mode: memoryMode });

      // Start generation
      const genJob = await api.generateCampaign(campaign.id, memoryMode);
      setJob(genJob);

      // Poll for completion
      const pollInterval = setInterval(async () => {
        try {
          const status = await api.getGenerationStatus(genJob.id);
          setJob(status);

          if (status.status === 'completed' || status.status === 'failed') {
            clearInterval(pollInterval);
            if (status.status === 'completed') {
              setTimeout(() => navigate(`/campaigns/${campaign.id}`), 1000);
            } else {
              setError(status.error || 'Generation failed');
              setGenerating(false);
            }
          }
        } catch (err) {
          clearInterval(pollInterval);
          setError('Failed to check generation status');
          setGenerating(false);
        }
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Failed to create campaign');
      setGenerating(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Create Campaign</h1>
        <p className="text-gray-500 mt-1">Define your campaign brief and let DevAd create a memory-informed, product-grounded static ad.</p>
      </div>

      {/* Memory Mode Toggle */}
      <div className="card p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {memoryMode ? (
              <div className="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center">
                <Brain className="w-5 h-5 text-purple-600" />
              </div>
            ) : (
              <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center">
                <Brain className="w-5 h-5 text-gray-400 opacity-50" />
              </div>
            )}
            <div>
              <p className="font-semibold text-gray-900">Memory Mode</p>
              <p className="text-sm text-gray-500">
                {memoryMode
                  ? 'Campaign will use historical memory from Hindsight'
                  : 'Baseline mode — no historical memory used'}
              </p>
            </div>
          </div>
          <button
            onClick={() => setMemoryMode(!memoryMode)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              memoryMode ? 'bg-purple-600' : 'bg-gray-300'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                memoryMode ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
        {memoryMode && (
          <div className="mt-3 px-3 py-2 bg-purple-50 rounded-lg">
            <p className="text-xs text-purple-700">
              <strong>Memory-informed campaign:</strong> DevAd will recall relevant campaign experiences from Hindsight,
              analyze historical evidence, and use it to shape the strategy.
            </p>
          </div>
        )}
        {!memoryMode && (
          <div className="mt-3 px-3 py-2 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-600">
              <strong>Baseline — no historical memory used:</strong> Campaign will be generated from the brief only,
              without recalling previous campaign experiences.
            </p>
          </div>
        )}
      </div>

      {/* Generation Progress */}
      {generating && job && (
        <GenerationProgress job={job} memoryMode={memoryMode} />
      )}

      {/* Error */}
      {error && (
        <div className="card p-4 bg-red-50 border-red-200">
          <p className="text-sm text-red-700 font-medium">{error}</p>
        </div>
      )}

      {/* Campaign Form */}
      {!generating && (
        <CampaignForm onSubmit={handleSubmit} memoryMode={memoryMode} />
      )}
    </div>
  );
}
