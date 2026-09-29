import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Sparkles,
  Brain,
  Eye,
  Target,
  BookOpen,
  PlusCircle,
  Database,
  RotateCcw,
  Loader2,
  TrendingUp,
  Clock,
} from 'lucide-react';
import { api } from '../api/client';
import type { DashboardStats } from '../types';

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [learningDemo, setLearningDemo] = useState(false);
  const [system, setSystem] = useState<any>(null);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const [data, systemData] = await Promise.all([api.getDashboardStats(), api.getSystemStatus().catch(() => null)]);
      setStats(data);
      setSystem(systemData);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleSeed = async () => {
    try {
      setSeeding(true);
      await api.seedDemoData();
      await fetchStats();
    } catch (err) {
      console.error('Failed to seed:', err);
    } finally {
      setSeeding(false);
    }
  };

  const handleLearningDemo = async () => {
    try {
      setLearningDemo(true);
      const result = await api.startLearningLoopDemo();
      window.location.href = `/campaigns/${result.campaign_id}`;
    } catch (err: any) {
      console.error('Failed to start learning demo:', err);
      alert(err.message || 'Load Demo Data first, then start the learning demo.');
    } finally {
      setLearningDemo(false);
    }
  };

  const handleReset = async () => {
    try {
      setResetting(true);
      await api.resetDemoData();
      await fetchStats();
    } catch (err) {
      console.error('Failed to reset:', err);
    } finally {
      setResetting(false);
    }
  };

  const statCards = [
    { label: 'Campaigns', value: stats?.total_campaigns || 0, icon: Target, color: 'text-brand-600 bg-brand-50' },
    { label: stats?.hindsight_available ? 'Hindsight Memories' : 'Hindsight Memories*', value: stats?.total_memories || 0, icon: Brain, color: 'text-purple-600 bg-purple-50' },
    { label: 'Observations', value: stats?.total_observations || 0, icon: Eye, color: 'text-amber-600 bg-amber-50' },
    { label: 'Outcomes', value: stats?.total_outcomes || 0, icon: TrendingUp, color: 'text-emerald-600 bg-emerald-50' },
    { label: 'Learning Events', value: stats?.total_learning_events || 0, icon: BookOpen, color: 'text-blue-600 bg-blue-50' },
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Hero */}
      <div className="text-center py-6">
        <div className="inline-flex items-center gap-2 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">DevAd</h1>
        </div>
        <p className="text-lg text-gray-500 font-medium">
          Your advertising team's memory.
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        {statCards.map((stat) => (
          <div key={stat.label} className="card p-4">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${stat.color}`}>
                <stat.icon className="w-5 h-5" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">
                  {loading ? '—' : stat.value}
                </p>
                <p className="text-xs text-gray-500 font-medium">{stat.label}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <p className="text-xs text-gray-400">* Hindsight Memories is the server-reported memory count. Local evidence records are tracked separately from memory.</p>
      {system && (
        <div className="card p-4">
          <div className="flex flex-wrap items-center gap-3 text-xs">
            <span className="font-semibold text-gray-700">Runtime readiness</span>
            <span className={`badge ${system.llm?.configured ? 'badge-success' : 'badge-warning'}`}>Groq {system.llm?.configured ? 'configured' : 'missing key'}</span>
            <span className={`badge ${system.hindsight?.available ? 'badge-success' : 'badge-warning'}`}>Hindsight {system.hindsight?.available ? 'reachable' : 'unavailable'}</span>
            <span className="badge badge-success">Product poster renderer ready</span>
          </div>
        </div>
      )}

      {stats && !stats.hindsight_available && (
        <div className="card p-4 bg-amber-50 border-amber-200">
          <p className="text-sm font-semibold text-amber-800">Hindsight is not currently reachable.</p>
          <p className="text-xs text-amber-700 mt-1">DevAd will not pretend that memory-informed generation succeeded. Check the Hindsight URL/key before the live demo.</p>
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-wrap gap-3">
        <Link to="/campaigns/new" className="btn-primary gap-2">
          <PlusCircle className="w-4 h-4" />
          Create Campaign
        </Link>
        <button onClick={handleSeed} disabled={seeding} className="btn-secondary gap-2">
          {seeding ? <Loader2 className="w-4 h-4 animate-spin" /> : <Database className="w-4 h-4" />}
          Load Demo Data
        </button>
        <button onClick={handleLearningDemo} disabled={learningDemo} className="btn-secondary gap-2">
          {learningDemo ? <Loader2 className="w-4 h-4 animate-spin" /> : <Brain className="w-4 h-4" />}
          Run Learning Demo
        </button>
        <button onClick={handleReset} disabled={resetting} className="btn-secondary gap-2 text-red-600 hover:text-red-700">
          {resetting ? <Loader2 className="w-4 h-4 animate-spin" /> : <RotateCcw className="w-4 h-4" />}
          Reset Local Demo
        </button>
      </div>

      {/* Recent campaigns */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Campaigns</h2>
        {loading ? (
          <div className="card p-8 text-center text-gray-500">
            <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
            Loading...
          </div>
        ) : stats?.recent_campaigns && stats.recent_campaigns.length > 0 ? (
          <div className="grid gap-3">
            {stats.recent_campaigns.map((campaign) => (
              <Link
                key={campaign.id}
                to={`/campaigns/${campaign.id}`}
                className="card p-4 hover:shadow-md transition-shadow duration-200 flex items-center justify-between"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-brand-50 flex items-center justify-center">
                    <Target className="w-5 h-5 text-brand-600" />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">{campaign.product}</p>
                    <p className="text-sm text-gray-500">{campaign.brand} · {campaign.platform}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  {campaign.roas && (
                    <span className="text-sm font-medium text-emerald-600">{campaign.roas}x ROAS</span>
                  )}
                  {campaign.ctr && (
                    <span className="text-sm text-gray-500">{campaign.ctr}% CTR</span>
                  )}
                  <span className={`badge ${campaign.status === 'completed' ? 'badge-success' : 'badge-neutral'}`}>
                    {campaign.status}
                  </span>
                  {campaign.memory_mode && (
                    <span className="badge badge-info">
                      <Brain className="w-3 h-3 mr-1" />
                      Memory
                    </span>
                  )}
                  <Clock className="w-4 h-4 text-gray-400" />
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="card p-8 text-center">
            <Brain className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 mb-2">No campaigns yet</p>
            <p className="text-sm text-gray-400">Load demo data or create your first campaign</p>
          </div>
        )}
      </div>

      {/* Demo mode notice */}
      <div className="card p-4 bg-amber-50 border-amber-200">
        <div className="flex items-start gap-3">
          <Sparkles className="w-5 h-5 text-amber-600 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-amber-800">Demo / Synthetic Data</p>
            <p className="text-sm text-amber-600 mt-1">
              All campaign data shown is synthetic and for demonstration purposes only.
              These are not real client campaign results.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
