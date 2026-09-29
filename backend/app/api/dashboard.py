from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from ..db import get_db
from ..models import Campaign, Outcome, LearningEvent, CampaignEvidence, GenerationJob, JobStatus
from ..schemas.outcome import DashboardStats
from ..services.seed import seed_demo_data, reset_demo_data
from ..services.hindsight import count_memories
from ..services.orchestrator import run_campaign_generation

router = APIRouter()


@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    # Count campaigns
    campaigns_count = await db.scalar(select(func.count(Campaign.id)))
    
    # Hindsight memory count is queried from Hindsight itself. Local evidence is tracked separately.
    local_evidence_count = await db.scalar(select(func.count(CampaignEvidence.id)))
    hindsight_available = False
    memories_count = 0
    try:
        memories_count = await count_memories()
        hindsight_available = True
    except Exception:
        pass

    # Count local evidence with type='observation' for the evidence view.
    observations_count = await db.scalar(
        select(func.count(CampaignEvidence.id))
        .where(CampaignEvidence.evidence_type == "observation")
    )
    
    # Count outcomes
    outcomes_count = await db.scalar(select(func.count(Outcome.id)))
    
    # Count learning events
    learning_count = await db.scalar(select(func.count(LearningEvent.id)))
    
    # Recent campaigns
    result = await db.execute(
        select(Campaign)
        .options(selectinload(Campaign.metrics))
        .order_by(Campaign.created_at.desc())
        .limit(5)
    )
    recent = result.scalars().all()
    recent_list = []
    for c in recent:
        recent_list.append({
            "id": c.id,
            "product": c.product,
            "brand": c.brand,
            "platform": c.platform,
            "status": c.status,
            "memory_mode": c.memory_mode,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "ctr": c.metrics.ctr if c.metrics else None,
            "roas": c.metrics.roas if c.metrics else None,
        })
    
    return DashboardStats(
        total_campaigns=campaigns_count or 0,
        total_memories=memories_count or 0,
        local_evidence=local_evidence_count or 0,
        hindsight_available=hindsight_available,
        total_observations=observations_count or 0,
        total_outcomes=outcomes_count or 0,
        total_learning_events=learning_count or 0,
        recent_campaigns=recent_list,
    )


@router.post("/demo/seed")
async def seed_data(db: AsyncSession = Depends(get_db)):
    count = await seed_demo_data(db)
    return {"status": "ok", "campaigns_seeded": count}


@router.post("/demo/reset")
async def reset_data(db: AsyncSession = Depends(get_db)):
    await reset_demo_data(db)
    return {"status": "ok", "message": "Local demo data reset. Hindsight memories were intentionally preserved."}

@router.post("/demo/learning-loop")
async def create_learning_loop_demo(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create a fresh related campaign whose generation recalls seeded experience."""
    result = await db.execute(
        select(Campaign).where(Campaign.product.ilike("%Pulse Hydration%")).order_by(Campaign.created_at.asc())
    )
    source = result.scalars().first()
    if source is None:
        raise HTTPException(status_code=400, detail="Load Demo Data first so the learning loop has prior experience to recall.")

    product_image_path = source.product_image_path
    if not product_image_path:
        from pathlib import Path
        from PIL import Image, ImageDraw
        product_root = Path(__file__).resolve().parents[2] / "generated" / "products"
        product_root.mkdir(parents=True, exist_ok=True)
        demo_image = product_root / "pulse_demo_product.png"
        if not demo_image.exists():
            img = Image.new("RGBA", (800, 800), (248, 250, 252, 255))
            draw = ImageDraw.Draw(img)
            draw.rounded_rectangle((275, 100, 525, 700), radius=65, fill=(36, 126, 214, 255))
            draw.rounded_rectangle((315, 70, 485, 145), radius=25, fill=(28, 40, 55, 255))
            draw.text((350, 360), "PULSE", fill=(255, 255, 255, 255))
            img.save(demo_image)
        product_image_path = str(demo_image)

    campaign = Campaign(
        brand=source.brand,
        product="Pulse Hydration Campus Poster",
        audience="College students and campus fitness enthusiasts",
        platform="Instagram Feed",
        objective="Conversions",
        offer="20% launch discount",
        budget=3500.0,
        creative_format="Static image ad",
        brand_voice="Energetic, direct, authentic",
        brief_context="Learning-loop demo: create a new product poster using what previous Pulse campaigns taught DevAd.",
        memory_mode=True,
        product_image_path=product_image_path,
        status="generating",
    )
    db.add(campaign)
    await db.flush()
    job = GenerationJob(
        campaign_id=campaign.id,
        status=JobStatus.QUEUED,
        current_step="Starting learning-loop demo",
        progress=0,
        memory_mode=True,
    )
    db.add(job)
    await db.commit()
    await db.refresh(campaign)
    await db.refresh(job)
    background_tasks.add_task(run_campaign_generation, job.id, campaign.id, True)
    return {"status": "started", "campaign_id": campaign.id, "job_id": job.id}

