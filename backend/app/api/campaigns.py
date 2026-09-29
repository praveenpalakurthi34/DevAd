from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from pathlib import Path
from ..db import get_db
from ..models import Campaign, CampaignMetric, GeneratedAsset
from ..schemas.campaign import CampaignCreate, CampaignResponse, CampaignListResponse

PRODUCT_ROOT = Path(__file__).resolve().parents[2] / "generated" / "products"

router = APIRouter()


@router.post("/campaigns", response_model=CampaignResponse)
async def create_campaign(data: CampaignCreate, db: AsyncSession = Depends(get_db)):
    payload = data.model_dump()
    if payload.get("product_image_path"):
        candidate = Path(payload["product_image_path"]).resolve()
        if PRODUCT_ROOT.resolve() not in candidate.parents or not candidate.exists():
            raise HTTPException(status_code=400, detail="Invalid product image reference. Upload the product image through DevAd first.")
        payload["product_image_path"] = str(candidate)
    campaign = Campaign(**payload)
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    # Reload with relationships
    result = await db.execute(
        select(Campaign)
        .options(selectinload(Campaign.metrics), selectinload(Campaign.evidence), selectinload(Campaign.generated_assets))
        .where(Campaign.id == campaign.id)
    )
    campaign = result.scalar_one()
    return campaign


@router.get("/campaigns", response_model=List[CampaignListResponse])
async def list_campaigns(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Campaign)
        .options(selectinload(Campaign.metrics))
        .order_by(Campaign.created_at.desc())
    )
    return result.scalars().all()


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Campaign)
        .options(
            selectinload(Campaign.metrics),
            selectinload(Campaign.evidence),
            selectinload(Campaign.generated_assets),
        )
        .where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.post("/campaigns/{campaign_id}/creative/render")
async def render_campaign_creative(campaign_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Re-render the stored product creative without regenerating the strategy."""
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if not campaign.storyboard or not campaign.generated_ad:
        raise HTTPException(status_code=400, detail="Generate the campaign strategy before rendering the creative.")

    import json
    from ..services import creative as creative_service
    try:
        storyboard = json.loads(campaign.storyboard)
        ad = json.loads(campaign.generated_ad)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Stored creative data is invalid.") from exc

    product_image = Path(campaign.product_image_path) if campaign.product_image_path else None
    if product_image and not product_image.exists():
        product_image = None
    try:
        strategy = json.loads(campaign.strategy or "{}")
    except json.JSONDecodeError:
        strategy = {}
    result = await creative_service.generate_creative(
        campaign_id=campaign_id,
        storyboard=storyboard,
        campaign={
            "brand": campaign.brand,
            "product": campaign.product,
            "audience": campaign.audience,
            "platform": campaign.platform,
            "objective": campaign.objective,
            "offer": campaign.offer,
            "brand_voice": campaign.brand_voice,
            "brief_context": campaign.brief_context,
            "creative_format": campaign.creative_format,
            "product_image_path": campaign.product_image_path,
            "creative_concept": strategy.get("creative_concept", ""),
            "creative_direction": strategy.get("creative_direction", ""),
            "memory_influence": strategy.get("memory_influence", ""),
        },
        ad=ad,
        product_image=product_image,
    )
    asset_type = "carousel_image" if "carousel" in campaign.creative_format.lower() else "static_image"
    db.add(GeneratedAsset(
        campaign_id=campaign_id,
        asset_type=asset_type,
        content=json.dumps(result),
        file_path=result.get("file_path"),
        metadata_json=json.dumps({k: v for k, v in result.items() if k != "file_path"}),
    ))
    await db.commit()
    return result
