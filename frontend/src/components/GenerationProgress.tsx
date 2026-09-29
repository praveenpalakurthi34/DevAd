import React from 'react';
import { Loader2, CheckCircle2, XCircle, Brain, Search, BarChart3, Lightbulb, Palette, Film, Check } from 'lucide-react';
import type { GenerationJob } from '../types';

interface Props {
  job: GenerationJob;
  memoryMode: boolean;
}

const STEPS = [
  { key: 'queued', label: 'Reading campaign brief', icon: Search },
  { key: 'recalling', label: 'Recalling campaign memory', icon: Brain },
  { key: 'analyzing', label: 'Analyzing historical evidence', icon: BarChart3 },
  { key: 'strategizing', label: 'Building strategy', icon: Lightbulb },
  { key: 'generating', label: 'Creating advertisement', icon: Palette },
  { key: 'rendering', label: 'Generating product creative', icon: Film },
  { key: 'completed', label: 'Campaign ready', icon: Check },
];

const STATUS_ORDER = ['queued', 'recalling', 'analyzing', 'strategizing', 'generating', 'rendering', 'completed'];

export default function GenerationProgress({ job, memoryMode }: Props) {
  const currentIdx = STATUS_ORDER.indexOf(job.status);

  return (
    <div className="card p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-gray-900">Generating Campaign...</h3>
        {memoryMode ? (
          <span className="badge badge-info">
            <Brain className="w-3 h-3 mr-1" />
            Memory-informed
          </span>
        ) : (
          <span className="badge badge-neutral">Baseline</span>
        )}
      </div>

      {/* Progress bar */}
      <div className="w-full bg-gray-100 rounded-full h-2">
        <div
          className="bg-brand-600 h-2 rounded-full transition-all duration-500"
          style={{ width: `${job.progress}%` }}
        />
      </div>

      {/* Steps */}
      <div className="space-y-2">
        {STEPS.map((step, idx) => {
          // Skip recall/analyze steps when memory mode is off
          if (!memoryMode && (step.key === 'recalling' || step.key === 'analyzing')) return null;

          const stepIdx = STATUS_ORDER.indexOf(step.key);
          const isDone = currentIdx > stepIdx;
          const isCurrent = currentIdx === stepIdx;
          const isPending = currentIdx < stepIdx;

          return (
            <div key={step.key} className={`flex items-center gap-3 py-1.5 ${
              isCurrent ? 'text-brand-700' : isDone ? 'text-gray-500' : 'text-gray-300'
            }`}>
              {isDone && <CheckCircle2 className="w-5 h-5 text-emerald-500" />}
              {isCurrent && <Loader2 className="w-5 h-5 animate-spin text-brand-600" />}
              {isPending && <div className="w-5 h-5 rounded-full border-2 border-gray-200" />}
              <step.icon className="w-4 h-4" />
              <span className={`text-sm font-medium ${
                isCurrent ? 'text-brand-700' : isDone ? 'text-gray-600' : 'text-gray-400'
              }`}>
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Current step detail */}
      {job.current_step && job.status !== 'completed' && job.status !== 'failed' && (
        <p className="text-sm text-gray-500 animate-pulse-soft">
          {job.current_step}...
        </p>
      )}

      {/* Error */}
      {job.status === 'failed' && job.error && (
        <div className="flex items-start gap-2 p-3 bg-red-50 rounded-lg">
          <XCircle className="w-5 h-5 text-red-500 mt-0.5" />
          <p className="text-sm text-red-700">{job.error}</p>
        </div>
      )}
    </div>
  );
}
