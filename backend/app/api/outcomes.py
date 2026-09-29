from typing import List
import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..db import get_db
from ..models import (
    Campaign,
    Outcome,
    LearningEvent,
    CampaignMetric,
)
from ..schemas.outcome import (
    OutcomeCreate,
    OutcomeResponse,
    LearningEventResponse,
    LessonResponse,
)
from ..services.hindsight import (
    retain_campaign_outcome,
    RETAINED_SENTINEL,
)
from ..services import groq as groq_service


logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Metric calculation
# ---------------------------------------------------------------------------

def calculate_metrics(
    impressions,
    clicks,
    conversions,
    spend,
    revenue,
):
    """
    Calculate standard advertising performance metrics.
    """

    metrics = {}

    if (
        impressions is not None
        and impressions > 0
        and clicks is not None
    ):
        metrics["ctr"] = round(
            (clicks / impressions) * 100,
            2,
        )

    if (
        clicks is not None
        and clicks > 0
        and conversions is not None
    ):
        metrics["cvr"] = round(
            (conversions / clicks) * 100,
            2,
        )

    if (
        conversions is not None
        and conversions > 0
        and spend is not None
    ):
        metrics["cpa"] = round(
            spend / conversions,
            2,
        )

    if (
        spend is not None
        and spend > 0
        and revenue is not None
    ):
        metrics["roas"] = round(
            revenue / spend,
            2,
        )

    return metrics


# ---------------------------------------------------------------------------
# Record outcome
# ---------------------------------------------------------------------------

