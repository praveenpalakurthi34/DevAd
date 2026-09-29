from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class GenerateRequest(BaseModel):
    memory_mode: bool = True


class GenerationJobResponse(BaseModel):
    id: int
    campaign_id: int
    status: str
    current_step: Optional[str] = None
    progress: int = 0
    error: Optional[str] = None
    result: Optional[str] = None
    memory_mode: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class StoryboardScene(BaseModel):
    scene_number: int
    time_range: str
    visual: str
    audio: Optional[str] = None
    text_overlay: Optional[str] = None
    purpose: Optional[str] = None
    duration_seconds: Optional[float] = None


class CampaignStrategy(BaseModel):
    core_insight: str
    messaging_angle: str
    creative_direction: str
    creative_concept: Optional[str] = None
    evidence_reasoning: str
    memory_influence: Optional[str] = None
    risks_uncertainties: List[str] = Field(default_factory=list)


class GeneratedAd(BaseModel):
    headline: str
    primary_copy: str
    cta: str


class WhyCampaign(BaseModel):
    memories_recalled: int = 0
    relevant_campaigns: int = 0
    memory_requested: bool = False
    memory_available: bool = False
    memory_status: str = "off"
    memory_error: Optional[str] = None
    high_performing: List[dict] = Field(default_factory=list)
    underperforming: List[dict] = Field(default_factory=list)
    positive_patterns: List[str] = Field(default_factory=list)
    negative_patterns: List[str] = Field(default_factory=list)
    conflicts: List[str] = Field(default_factory=list)
    evidence_items: List[dict] = Field(default_factory=list)


class FullGenerationResult(BaseModel):
    strategy: CampaignStrategy
    ad: GeneratedAd
    storyboard: List[StoryboardScene] = Field(default_factory=list)
    why_campaign: WhyCampaign


# Schema for Groq structured response
class GroqCampaignResponse(BaseModel):
    core_insight: str = Field(..., description="The key strategic insight driving the campaign")
    messaging_angle: str = Field(..., description="The messaging approach")
    creative_direction: str = Field(..., description="How the creative should look and feel")
    headline: str = Field(..., description="The ad headline")
    primary_copy: str = Field(..., description="The main ad copy text")
    cta: str = Field(..., description="Call to action text")
    creative_concept: str = Field(..., description="Overall creative concept description")
    storyboard: List[StoryboardScene] = Field(default_factory=list, description="Optional creative blueprint; final static build does not require video scenes")
    evidence_reasoning: str = Field(..., description="Why this strategy follows from the evidence")
    memory_influence: str = Field(default="", description="One concrete statement describing how recalled memory changed the strategy, or that memory was not used")
    risks_uncertainties: List[str] = Field(default_factory=list, description="Known risks and uncertainties")
