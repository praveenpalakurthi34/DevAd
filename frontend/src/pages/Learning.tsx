import React, { useEffect, useState } from 'react';
import { Brain, BookOpen, Eye, Target, Loader2, Sparkles } from 'lucide-react';
import { api } from '../api/client';
import LearningTimeline from '../components/LearningTimeline';
import type { LearningEvent, DashboardStats } from '../types';

export default function Learning() {
  const [events, setEvents] = useState<LearningEvent[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [demoRunning, setDemoRunning] = useState(false);

  useEffect(() => {
    const fetch = async () => {
      try {
        const [evts, st] = await Promise.all([
          api.getLearningEvents(),
          api.getDashboardStats(),
        ]);
        setEvents(evts);
        setStats(st);
      } catch (err) {
        console.error('Failed to fetch learning data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-brand-600" />
      </div>
    );
  }

  const retainedCount = events.filter(e => e.hindsight_status === 'retained').length;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Learning</h1>
        <p className="text-gray-500 mt-1">How DevAd learns from campaign experiences</p>
      </div>

      <div className="card p-5 bg-purple-50 border-purple-200">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <p className="font-semibold text-purple-900 flex items-center gap-2"><Sparkles className="w-4 h-4" /> Prove the learning loop</p>
            <p className="text-sm text-purple-700 mt-1">Generate a related campaign that recalls prior campaign experience and exposes the memory-driven decision.</p>
          </div>
          <button
            className="btn-primary gap-2"
            disabled={demoRunning}
            onClick={async () => {
              try {
                setDemoRunning(true);
                const result = await api.startLearningLoopDemo();
                window.location.href = `/campaigns/${result.campaign_id}`;
              } catch (err: any) {
                alert(err.message || 'Load Demo Data first, then run the learning demo.');
              } finally {
                setDemoRunning(false);
              }
            }}
          >
            {demoRunning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            Run Learning Demo
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="card p-4 text-center">
          <Brain className="w-6 h-6 text-purple-600 mx-auto mb-2" />
          <p className="text-2xl font-bold text-gray-900">{stats?.total_memories || 0}</p>
          <p className="text-xs text-gray-500">Total Memories</p>
        </div>
        <div className="card p-4 text-center">
          <BookOpen className="w-6 h-6 text-blue-600 mx-auto mb-2" />
          <p className="text-2xl font-bold text-gray-900">{retainedCount}</p>
          <p className="text-xs text-gray-500">Experiences Retained</p>
        </div>
        <div className="card p-4 text-center">
          <Eye className="w-6 h-6 text-amber-600 mx-auto mb-2" />
          <p className="text-2xl font-bold text-gray-900">{stats?.total_observations || 0}</p>
          <p className="text-xs text-gray-500">Observations</p>
        </div>
        <div className="card p-4 text-center">
          <Target className="w-6 h-6 text-emerald-600 mx-auto mb-2" />
          <p className="text-2xl font-bold text-gray-900">{stats?.total_outcomes || 0}</p>
          <p className="text-xs text-gray-500">Outcomes Recorded</p>
        </div>
      </div>

      {/* Learned patterns summary */}
      {events.filter(e => e.hindsight_status === 'retained').length > 0 && (
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Learned Patterns</h2>
          <div className="space-y-3">
            {events
              .filter(e => e.hindsight_status === 'retained')
              .slice(0, 5)
              .map(event => (
                <div key={event.id} className="flex items-start gap-3 p-3 bg-emerald-50 rounded-lg">
                  <Brain className="w-4 h-4 text-emerald-600 mt-0.5" />
                  <div>
                    <p className="text-sm text-emerald-800">{event.lesson}</p>
                    <p className="text-xs text-emerald-600 mt-1">
                      Campaign #{event.campaign_id} · {new Date(event.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Timeline */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Learning Timeline</h2>
        <LearningTimeline events={events} />
      </div>
    </div>
  );
}
