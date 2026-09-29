from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from .db import Base


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    RECALLING = "recalling"
    ANALYZING = "analyzing"
    STRATEGIZING = "strategizing"
    GENERATING = "generating"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    brand = Column(String(200), nullable=False)
    product = Column(String(200), nullable=False)
    audience = Column(String(500), nullable=False)
    platform = Column(String(100), nullable=False)
    objective = Column(String(100), nullable=False)
    offer = Column(String(500), nullable=True)
    budget = Column(Float, nullable=True)
    creative_format = Column(String(200), nullable=False)
    brand_voice = Column(String(500), nullable=True)
    brief_context = Column(Text, nullable=True)
    product_image_path = Column(String(500), nullable=True)
    memory_mode = Column(Boolean, default=True)
    status = Column(String(20), default=CampaignStatus.DRAFT)
    
    # Generated content
    strategy = Column(Text, nullable=True)  # JSON
    generated_ad = Column(Text, nullable=True)  # JSON
    storyboard = Column(Text, nullable=True)  # JSON
    why_campaign = Column(Text, nullable=True)  # JSON
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    metrics = relationship("CampaignMetric", back_populates="campaign", uselist=False, cascade="all, delete-orphan")
    evidence = relationship("CampaignEvidence", back_populates="campaign", cascade="all, delete-orphan")
    outcomes = relationship("Outcome", back_populates="campaign", cascade="all, delete-orphan")
    learning_events = relationship("LearningEvent", back_populates="campaign", cascade="all, delete-orphan")
    generation_jobs = relationship("GenerationJob", back_populates="campaign", cascade="all, delete-orphan")
    generated_assets = relationship("GeneratedAsset", back_populates="campaign", cascade="all, delete-orphan")


class CampaignMetric(Base):
    __tablename__ = "campaign_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    impressions = Column(Integer, nullable=True)
    clicks = Column(Integer, nullable=True)
    conversions = Column(Integer, nullable=True)
    spend = Column(Float, nullable=True)
    revenue = Column(Float, nullable=True)
    ctr = Column(Float, nullable=True)
    cvr = Column(Float, nullable=True)
    cpa = Column(Float, nullable=True)
    roas = Column(Float, nullable=True)
    
    campaign = relationship("Campaign", back_populates="metrics")


class GenerationJob(Base):
    __tablename__ = "generation_jobs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    status = Column(String(20), default=JobStatus.QUEUED)
    current_step = Column(String(100), nullable=True)
    progress = Column(Integer, default=0)  # 0-100
    error = Column(Text, nullable=True)
    result = Column(Text, nullable=True)  # JSON
    memory_mode = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    campaign = relationship("Campaign", back_populates="generation_jobs")


class CampaignEvidence(Base):
    __tablename__ = "campaign_evidence"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    memory_id = Column(String(200), nullable=True)
    campaign_reference = Column(String(200), nullable=True)
    relevance_score = Column(Float, nullable=True)
    evidence_type = Column(String(50), nullable=True)  # experience, observation, world_fact
    summary = Column(Text, nullable=True)
    raw_content = Column(Text, nullable=True)
    
    campaign = relationship("Campaign", back_populates="evidence")


class GeneratedAsset(Base):
    __tablename__ = "generated_assets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    asset_type = Column(String(50), nullable=False)  # strategy, ad_copy, storyboard, static_image, carousel_image
    content = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    campaign = relationship("Campaign", back_populates="generated_assets")


class Outcome(Base):
    __tablename__ = "outcomes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    impressions = Column(Integer, nullable=True)
    clicks = Column(Integer, nullable=True)
    conversions = Column(Integer, nullable=True)
    spend = Column(Float, nullable=True)
    revenue = Column(Float, nullable=True)
    ctr = Column(Float, nullable=True)
    cvr = Column(Float, nullable=True)
    cpa = Column(Float, nullable=True)
    roas = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    what_happened = Column(Text, nullable=True)
    lesson_learned = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    campaign = relationship("Campaign", back_populates="outcomes")


class LearningEvent(Base):
    __tablename__ = "learning_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    lesson = Column(Text, nullable=False)
    hindsight_status = Column(String(20), default="pending")  # pending, retained, failed
    hindsight_memory_id = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    campaign = relationship("Campaign", back_populates="learning_events")
