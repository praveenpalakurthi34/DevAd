import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Loader2, Brain, RefreshCw, RotateCcw } from 'lucide-react';
import { api } from '../api/client';
import MemoryEvidence from '../components/MemoryEvidence';
import StrategyCard from '../components/StrategyCard';
import CreativePreview from '../components/CreativePreview';
import OutcomeForm from '../components/OutcomeForm';
import type { Campaign, CampaignStrategy, GeneratedAd, WhyCampaign, Outcome, LearningEvent } from '../types';

export default function CampaignDetail() {
  const { id } = useParams<{ id: string }>();
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [loading, setLoading] = useState(true);
  const [outcomes, setOutcomes] = useState<Outcome[]>([]);
  const [learningEvent, setLearningEvent] = useState<LearningEvent | null>(null);
  const [renderingCreative, setRenderingCreative] = useState(false);
  const [retryingLearning, setRetryingLearning] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    const fetchData = async () => {
      try {
        setLoading(true);
        const [camp, outs, learningEvents] = await Promise.all([
          api.getCampaign(parseInt(id)),
          api.getCampaignOutcomes(parseInt(id)).catch(() => []),
          api.getLearningEvents().catch(() => []),
        ]);
        setCampaign(camp);
        setOutcomes(outs);
        const matchingLearning = learningEvents.find((event: LearningEvent) => event.campaign_id === parseInt(id));
        setLearningEvent(matchingLearning || null);
      } catch (err) {
        console.error('Failed to fetch campaign:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-brand-600" />
      </div>
    );
  }

  if (!campaign) {
    return <div className="text-center py-20 text-gray-500">Campaign not found</div>;
  }

  const safeJson = <T,>(value: string | undefined, fallback: T): T => {
    if (!value) return fallback;
    try { return JSON.parse(value) as T; } catch { return fallback; }
  };
  const strategy: CampaignStrategy | null = safeJson(campaign.strategy, null);
  const ad: GeneratedAd | null = safeJson(campaign.generated_ad, null);
  const whyCampaign = safeJson<WhyCampaign | null>(campaign.why_campaign, null);

  const handleRenderCreative = async () => {
    try {
      setRenderingCreative(true);
      setActionMessage(null);
      await api.renderCreative(campaign.id);
      const refreshed = await api.getCampaign(campaign.id);
      setCampaign(refreshed);
      setActionMessage('Creative regenerated successfully.');
    } catch (err: any) {
      setActionMessage(err.message || 'Creative regeneration failed.');
    } finally {
      setRenderingCreative(false);
    }
  };

  const handleRetryLearning = async () => {
    try {
      setRetryingLearning(true);
      setActionMessage(null);
      const result = await api.retryLearning(campaign.id);
      setLearningEvent((current) => current ? { ...current, hindsight_status: result.status, hindsight_memory_id: result.memory_id } : current);
      setActionMessage('Hindsight retention confirmed.');
    } catch (err: any) {
      setActionMessage(err.message || 'Hindsight retention retry failed.');
    } finally {
      setRetryingLearning(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      {/* Back link */}
      <Link to="/history" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="w-4 h-4" /> Back to History
      </Link>

      {/* Campaign header */}
      <div className="card p-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{campaign.product}</h1>
            <p className="text-gray-500 mt-1">{campaign.brand} · {campaign.platform} · {campaign.objective}</p>
          </div>
          <div className="flex items-center gap-2">
            <span className={`badge ${campaign.status === 'completed' ? 'badge-success' : 'badge-neutral'}`}>
              {campaign.status}
            </span>
            {campaign.memory_mode ? (
              <span className="badge badge-info"><Brain className="w-3 h-3 mr-1" /> Memory ON</span>
            ) : (
              <span className="badge badge-neutral">Memory OFF</span>
            )}
          </div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4 pt-4 border-t border-gray-100">
          <div>
            <p className="text-xs text-gray-500">Audience</p>
            <p className="text-sm font-medium text-gray-900">{campaign.audience}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Creative Format</p>
            <p className="text-sm font-medium text-gray-900">{campaign.creative_format}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Offer</p>
            <p className="text-sm font-medium text-gray-900">{campaign.offer || 'N/A'}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Budget</p>
            <p className="text-sm font-medium text-gray-900">{campaign.budget ? `$${campaign.budget}` : 'N/A'}</p>
          </div>
        </div>

        {/* Metrics if available */}
        {campaign.metrics && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-4 border-t border-gray-100">
            {campaign.metrics.ctr != null && (
              <div className="text-center p-2 bg-blue-50 rounded-lg">
                <p className="text-lg font-bold text-blue-700">{campaign.metrics.ctr}%</p>
                <p className="text-xs text-blue-600">CTR</p>
              </div>
            )}
            {campaign.metrics.cvr != null && (
              <div className="text-center p-2 bg-emerald-50 rounded-lg">
                <p className="text-lg font-bold text-emerald-700">{campaign.metrics.cvr}%</p>
                <p className="text-xs text-emerald-600">CVR</p>
              </div>
            )}
            {campaign.metrics.cpa != null && (
              <div className="text-center p-2 bg-amber-50 rounded-lg">
                <p className="text-lg font-bold text-amber-700">${campaign.metrics.cpa}</p>
                <p className="text-xs text-amber-600">CPA</p>
              </div>
            )}
            {campaign.metrics.roas != null && (
              <div className="text-center p-2 bg-purple-50 rounded-lg">
                <p className="text-lg font-bold text-purple-700">{campaign.metrics.roas}x</p>
                <p className="text-xs text-purple-600">ROAS</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Why this campaign? */}
      {whyCampaign && (
        <MemoryEvidence whyCampaign={whyCampaign} memoryMode={campaign.memory_mode} />
      )}

      {/* Strategy */}
      {strategy && (
        <StrategyCard strategy={strategy} memoryMode={campaign.memory_mode} memoryStatus={whyCampaign?.memory_status} />
      )}

      {/* Creative */}
      {ad && (
        <CreativePreview ad={ad} assets={campaign.assets} />
      )}

      <div className="flex flex-wrap items-center gap-3">
        <button onClick={handleRenderCreative} disabled={renderingCreative || !ad} className="btn-secondary gap-2">
          {renderingCreative ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          {renderingCreative ? 'Generating creative…' : (campaign.creative_format.toLowerCase().includes('carousel') ? 'Regenerate Carousel' : 'Regenerate Image')}
        </button>
        {learningEvent?.hindsight_status === 'failed' && (
          <button onClick={handleRetryLearning} disabled={retryingLearning} className="btn-secondary gap-2">
            {retryingLearning ? <Loader2 className="w-4 h-4 animate-spin" /> : <RotateCcw className="w-4 h-4" />}
            Retry Hindsight Retain
          </button>
        )}
        {actionMessage && <span className="text-sm text-gray-600">{actionMessage}</span>}
      </div>

      {learningEvent && (
        <div className={`card p-5 ${learningEvent.hindsight_status === 'retained' ? 'bg-emerald-50 border-emerald-200' : learningEvent.hindsight_status === 'failed' ? 'bg-red-50 border-red-200' : 'bg-amber-50 border-amber-200'}`}>
          <p className="text-sm font-semibold text-gray-900">Learning status: {learningEvent.hindsight_status}</p>
          <p className="text-sm text-gray-700 mt-1">{learningEvent.lesson}</p>
          {learningEvent.hindsight_status === 'retained' && <p className="text-xs text-emerald-700 mt-2">Hindsight accepted this experience for future campaign recall.</p>}
          {learningEvent.hindsight_status === 'failed' && <p className="text-xs text-red-700 mt-2">The lesson is stored locally, but Hindsight did not confirm retention.</p>}
        </div>
      )}

      {/* Outcome */}
      {campaign.status === 'completed' && outcomes.length === 0 && (
        <OutcomeForm campaignId={campaign.id} onOutcomeRecorded={(o) => setOutcomes([o])} />
      )}

      {/* Recorded outcomes */}
      {outcomes.length > 0 && (
        <div className="card p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Recorded Outcomes</h2>
          {outcomes.map((outcome) => (
            <div key={outcome.id} className="space-y-3">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {outcome.ctr != null && (
                  <div className="text-center p-3 bg-blue-50 rounded-lg">
                    <p className="text-lg font-bold text-blue-700">{outcome.ctr}%</p>
                    <p className="text-xs text-blue-600">CTR</p>
                  </div>
                )}
                {outcome.cvr != null && (
                  <div className="text-center p-3 bg-emerald-50 rounded-lg">
                    <p className="text-lg font-bold text-emerald-700">{outcome.cvr}%</p>
                    <p className="text-xs text-emerald-600">CVR</p>
                  </div>
                )}
                {outcome.cpa != null && (
                  <div className="text-center p-3 bg-amber-50 rounded-lg">
                    <p className="text-lg font-bold text-amber-700">${outcome.cpa}</p>
                    <p className="text-xs text-amber-600">CPA</p>
                  </div>
                )}
                {outcome.roas != null && (
                  <div className="text-center p-3 bg-purple-50 rounded-lg">
                    <p className="text-lg font-bold text-purple-700">{outcome.roas}x</p>
                    <p className="text-xs text-purple-600">ROAS</p>
                  </div>
                )}
              </div>
              {outcome.lesson_learned && (
                <div className="bg-emerald-50 rounded-lg p-4">
                  <p className="text-sm font-medium text-emerald-800">Lesson Learned</p>
                  <p className="text-sm text-emerald-700 mt-1">{outcome.lesson_learned}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
