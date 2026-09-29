import React from 'react';
import { Brain, CheckCircle2, ArrowDown, Target, TrendingUp, BookOpen, XCircle } from 'lucide-react';
import type { LearningEvent } from '../types';

interface Props {
  events: LearningEvent[];
}

export default function LearningTimeline({ events }: Props) {
  if (!events.length) {
    return (
      <div className="card p-8 text-center">
        <Brain className="w-12 h-12 text-gray-300 mx-auto mb-3" />
        <p className="text-gray-500">No learning events yet</p>
        <p className="text-sm text-gray-400 mt-1">Record campaign outcomes to start building memory</p>
      </div>
    );
  }

  return (
    <div className="space-y-0">
      {events.map((event, idx) => (
        <div key={event.id} className="relative">
          {/* Connector line */}
          {idx < events.length - 1 && (
            <div className="absolute left-5 top-12 bottom-0 w-0.5 bg-gray-200" />
          )}

          <div className="flex gap-4 pb-6">
            {/* Icon */}
            <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 z-10 ${
              event.hindsight_status === 'retained'
                ? 'bg-emerald-100'
                : event.hindsight_status === 'failed'
                ? 'bg-red-100'
                : 'bg-gray-100'
            }`}>
              {event.hindsight_status === 'retained' ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              ) : event.hindsight_status === 'failed' ? (
                <XCircle className="w-5 h-5 text-red-500" />
              ) : (
                <BookOpen className="w-5 h-5 text-gray-400" />
              )}
            </div>

            {/* Content */}
            <div className="card p-4 flex-1">
              <div className="flex items-center justify-between mb-2">
                <span className={`badge ${
                  event.hindsight_status === 'retained' ? 'badge-success' :
                  event.hindsight_status === 'failed' ? 'badge-error' :
                  'badge-warning'
                }`}>
                  {event.hindsight_status === 'retained' ? '✓ Learned by DevAd' :
                   event.hindsight_status === 'failed' ? '✕ Failed to retain' :
                   'Pending'}
                </span>
                <span className="text-xs text-gray-400">
                  {new Date(event.created_at).toLocaleDateString()}
                </span>
              </div>
              <p className="text-sm text-gray-700">{event.lesson}</p>
              <p className="text-xs text-gray-400 mt-2">Campaign #{event.campaign_id}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
