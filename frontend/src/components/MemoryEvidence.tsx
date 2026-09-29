import React from 'react';
import { Brain, TrendingUp, TrendingDown, AlertTriangle, CheckCircle2, XCircle, Search } from 'lucide-react';
import type { WhyCampaign } from '../types';

interface Props {
  whyCampaign: WhyCampaign;
  memoryMode: boolean;
}

export default function MemoryEvidence({ whyCampaign, memoryMode }: Props) {
  if (!memoryMode) {
    return (
      <div className="card p-6 bg-gray-50 border-gray-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center">
            <Brain className="w-5 h-5 text-gray-400" />
          </div>
          <div>
            <p className="font-semibold text-gray-700">Baseline — No Historical Memory Used</p>
            <p className="text-sm text-gray-500">This campaign was generated without recalling previous experiences.</p>
          </div>
        </div>
      </div>
    );
  }

  if (whyCampaign.memory_status === 'unavailable') {
    return (
      <div className="card p-6 bg-amber-50 border-amber-200">
        <div className="flex items-start gap-3">
          <Brain className="w-5 h-5 text-amber-600 mt-0.5" />
          <div>
            <p className="font-semibold text-amber-800">Hindsight requested, but unavailable</p>
            <p className="text-sm text-amber-700 mt-1">DevAd generated a transparent baseline instead of claiming that memory influenced this campaign.</p>
            {whyCampaign.memory_error && <p className="text-xs text-amber-600 mt-2">{whyCampaign.memory_error}</p>}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-50 to-brand-50 p-6 border-b border-gray-100">
        <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
          <Brain className="w-5 h-5 text-purple-600" />
          Why This Campaign?
        </h2>
        <p className="text-sm text-gray-600 mt-1">Evidence-based reasoning from campaign memory</p>
        <div className="mt-3 text-xs font-medium text-purple-700">Hindsight status: {whyCampaign.memory_status === 'available_with_results' ? 'Memory recalled and used' : 'Memory service available; no matching memories returned'}</div>
      </div>

      <div className="p-6 space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="text-center p-3 bg-purple-50 rounded-lg">
            <p className="text-2xl font-bold text-purple-700">{whyCampaign.memories_recalled}</p>
            <p className="text-xs text-purple-600">Memories Recalled</p>
          </div>
          <div className="text-center p-3 bg-brand-50 rounded-lg">
            <p className="text-2xl font-bold text-brand-700">{whyCampaign.relevant_campaigns}</p>
            <p className="text-xs text-brand-600">Relevant Campaigns</p>
          </div>
          <div className="text-center p-3 bg-emerald-50 rounded-lg">
            <p className="text-2xl font-bold text-emerald-700">{whyCampaign.high_performing.length}</p>
            <p className="text-xs text-emerald-600">High Performing</p>
          </div>
          <div className="text-center p-3 bg-amber-50 rounded-lg">
            <p className="text-2xl font-bold text-amber-700">{whyCampaign.underperforming.length}</p>
            <p className="text-xs text-amber-600">Underperforming</p>
          </div>
        </div>

        {/* Recall query */}
        {whyCampaign.recall_query && (
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-xs font-medium text-gray-500 mb-2 flex items-center gap-1">
              <Search className="w-3 h-3" /> Recall Query
            </p>
            <p className="text-sm text-gray-700 italic">"{whyCampaign.recall_query}"</p>
          </div>
        )}

        {/* Patterns */}
        {whyCampaign.positive_patterns.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-2">Patterns Found</h3>
            <div className="space-y-2">
              {whyCampaign.positive_patterns.map((pattern, i) => (
                <div key={i} className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-gray-700">{pattern}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {whyCampaign.negative_patterns.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-2">Avoided</h3>
            <div className="space-y-2">
              {whyCampaign.negative_patterns.map((pattern, i) => (
                <div key={i} className="flex items-start gap-2">
                  <XCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-gray-700">{pattern}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Conflicts */}
        {whyCampaign.conflicts.length > 0 && (
          <div className="bg-amber-50 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-amber-800 mb-2 flex items-center gap-1">
              <AlertTriangle className="w-4 h-4" /> Conflicting Evidence
            </h3>
            {whyCampaign.conflicts.map((conflict, i) => (
              <p key={i} className="text-sm text-amber-700">{conflict}</p>
            ))}
          </div>
        )}

        {/* Evidence items */}
        {whyCampaign.evidence_items.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Evidence</h3>
            <div className="space-y-3">
              {whyCampaign.evidence_items.map((item, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    {item.performance === 'high' ? (
                      <TrendingUp className="w-4 h-4 text-emerald-500" />
                    ) : item.performance === 'low' ? (
                      <TrendingDown className="w-4 h-4 text-red-400" />
                    ) : (
                      <div className="w-4 h-4 rounded-full bg-gray-300" />
                    )}
                    <span className="text-sm font-medium text-gray-900">
                      {item.campaign_name || 'Campaign'}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-gray-500">
                    {item.metrics?.ctr && <span>{item.metrics.ctr}% CTR</span>}
                    {item.metrics?.cvr && <span>{item.metrics.cvr}% CVR</span>}
                    {item.metrics?.roas && <span>{item.metrics.roas}x ROAS</span>}
                    <span className="text-brand-600 font-medium">
                      {((item.relevance_score || 0) * 100).toFixed(0)}% match
                    </span>
                  </div>
                  {item.relevance_breakdown?.components && (
                    <div className="mt-2 ml-7 flex flex-wrap gap-2">
                      {Object.entries(item.relevance_breakdown.components).map(([key, value]) => (
                        <span key={key} className="text-[11px] px-2 py-1 rounded bg-white border border-gray-200 text-gray-500">
                          {key.replace('_', ' ')} {Math.round(value * 100)}%
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Summary */}
        {whyCampaign.summary && (
          <div className="border-t border-gray-100 pt-4">
            <p className="text-sm text-gray-600">{whyCampaign.summary}</p>
          </div>
        )}
      </div>
    </div>
  );
}
