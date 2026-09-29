from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CampaignCreate(BaseModel):
    brand: str = Field(..., min_length=1, max_length=200)
    product: str = Field(..., min_length=1, max_length=200)
    audience: str = Field(..., min_length=1, max_length=500)
    platform: str = Field(..., min_length=1, max_length=100)
    objective: str = Field(..., min_length=1, max_length=100)
    offer: Optional[str] = None
    budget: Optional[float] = None
    creative_format: str = Field(..., min_length=1, max_length=200)
    brand_voice: Optional[str] = None
    brief_context: Optional[str] = None
    product_image_path: Optional[str] = None
    memory_mode: bool = True


class CampaignMetricResponse(BaseModel):
    impressions: Optional[int] = None
    clicks: Optional[int] = None
    conversions: Optional[int] = None
    spend: Optional[float] = None
    revenue: Optional[float] = None
    ctr: Optional[float] = None
    cvr: Optional[float] = None
    cpa: Optional[float] = None
    roas: Optional[float] = None
    
    model_config = {"from_attributes": True}


class CampaignEvidenceResponse(BaseModel):
    id: int
    memory_id: Optional[str] = None
    campaign_reference: Optional[str] = None
    relevance_score: Optional[float] = None
    evidence_type: Optional[str] = None
    summary: Optional[str] = None
    
    model_config = {"from_attributes": True}


class GeneratedAssetResponse(BaseModel):
    id: int
    asset_type: str
    content: Optional[str] = None
    file_path: Optional[str] = None
    metadata_json: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CampaignResponse(BaseModel):
    id: int
    brand: str
    product: str
    audience: str
    platform: str
    objective: str
    offer: Optional[str] = None
    budget: Optional[float] = None
    creative_format: str
    brand_voice: Optional[str] = None
    brief_context: Optional[str] = None
    product_image_path: Optional[str] = None
    memory_mode: bool
    status: str
    strategy: Optional[str] = None
    generated_ad: Optional[str] = None
    storyboard: Optional[str] = None
    why_campaign: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    metrics: Optional[CampaignMetricResponse] = None
    evidence: List[CampaignEvidenceResponse] = []
    assets: List[GeneratedAssetResponse] = []
    
    model_config = {"from_attributes": True}


class CampaignListResponse(BaseModel):
    id: int
    brand: str
    product: str
    audience: str
    platform: str
    objective: str
    creative_format: str
    memory_mode: bool
    status: str
    created_at: datetime
    metrics: Optional[CampaignMetricResponse] = None
    
    model_config = {"from_attributes": True}
