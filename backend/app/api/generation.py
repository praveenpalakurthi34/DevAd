from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db import get_db, async_session
from ..models import Campaign, GenerationJob, JobStatus
from ..schemas.generation import GenerateRequest, GenerationJobResponse
from ..services.orchestrator import run_campaign_generation

router = APIRouter()


@router.post("/campaigns/{campaign_id}/generate", response_model=GenerationJobResponse)
async def generate_campaign(
    campaign_id: int,
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # Verify campaign exists
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Update campaign memory mode
    campaign.memory_mode = request.memory_mode
    campaign.status = "generating"
    
    # Create job
    job = GenerationJob(
        campaign_id=campaign_id,
        status=JobStatus.QUEUED,
        current_step="Reading campaign brief",
        progress=0,
        memory_mode=request.memory_mode,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # Run generation in background
    background_tasks.add_task(run_campaign_generation, job.id, campaign_id, request.memory_mode)
    
    return job


@router.get("/generation/{job_id}", response_model=GenerationJobResponse)
async def get_generation_status(job_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GenerationJob).where(GenerationJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")
    return job
