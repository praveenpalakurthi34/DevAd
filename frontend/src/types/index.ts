export interface Campaign {
  id: number;
  brand: string;
  product: string;
  audience: string;
  platform: string;
  objective: string;
  offer?: string;
  budget?: number;
  creative_format: string;
  brand_voice?: string;
  brief_context?: string;
  product_image_path?: string;
  memory_mode: boolean;
  assets?: GeneratedAsset[];
  status: string;
  strategy?: string;
  generated_ad?: string;
  storyboard?: string;
  why_campaign?: string;
  created_at: string;
  updated_at: string;
  metrics?: CampaignMetrics;
  evidence?: CampaignEvidence[];
}

export interface GeneratedAsset {
  id: number;
  asset_type: string;
  content?: string;
  file_path?: string;
  metadata_json?: string;
  created_at: string;
}

export interface ReelResult {
  status: string;
  provider?: string;
  video_url?: string;
  duration_seconds?: number;
  width?: number;
  height?: number;
  scene_count?: number;
  voiceover?: boolean;
  message?: string;
  error?: string;
  realistic_visuals?: boolean;
  real_product_reference?: boolean;
  creative_format?: string;
  assets?: Array<Record<string, any>>;
}

export interface CampaignMetrics {
  impressions?: number;
  clicks?: number;
  conversions?: number;
  spend?: number;
  revenue?: number;
  ctr?: number;
  cvr?: number;
  cpa?: number;
  roas?: number;
}

export interface CampaignEvidence {
  id: number;
  memory_id?: string;
  campaign_reference?: string;
  relevance_score?: number;
  evidence_type?: string;
  summary?: string;
}

export interface GenerationJob {
  id: number;
  campaign_id: number;
  status: string;
  current_step?: string;
  progress: number;
  error?: string;
  result?: string;
  memory_mode: boolean;
  created_at: string;
  updated_at: string;
}

export interface CampaignStrategy {
  core_insight: string;
  messaging_angle: string;
  creative_direction: string;
  creative_concept?: string;
  evidence_reasoning: string;
  memory_influence?: string;
  risks_uncertainties: string[];
}

export interface GeneratedAd {
  headline: string;
  primary_copy: string;
  cta: string;
}

export interface StoryboardScene {
  scene_number: number;
  time_range: string;
  visual: string;
  audio?: string;
  text_overlay?: string;
  purpose?: string;
  duration_seconds?: number;
}

export interface WhyCampaign {
  memories_recalled: number;
  relevant_campaigns: number;
  memory_requested?: boolean;
  memory_available?: boolean;
  memory_status?: string;
  memory_error?: string;
  high_performing: PerformanceItem[];
  underperforming: PerformanceItem[];
  positive_patterns: string[];
  negative_patterns: string[];
  conflicts: string[];
  evidence_items: EvidenceItem[];
  recall_query?: string;
  summary?: string;
}

export interface PerformanceItem {
  campaign_name?: string;
  metrics?: Record<string, number>;
  relevance_score?: number;
}

export interface EvidenceItem {
  memory_id?: string;
  campaign_name?: string;
  relevance_score?: number;
  performance?: string;
  metrics?: Record<string, number>;
  relevance_breakdown?: {
    components?: Record<string, number>;
    weighted_score?: number;
  };
}

export interface OutcomeData {
  impressions?: number;
  clicks?: number;
  conversions?: number;
  spend?: number;
  revenue?: number;
  notes?: string;
  what_happened?: string;
  lesson_learned?: string;
}

export interface Outcome {
  id: number;
  campaign_id: number;
  impressions?: number;
  clicks?: number;
  conversions?: number;
  spend?: number;
  revenue?: number;
  ctr?: number;
  cvr?: number;
  cpa?: number;
  roas?: number;
  notes?: string;
  what_happened?: string;
  lesson_learned?: string;
  created_at: string;
}

export interface DashboardStats {
  total_campaigns: number;
  total_memories: number;
  local_evidence: number;
  hindsight_available: boolean;
  total_observations: number;
  total_outcomes: number;
  total_learning_events: number;
  recent_campaigns: RecentCampaign[];
}

export interface RecentCampaign {
  id: number;
  product: string;
  brand: string;
  platform: string;
  status: string;
  memory_mode: boolean;
  created_at: string;
  ctr?: number;
  roas?: number;
}

export interface LearningEvent {
  id: number;
  campaign_id: number;
  lesson: string;
  hindsight_status: string;
  hindsight_memory_id?: string;
  created_at: string;
}

export interface CampaignCreateData {
  brand: string;
  product: string;
  audience: string;
  platform: string;
  objective: string;
  offer?: string;
  budget?: number;
  creative_format: string;
  brand_voice?: string;
  brief_context?: string;
  product_image_path?: string;
  product_image?: File;
  memory_mode: boolean;
}
