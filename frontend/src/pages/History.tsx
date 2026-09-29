import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Target, Brain, Clock, Loader2, TrendingUp, ChevronRight } from 'lucide-react';
import { api } from '../api/client';
import type { Campaign, CampaignMetrics } from '../types';

interface CampaignListItem {
  id: number;
  brand: string;
  product: string;
  audience: string;
  platform: string;
  objective: string;
  creative_format: string;
  memory_mode: boolean;
  status: string;
  created_at: string;
  metrics?: CampaignMetrics;
}

export default function HistoryPage() {
  const [campaigns, setCampaigns] = useState<CampaignListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        const data = await api.listCampaigns();
        setCampaigns(data);
      } catch (err) {
        console.error('Failed to fetch campaigns:', err);
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, []);

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Campaign History</h1>
        <p className="text-gray-500 mt-1">View all campaigns and their performance</p>
      </div>

      {loading ? (
        <div className="card p-8 text-center text-gray-500">
          <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
          Loading campaigns...
        </div>
      ) : campaigns.length === 0 ? (
        <div className="card p-8 text-center">
          <Target className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No campaigns yet</p>
          <Link to="/campaigns/new" className="btn-primary mt-4 inline-flex">Create Campaign</Link>
        </div>
      ) : (
        <div className="space-y-3">
          {campaigns.map((campaign) => (
            <Link
              key={campaign.id}
              to={`/campaigns/${campaign.id}`}
              className="card p-4 hover:shadow-md transition-all duration-200 block"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-brand-50 flex items-center justify-center">
                    <Target className="w-5 h-5 text-brand-600" />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">{campaign.product}</p>
                    <p className="text-sm text-gray-500">
                      {campaign.brand} · {campaign.platform} · {campaign.objective}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="hidden sm:flex items-center gap-3 text-sm">
                    {campaign.metrics?.roas != null && (
                      <span className="font-medium text-emerald-600">
                        <TrendingUp className="w-3 h-3 inline mr-1" />
                        {campaign.metrics.roas}x ROAS
                      </span>
                    )}
                    {campaign.metrics?.ctr != null && (
                      <span className="text-gray-500">{campaign.metrics.ctr}% CTR</span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <span className={`badge ${campaign.status === 'completed' ? 'badge-success' : campaign.status === 'generating' ? 'badge-warning' : 'badge-neutral'}`}>
                      {campaign.status}
                    </span>
                    {campaign.memory_mode && (
                      <span className="badge badge-info">
                        <Brain className="w-3 h-3" />
                      </span>
                    )}
                  </div>

                  <span className="text-xs text-gray-400 hidden sm:block">
                    {new Date(campaign.created_at).toLocaleDateString()}
                  </span>

                  <ChevronRight className="w-4 h-4 text-gray-400" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
