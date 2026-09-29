const API_BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `API error: ${response.status}`);
  }

  return response.json();
}

export const api = {
  // Dashboard
  getDashboardStats: () => request<any>('/dashboard/stats'),

  // Assets
  uploadProductImage: async (file: File) => {
    const form = new FormData();
    form.append('file', file);
    const response = await fetch(`${API_BASE}/assets/product-image`, { method: 'POST', body: form });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `Upload failed: ${response.status}`);
    }
    return response.json();
  },

  // Campaigns
  createCampaign: (data: any) =>
    request<any>('/campaigns', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  listCampaigns: () => request<any[]>('/campaigns'),

  getCampaign: (id: number) => request<any>(`/campaigns/${id}`),

  // Generation
  generateCampaign: (campaignId: number, memoryMode: boolean) =>
    request<any>(`/campaigns/${campaignId}/generate`, {
      method: 'POST',
      body: JSON.stringify({ memory_mode: memoryMode }),
    }),

  getGenerationStatus: (jobId: number) => request<any>(`/generation/${jobId}`),

  // Memory
  recallMemories: (query: string, limit?: number) =>
    request<any>('/memory/recall', {
      method: 'POST',
      body: JSON.stringify({ query, limit: limit || 10 }),
    }),

  getCampaignMemories: (campaignId: number) => request<any[]>(`/campaigns/${campaignId}/memories`),

  getCampaignEvidence: (campaignId: number) => request<any>(`/campaigns/${campaignId}/evidence`),

  getCampaignInsights: (campaignId: number) => request<any>(`/campaigns/${campaignId}/insights`),

  // Outcomes
  recordOutcome: (campaignId: number, data: any) =>
    request<any>(`/campaigns/${campaignId}/outcome`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getCampaignOutcomes: (campaignId: number) => request<any[]>(`/campaigns/${campaignId}/outcomes`),

  // Learning
  getLearningEvents: () => request<any[]>('/learning-events'),

  // Demo
  seedDemoData: () =>
    request<any>('/demo/seed', { method: 'POST' }),

  resetDemoData: () =>
    request<any>('/demo/reset', { method: 'POST' }),
  startLearningLoopDemo: () =>
    request<any>('/demo/learning-loop', { method: 'POST' }),

  // Health
  healthCheck: () => request<any>('/health'),
  getSystemStatus: () => request<any>('/system/status'),
  renderCreative: (campaignId: number) => request<any>(`/campaigns/${campaignId}/creative/render`, { method: 'POST' }),
  retryLearning: (campaignId: number) => request<any>(`/campaigns/${campaignId}/learning/retry`, { method: 'POST' }),
};
