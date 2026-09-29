from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class OutcomeCreate(BaseModel):
    impressions: Optional[int] = Field(None, ge=0)
    clicks: Optional[int] = Field(None, ge=0)
    conversions: Optional[int] = Field(None, ge=0)
    spend: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None
    what_happened: Optional[str] = None
    lesson_learned: Optional[str] = None


class OutcomeResponse(BaseModel):
    learning_status: Optional[str] = None
    lesson: Optional[str] = None
    id: int
    campaign_id: int
    impressions: Optional[int] = None
    clicks: Optional[int] = None
    conversions: Optional[int] = None
    spend: Optional[float] = None
    revenue: Optional[float] = None
    ctr: Optional[float] = None
    cvr: Optional[float] = None
    cpa: Optional[float] = None
    roas: Optional[float] = None
    notes: Optional[str] = None
    what_happened: Optional[str] = None
    lesson_learned: Optional[str] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class LearningEventResponse(BaseModel):
    id: int
    campaign_id: int
    lesson: str
    hindsight_status: str
    hindsight_memory_id: Optional[str] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    total_campaigns: int = 0
    total_memories: int = 0  # Hindsight memory units, not local evidence rows.
    local_evidence: int = 0
    hindsight_available: bool = False
    total_observations: int = 0
    total_outcomes: int = 0
    total_learning_events: int = 0
    recent_campaigns: list = []


class LessonResponse(BaseModel):
    lesson: str = Field(..., min_length=10, max_length=600)
    confidence: str = "medium"
    reusable_guidance: str = ""
