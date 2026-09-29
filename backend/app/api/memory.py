from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db import get_db
from ..models import Campaign, CampaignEvidence
from ..schemas.campaign import CampaignEvidenceResponse
from ..services.hindsight import (
    recall_campaign_experience,
    list_memories,
)
from pydantic import BaseModel
from typing import List, Optional


router = APIRouter()


class RecallRequest(BaseModel):
    query: str
    limit: int = 10


class RecallResponse(BaseModel):
    query: str
    memories: list = []
    total: int = 0
    hindsight_available: bool = True
    error: Optional[str] = None


@router.post("/memory/recall", response_model=RecallResponse)
async def recall_memories(request: RecallRequest):
    try:
        memories = await recall_campaign_experience(
            request.query,
            limit=request.limit,
        )

        return RecallResponse(
            query=request.query,
            memories=memories,
            total=len(memories),
            hindsight_available=True,
        )

    except Exception as e:
        return RecallResponse(
            query=request.query,
            memories=[],
            total=0,
            hindsight_available=False,
            error=str(e),
        )


@router.get("/memory/list")
async def list_hindsight_memories(
    memory_type: Optional[str] = Query(
        default=None,
        description="Optional Hindsight memory type: experience, observation, or world",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
):
    """
    Debug endpoint for inspecting memories currently stored in Hindsight.
    """

    try:
        memories = await list_memories(
            memory_type=memory_type,
            limit=limit,
        )

        return {
            "memory_type": memory_type,
            "count": len(memories),
            "memories": memories,
            "hindsight_available": True,
            "error": None,
        }

    except Exception as e:
        return {
            "memory_type": memory_type,
            "count": 0,
            "memories": [],
            "hindsight_available": False,
            "error": str(e),
        }


@router.get(
    "/campaigns/{campaign_id}/memories",
    response_model=List[CampaignEvidenceResponse],
)
async def get_campaign_memories(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CampaignEvidence)
        .where(CampaignEvidence.campaign_id == campaign_id)
        .order_by(CampaignEvidence.relevance_score.desc())
    )

    return result.scalars().all()


@router.get("/campaigns/{campaign_id}/evidence")
async def get_campaign_evidence(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )

    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(
            status_code=404,
            detail="Campaign not found",
        )

    evidence_result = await db.execute(
        select(CampaignEvidence)
        .where(CampaignEvidence.campaign_id == campaign_id)
        .order_by(CampaignEvidence.relevance_score.desc())
    )

    evidence_list = evidence_result.scalars().all()

    import json

    why_data = (
        json.loads(campaign.why_campaign)
        if campaign.why_campaign
        else None
    )

    return {
        "campaign_id": campaign_id,
        "memory_mode": campaign.memory_mode,
        "evidence": [
            CampaignEvidenceResponse.model_validate(e).model_dump()
            for e in evidence_list
        ],
        "why_campaign": why_data,
    }


@router.get("/campaigns/{campaign_id}/insights")
async def get_campaign_insights(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )

    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(
            status_code=404,
            detail="Campaign not found",
        )

    import json

    return {
        "campaign_id": campaign_id,
        "strategy": (
            json.loads(campaign.strategy)
            if campaign.strategy
            else None
        ),
        "why_campaign": (
            json.loads(campaign.why_campaign)
            if campaign.why_campaign
            else None
        ),
        "generated_ad": (
            json.loads(campaign.generated_ad)
            if campaign.generated_ad
            else None
        ),
        "storyboard": (
            json.loads(campaign.storyboard)
            if campaign.storyboard
            else None
        ),
    }