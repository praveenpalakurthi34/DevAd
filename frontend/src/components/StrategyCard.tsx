import React from 'react';
import { Lightbulb, MessageSquare, Palette, AlertTriangle, Shield } from 'lucide-react';
import type { CampaignStrategy } from '../types';

interface Props {
  strategy: CampaignStrategy;
  memoryMode: boolean;
  memoryStatus?: string;
}

export default function StrategyCard({ strategy, memoryMode, memoryStatus }: Props) {
  return (
    <div className="card overflow-hidden">
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-900">Campaign Strategy</h2>
          {memoryMode && memoryStatus !== 'unavailable' ? (
            <span className="badge badge-info">{memoryStatus === 'available_with_results' ? 'Memory-informed campaign' : 'Memory mode — no matching history'}</span>
          ) : (
            <span className="badge badge-neutral">Baseline — no historical memory used</span>
          )}
        </div>
      </div>

      <div className="p-6 space-y-5">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-amber-50 flex items-center justify-center flex-shrink-0">
            <Lightbulb className="w-4 h-4 text-amber-600" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Core Insight</p>
            <p className="text-gray-900 mt-1">{strategy.core_insight}</p>
          </div>
        </div>

        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
            <MessageSquare className="w-4 h-4 text-blue-600" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Messaging Angle</p>
            <p className="text-gray-900 mt-1">{strategy.messaging_angle}</p>
          </div>
        </div>

        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-purple-50 flex items-center justify-center flex-shrink-0">
            <Palette className="w-4 h-4 text-purple-600" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Creative Direction</p>
            <p className="text-gray-900 mt-1">{strategy.creative_direction}</p>
          </div>
        </div>

        {strategy.memory_influence && memoryMode && memoryStatus === 'available_with_results' && (
          <div className="rounded-lg border border-purple-200 bg-purple-50 p-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-purple-700">How memory changed this decision</p>
            <p className="mt-1 text-sm text-purple-900">{strategy.memory_influence}</p>
          </div>
        )}

        {strategy.evidence_reasoning && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-50 flex items-center justify-center flex-shrink-0">
              <Shield className="w-4 h-4 text-emerald-600" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Evidence Reasoning</p>
              <p className="text-gray-900 mt-1">{strategy.evidence_reasoning}</p>
            </div>
          </div>
        )}

        {strategy.risks_uncertainties && strategy.risks_uncertainties.length > 0 && (
          <div className="bg-amber-50 rounded-lg p-4">
            <p className="text-sm font-semibold text-amber-800 mb-2 flex items-center gap-1">
              <AlertTriangle className="w-4 h-4" /> Risks & Uncertainties
            </p>
            <ul className="space-y-1">
              {strategy.risks_uncertainties.map((risk, i) => (
                <li key={i} className="text-sm text-amber-700">• {risk}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