@router.post(
    "/campaigns/{campaign_id}/outcome",
    response_model=OutcomeResponse,
)
async def record_outcome(
    campaign_id: int,
    data: OutcomeCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Record campaign performance and retain the resulting experience
    in Hindsight.

    Flow:

        Campaign
          ↓
        Outcome
          ↓
        Metrics
          ↓
        Lesson
          ↓
        Hindsight Retain
          ↓
        LearningEvent
    """

    # -----------------------------------------------------------------------
    # Load campaign
    # -----------------------------------------------------------------------

    result = await db.execute(
        select(Campaign)
        .where(Campaign.id == campaign_id)
    )

    campaign = result.scalar_one_or_none()

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail=f"Campaign {campaign_id} not found.",
        )

    # -----------------------------------------------------------------------
    # Calculate metrics
    # -----------------------------------------------------------------------

    calculated_metrics = calculate_metrics(
        impressions=data.impressions,
        clicks=data.clicks,
        conversions=data.conversions,
        spend=data.spend,
        revenue=data.revenue,
    )

    # -----------------------------------------------------------------------
    # Create outcome
    # -----------------------------------------------------------------------

    outcome = Outcome(
        campaign_id=campaign_id,
        impressions=data.impressions,
        clicks=data.clicks,
        conversions=data.conversions,
        spend=data.spend,
        revenue=data.revenue,
        ctr=calculated_metrics.get("ctr"),
        cvr=calculated_metrics.get("cvr"),
        cpa=calculated_metrics.get("cpa"),
        roas=calculated_metrics.get("roas"),
        notes=data.notes,
        what_happened=data.what_happened,
        lesson_learned=data.lesson_learned,
    )

    db.add(outcome)

    # -----------------------------------------------------------------------
    # Update/create CampaignMetric
    # -----------------------------------------------------------------------

    metric_result = await db.execute(
        select(CampaignMetric)
        .where(CampaignMetric.campaign_id == campaign_id)
    )

    campaign_metric = metric_result.scalar_one_or_none()

    if campaign_metric is None:
        campaign_metric = CampaignMetric(
            campaign_id=campaign_id,
        )
        db.add(campaign_metric)

    # Keep the campaign's latest aggregate metric row in sync with the
    # recorded outcome, including the raw totals as well as derived ratios.
    for field in ("impressions", "clicks", "conversions", "spend", "revenue"):
        value = getattr(data, field)
        if value is not None:
            setattr(campaign_metric, field, value)
    for field in ("ctr", "cvr", "cpa", "roas"):
        if field in calculated_metrics:
            setattr(campaign_metric, field, calculated_metrics[field])

    # -----------------------------------------------------------------------
    # Generate lesson
    # -----------------------------------------------------------------------

    lesson_text = await _generate_lesson(
        campaign=campaign,
        data=data,
        metrics=calculated_metrics,
    )

    # -----------------------------------------------------------------------
    # Create LearningEvent
    # -----------------------------------------------------------------------

    learning_event = LearningEvent(
        campaign_id=campaign_id,
        lesson = lesson_text,
        hindsight_status="pending",
    )

    db.add(learning_event)

    # Save the database records first.
    await db.commit()

    await db.refresh(outcome)
    await db.refresh(learning_event)

    # -----------------------------------------------------------------------
    # Build Hindsight memory
    # -----------------------------------------------------------------------

    memory_content = _build_memory_content(
        campaign=campaign,
        data=data,
        metrics=calculated_metrics,
        lesson=lesson_text,
    )

    # -----------------------------------------------------------------------
    # Retain in Hindsight
    # -----------------------------------------------------------------------

    try:
        hindsight_result = await retain_campaign_outcome(
            content=memory_content,
            metadata={
                "source": "DevAd",
                "campaign_id": campaign_id,
                "campaign_product": campaign.product,
                "campaign_platform": campaign.platform,
                "campaign_audience": campaign.audience,
                "event_type": "campaign_outcome",
            },
        )

        # IMPORTANT:
        #
        # Hindsight synchronous Retain can succeed without returning
        # a memory ID. Therefore any non-None result means the request
        # completed successfully.
        if hindsight_result is not None:
            learning_event.hindsight_status = "retained"

            # Only store a real returned identifier.
            #
            # RETAINED_SENTINEL means:
            # "Hindsight accepted and processed the memory, but did not
            # return an individual memory ID."
            if hindsight_result != RETAINED_SENTINEL:
                learning_event.hindsight_memory_id = (
                    hindsight_result
                )
            else:
                learning_event.hindsight_memory_id = None

            logger.info(
                "Campaign outcome retained in Hindsight: "
                "campaign_id=%s result=%s",
                campaign_id,
                hindsight_result,
            )

        else:
            learning_event.hindsight_status = "failed"

            logger.error(
                "Hindsight retain returned no success result: "
                "campaign_id=%s",
                campaign_id,
            )

        await db.commit()

    except Exception as exc:
        logger.exception(
            "Failed to retain campaign outcome in Hindsight: "
            "campaign_id=%s",
            campaign_id,
        )

        learning_event.hindsight_status = "failed"

        await db.commit()

    # -----------------------------------------------------------------------
    # Return outcome + truthful learning status
    # -----------------------------------------------------------------------

    response = OutcomeResponse.model_validate(outcome).model_dump()
    response["learning_status"] = learning_event.hindsight_status
    response["lesson"] = lesson_text
    return response


# ---------------------------------------------------------------------------
# Generate lesson
# ---------------------------------------------------------------------------

async def _generate_lesson(
    campaign,
    data: OutcomeCreate,
    metrics: dict,
) -> str:
    """Generate a reusable lesson with Groq, with a deterministic fallback."""
    if data.lesson_learned and data.lesson_learned.strip():
        return data.lesson_learned.strip()
    if data.what_happened and data.what_happened.strip():
        fallback_seed = data.what_happened.strip()
    else:
        fallback_seed = "No written context was supplied; infer only from the measured metrics."

    prompt = f"""Extract one honest, reusable advertising lesson from this campaign outcome.
Campaign: {campaign.product} by {campaign.brand}
Audience: {campaign.audience}
Platform: {campaign.platform}
Objective: {campaign.objective}
Creative: {campaign.creative_format}
Metrics: {json.dumps(metrics)}
What happened: {fallback_seed}
Return a concise lesson that can guide a future campaign. Do not invent causality that the data does not support."""
    try:
        result = await groq_service.generate_structured(
            prompt=prompt,
            system_prompt="You are a careful performance-marketing analyst. Produce only grounded, reusable lessons.",
            response_model=LessonResponse,
            temperature=0.2,
        )
        lesson = str(result.get("lesson", "")).strip()
        if lesson:
            return lesson
    except Exception as exc:
        logger.warning("LLM lesson generation failed; using deterministic lesson: %s", exc)

    return _deterministic_lesson(metrics)


def _deterministic_lesson(metrics: dict) -> str:
    parts = []
    for key, label in (("ctr", "CTR"), ("cvr", "CVR"), ("cpa", "CPA"), ("roas", "ROAS")):
        if metrics.get(key) is not None:
            suffix = "x" if key == "roas" else "%" if key in {"ctr", "cvr"} else ""
            parts.append(f"{label} was {metrics[key]}{suffix}")
    if not parts:
        return "The campaign outcome was recorded, but there was not enough measured data to identify a specific reusable performance lesson."
    return "Observed campaign performance: " + ", ".join(parts) + ". Compare this outcome with similar audience, platform, objective, and creative conditions before changing strategy."


# ---------------------------------------------------------------------------
# Build Hindsight memory
# ---------------------------------------------------------------------------

def _build_memory_content(
    campaign,
    data: OutcomeCreate,
    metrics: dict,
    lesson: str,
) -> str:
    """
    Build a rich experiential memory for Hindsight.

    The memory intentionally contains:

    - campaign context
    - decision/creative context
    - actual outcome
    - observed behavior
    - lesson
    - future decision guidance

    This allows DevAd to recall not just that a campaign existed,
    but why the result matters for future campaign planning.
    """

    ctr = metrics.get("ctr")
    cvr = metrics.get("cvr")
    cpa = metrics.get("cpa")
    roas = metrics.get("roas")

    notes = (
        data.notes.strip()
        if data.notes
        else "No additional campaign notes provided."
    )

    what_happened = (
        data.what_happened.strip()
        if data.what_happened
        else "No detailed outcome narrative provided."
    )

    metrics_lines = [
        f"Impressions: {data.impressions}",
        f"Clicks: {data.clicks}",
        f"Conversions: {data.conversions}",
        f"Spend: {data.spend}",
        f"Revenue: {data.revenue}",
    ]

    if ctr is not None:
        metrics_lines.append(
            f"CTR: {ctr}%"
        )

    if cvr is not None:
        metrics_lines.append(
            f"CVR: {cvr}%"
        )

    if cpa is not None:
        metrics_lines.append(
            f"CPA: {cpa}"
        )

    if roas is not None:
        metrics_lines.append(
            f"ROAS: {roas}x"
        )

    brand = getattr(campaign, "brand", None)
    product = getattr(campaign, "product", None)
    audience = getattr(campaign, "audience", None)
    platform = getattr(campaign, "platform", None)
    objective = getattr(campaign, "objective", None)
    creative_format = getattr(
        campaign,
        "creative_format",
        None,
    )
    brand_voice = getattr(
        campaign,
        "brand_voice",
        None,
    )
    offer = getattr(
        campaign,
        "offer",
        None,
    )

    return (
        "DEVAD CAMPAIGN EXPERIENCE\n"
        "\n"
        "CAMPAIGN CONTEXT\n"
        f"Campaign ID: {campaign.id}\n"
        f"Brand: {brand or 'N/A'}\n"
        f"Product: {product or 'N/A'}\n"
        f"Target audience: {audience or 'N/A'}\n"
        f"Platform: {platform or 'N/A'}\n"
        f"Objective: {objective or 'N/A'}\n"
        f"Creative format: {creative_format or 'N/A'}\n"
        f"Brand voice: {brand_voice or 'N/A'}\n"
        f"Offer: {offer or 'N/A'}\n"
        "\n"
        "CAMPAIGN OUTCOME\n"
        + "\n".join(metrics_lines)
        + "\n"
        "\n"
        "WHAT HAPPENED\n"
        f"{what_happened}\n"
        "\n"
        "CAMPAIGN NOTES\n"
        f"{notes}\n"
        "\n"
        "LESSON LEARNED\n"
        f"{lesson}\n"
        "\n"
        "FUTURE DECISION GUIDANCE\n"
        f"When planning future campaigns for similar audience/platform/"
        f"objective/creative conditions, consider this experience: "
        f"{lesson}"
    )


# ---------------------------------------------------------------------------
# Get outcomes for a campaign
# ---------------------------------------------------------------------------

@router.get(
    "/campaigns/{campaign_id}/outcomes",
    response_model=List[OutcomeResponse],
)
async def get_campaign_outcomes(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Return all recorded outcomes for a campaign.
    """

    campaign_result = await db.execute(
        select(Campaign)
        .where(Campaign.id == campaign_id)
    )

    campaign = campaign_result.scalar_one_or_none()

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail=f"Campaign {campaign_id} not found.",
        )

    result = await db.execute(
        select(Outcome)
        .where(Outcome.campaign_id == campaign_id)
        .order_by(Outcome.created_at.desc())
    )

    return result.scalars().all()


# ---------------------------------------------------------------------------
# Learning events
# ---------------------------------------------------------------------------

@router.get(
    "/learning-events",
    response_model=List[LearningEventResponse],
)
async def get_learning_events(
    db: AsyncSession = Depends(get_db),
):
    """
    Return learning events so the UI can show the
    Hindsight learning status.
    """

    result = await db.execute(
        select(LearningEvent)
        .order_by(LearningEvent.created_at.desc())
    )

    return result.scalars().all()

@router.post("/campaigns/{campaign_id}/learning/retry")
async def retry_learning(campaign_id: int, db: AsyncSession = Depends(get_db)):
    """Retry Hindsight retention for the latest failed learning event."""
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    event_result = await db.execute(
        select(LearningEvent)
        .where(LearningEvent.campaign_id == campaign_id)
        .order_by(LearningEvent.created_at.desc())
    )
    event = event_result.scalars().first()
    if event is None:
        raise HTTPException(status_code=404, detail="No learning event exists for this campaign")
    if event.hindsight_status == "retained":
        return {"status": "retained", "lesson": event.lesson, "memory_id": event.hindsight_memory_id}

    outcome_result = await db.execute(
        select(Outcome).where(Outcome.campaign_id == campaign_id).order_by(Outcome.created_at.desc())
    )
    outcome = outcome_result.scalars().first()
    if outcome is None:
        raise HTTPException(status_code=400, detail="No outcome exists for this campaign")

    content = _build_memory_content(
        campaign=campaign,
        data=OutcomeCreate(
            impressions=outcome.impressions,
            clicks=outcome.clicks,
            conversions=outcome.conversions,
            spend=outcome.spend,
            revenue=outcome.revenue,
            notes=outcome.notes,
            what_happened=outcome.what_happened,
            lesson_learned=event.lesson,
        ),
        metrics={
            "ctr": outcome.ctr,
            "cvr": outcome.cvr,
            "cpa": outcome.cpa,
            "roas": outcome.roas,
        },
        lesson=event.lesson,
    )
    try:
        retained = await retain_campaign_outcome(
            content=content,
            metadata={"source": "DevAd", "campaign_id": campaign_id, "event_type": "campaign_outcome_retry"},
        )
        event.hindsight_status = "retained"
        event.hindsight_memory_id = None if retained == RETAINED_SENTINEL else retained
        await db.commit()
        return {"status": "retained", "lesson": event.lesson, "memory_id": event.hindsight_memory_id}
    except Exception as exc:
        event.hindsight_status = "failed"
        await db.commit()
        raise HTTPException(status_code=502, detail=f"Hindsight retention failed: {exc}") from exc
