"""Campaign generation orchestrator.

The product loop is deliberately explicit:

Brief → Hindsight recall → evidence → Groq decision → product creative → outcome → lesson → retain.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict

from sqlalchemy import select

from ..db import async_session
from ..models import Campaign, GenerationJob, CampaignEvidence, GeneratedAsset, JobStatus
from ..schemas.generation import GroqCampaignResponse
from . import hindsight, evidence as evidence_engine, groq as groq_service, creative as creative_service

logger = logging.getLogger(__name__)


async def _update_job(job_id: int, **kwargs):
    async with async_session() as db:
        result = await db.execute(select(GenerationJob).where(GenerationJob.id == job_id))
        job = result.scalar_one_or_none()
        if job:
            for key, value in kwargs.items():
                setattr(job, key, value)
            await db.commit()


def _campaign_dict(campaign: Campaign) -> Dict[str, Any]:
    return {
        "brand": campaign.brand,
        "product": campaign.product,
        "audience": campaign.audience,
        "platform": campaign.platform,
        "objective": campaign.objective,
        "offer": campaign.offer,
        "budget": campaign.budget,
        "creative_format": campaign.creative_format,
        "brand_voice": campaign.brand_voice,
        "brief_context": campaign.brief_context,
        "product_image_path": campaign.product_image_path,
    }


async def run_campaign_generation(job_id: int, campaign_id: int, memory_mode: bool):
    try:
        await _update_job(job_id, status=JobStatus.QUEUED, current_step="Reading campaign brief", progress=5)

        async with async_session() as db:
            result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
            campaign = result.scalar_one_or_none()
            if not campaign:
                await _update_job(job_id, status=JobStatus.FAILED, error="Campaign not found")
                return
            campaign_data = _campaign_dict(campaign)

        memories = []
        recall_query = ""
        memory_available = False
        memory_error = None

        if memory_mode:
            await _update_job(job_id, status=JobStatus.RECALLING, current_step="Recalling campaign memory from Hindsight", progress=15)
            recall_query = evidence_engine.build_recall_query(campaign_data)
            try:
                memories = await hindsight.recall_campaign_experience(recall_query, limit=8)
                memory_available = True
                logger.info("Hindsight recalled %s memories for campaign %s", len(memories), campaign_id)
            except Exception as exc:
                memory_error = str(exc)
                logger.warning("Hindsight recall failed for campaign %s: %s", campaign_id, exc)

            await _update_job(
                job_id,
                current_step=("Hindsight memory unavailable — generating a transparent baseline" if not memory_available else f"Hindsight recalled {len(memories)} memories"),
                progress=22,
            )

            await _update_job(job_id, status=JobStatus.ANALYZING, current_step="Analyzing historical evidence", progress=30)
            evidence_data = evidence_engine.analyze_evidence(memories, campaign_data)

            async with async_session() as db:
                # Replace evidence for repeat generation rather than accumulating duplicates.
                old = await db.execute(select(CampaignEvidence).where(CampaignEvidence.campaign_id == campaign_id))
                for row in old.scalars().all():
                    await db.delete(row)
                for mem in memories:
                    content = mem.get("content", mem.get("text", ""))
                    relevance = evidence_engine.calculate_relevance_score(content, campaign_data)
                    metrics = evidence_engine.extract_metrics_from_content(content)
                    perf = evidence_engine.classify_performance(metrics)
                    campaign_ref = evidence_engine.extract_campaign_reference(content)
                    db.add(CampaignEvidence(
                        campaign_id=campaign_id,
                        memory_id=str(mem.get("id", mem.get("memory_id", ""))),
                        campaign_reference=campaign_ref,
                        relevance_score=relevance,
                        evidence_type=mem.get("type", mem.get("fact_type", "experience")),
                        summary=f"{campaign_ref}: {perf} performance. {', '.join(f'{k}: {v}' for k, v in metrics.items())}",
                        raw_content=content,
                    ))
                await db.commit()
        else:
            evidence_data = evidence_engine.analyze_evidence([], campaign_data)

        memory_status = "off" if not memory_mode else ("available_with_results" if memory_available and memories else "available_no_results" if memory_available else "unavailable")
        evidence_data["memory_requested"] = memory_mode
        evidence_data["memory_available"] = memory_available
        evidence_data["memory_status"] = memory_status
        evidence_data["memory_error"] = memory_error

        await _update_job(job_id, status=JobStatus.STRATEGIZING, current_step="Building evidence-backed strategy with Groq", progress=45)
        prompt = _build_groq_prompt(campaign_data, evidence_data, memory_mode)

        try:
            groq_result = await groq_service.generate_structured(
                prompt=prompt,
                system_prompt=_get_system_prompt(memory_mode, memory_available),
                response_model=GroqCampaignResponse,
                temperature=0.65,
            )
        except Exception as exc:
            logger.error("LLM generation failed: %s", exc)
            await _update_job(job_id, status=JobStatus.FAILED, error=f"LLM generation failed: {exc}")
            return

        await _update_job(job_id, status=JobStatus.GENERATING, current_step="Creating advertisement strategy and product creative brief", progress=65)
        await asyncio.sleep(0.2)

        why_data = {
            "memories_recalled": evidence_data.get("memories_recalled", 0),
            "relevant_campaigns": evidence_data.get("relevant_campaigns", 0),
            "memory_requested": memory_mode,
            "memory_available": memory_available,
            "memory_status": memory_status,
            "memory_error": memory_error,
            "high_performing": evidence_data.get("high_performing", []),
            "underperforming": evidence_data.get("underperforming", []),
            "positive_patterns": evidence_data.get("positive_patterns", []),
            "negative_patterns": evidence_data.get("negative_patterns", []),
            "conflicts": evidence_data.get("conflicts", []),
            "evidence_items": evidence_data.get("evidence_items", []),
            "recall_query": recall_query,
            "summary": evidence_data.get("summary", ""),
        }

        strategy_data = {
            "core_insight": groq_result.get("core_insight", ""),
            "messaging_angle": groq_result.get("messaging_angle", ""),
            "creative_direction": groq_result.get("creative_direction", ""),
            "creative_concept": groq_result.get("creative_concept", ""),
            "evidence_reasoning": groq_result.get("evidence_reasoning", ""),
            "memory_influence": groq_result.get(
                "memory_influence",
                "Memory was intentionally not used for this campaign." if not memory_mode or not memory_available else "No specific memory influence was stated by the model; review the evidence above.",
            ),
            "risks_uncertainties": groq_result.get("risks_uncertainties", []),
        }
        ad_data = {
            "headline": groq_result.get("headline", ""),
            "primary_copy": groq_result.get("primary_copy", ""),
            "cta": groq_result.get("cta", ""),
        }
        storyboard_data = groq_result.get("storyboard", [])
        campaign_data["creative_concept"] = strategy_data["creative_concept"]
        campaign_data["creative_direction"] = strategy_data["creative_direction"]
        campaign_data["memory_influence"] = strategy_data["memory_influence"]

        async with async_session() as db:
            result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
            campaign = result.scalar_one()
            campaign.strategy = json.dumps(strategy_data)
            campaign.generated_ad = json.dumps(ad_data)
            campaign.storyboard = json.dumps(storyboard_data)
            campaign.why_campaign = json.dumps(why_data)
            campaign.status = "completed"
            for asset_type, content in (("strategy", strategy_data), ("ad_copy", ad_data), ("storyboard", storyboard_data)):
                db.add(GeneratedAsset(campaign_id=campaign_id, asset_type=asset_type, content=json.dumps(content)))
            await db.commit()

        fmt_lower = str(campaign_data.get("creative_format") or "").lower()
        if "carousel" in fmt_lower:
            creative_step = "Generating 3 product-grounded carousel posters"
        else:
            creative_step = "Generating product-grounded poster"
        await _update_job(job_id, status=JobStatus.RENDERING, current_step=creative_step, progress=82)
        creative_result = None
        try:
            product_image = None
            if campaign_data.get("product_image_path"):
                from pathlib import Path
                candidate = Path(campaign_data["product_image_path"])
                if candidate.exists():
                    product_image = candidate
            creative_result = await creative_service.generate_creative(
                campaign_id=campaign_id,
                storyboard=storyboard_data if isinstance(storyboard_data, list) else [],
                campaign=campaign_data,
                ad=ad_data,
                product_image=product_image,
            )
            async with async_session() as db:
                if creative_result.get("assets"):
                    for item in creative_result["assets"]:
                        db.add(GeneratedAsset(
                            campaign_id=campaign_id,
                            asset_type=item.get("asset_type", "static_image"),
                            content=json.dumps(item),
                            file_path=item.get("file_path"),
                            metadata_json=json.dumps({k: v for k, v in item.items() if k != "file_path"}),
                        ))
                else:
                    asset_type = "carousel_image" if "carousel" in fmt_lower else "static_image"
                    db.add(GeneratedAsset(
                        campaign_id=campaign_id,
                        asset_type=asset_type,
                        content=json.dumps(creative_result),
                        file_path=creative_result.get("file_path"),
                        metadata_json=json.dumps({k: v for k, v in creative_result.items() if k != "file_path"}),
                    ))
                await db.commit()
        except Exception as exc:
            # A visual rendering failure must not erase the memory/strategy result.
            logger.exception("Creative rendering failed: %s", exc)
            creative_result = {"status": "failed", "provider": "creative-router", "error": str(exc)}

        full_result = {
            "strategy": strategy_data,
            "ad": ad_data,
            "storyboard": storyboard_data,
            "why_campaign": why_data,
            "creative": creative_result,
            "reel": None,
            "memory_mode": memory_mode,
        }
        await _update_job(job_id, status=JobStatus.COMPLETED, current_step="Campaign + product creative ready", progress=100, result=json.dumps(full_result))
        logger.info("Campaign %s generation completed", campaign_id)

    except Exception as exc:
        logger.exception("Campaign generation failed: %s", exc)
        await _update_job(job_id, status=JobStatus.FAILED, error=str(exc))


def _get_system_prompt(memory_mode: bool, memory_available: bool) -> str:
    base = (
        "You are DevAd, an advertising strategist and short-form creative director. "
        "Create a product-specific advertising campaign and production-ready creative. For the final zero-cost build, design static or carousel product advertising only. "
        "Never invent historical performance data."
    )
    if memory_mode and memory_available:
        return base + " Use only the supplied Hindsight evidence when making memory-based claims. Explain which evidence changed the strategy."
    if memory_mode and not memory_available:
        return base + " Hindsight was requested but unavailable. Do not claim memory informed the strategy; clearly produce a baseline from the brief."
    return base + " Memory is intentionally OFF. Produce a baseline from the brief only."


def _build_groq_prompt(campaign: Dict[str, Any], evidence: Dict[str, Any], memory_mode: bool) -> str:
    evidence_block = "No historical evidence available."
    if memory_mode and evidence.get("memory_available") and evidence.get("memories_recalled", 0):
        evidence_block = json.dumps({
            "summary": evidence.get("summary", ""),
            "high_performing": evidence.get("high_performing", []),
            "underperforming": evidence.get("underperforming", []),
            "positive_patterns": evidence.get("positive_patterns", []),
            "negative_patterns": evidence.get("negative_patterns", []),
            "conflicts": evidence.get("conflicts", []),
            "evidence_items": evidence.get("evidence_items", []),
        }, ensure_ascii=False)

    return f"""Create a complete, product-specific advertisement for this brief. The selected creative format is {campaign.get('creative_format', 'video')}.

BRIEF
Brand: {campaign['brand']}
Product: {campaign['product']}
Audience: {campaign['audience']}
Platform: {campaign['platform']}
Objective: {campaign['objective']}
Offer: {campaign.get('offer') or 'N/A'}
Budget: {campaign.get('budget') or 'N/A'}
Brand voice: {campaign.get('brand_voice') or 'Clear and confident'}
Context: {campaign.get('brief_context') or 'N/A'}
Product reference image: {'provided — preserve its exact identity in visuals' if campaign.get('product_image_path') else 'not provided'}

MEMORY/EVIDENCE
{evidence_block}

STATIC CREATIVE RULES
- The selected final creative is a static poster or a 3-slide carousel.
- Make the concept specific to the actual product category and target audience.
- The uploaded product photo is the exact product identity; never invent packaging, logos or product variants.
- Headlines and offers must be concise because the application renders exact text locally.
- For carousel formats, make each of the three concepts materially different: hero/product, benefit/problem, and proof/offer/CTA.
- If memory evidence exists, make at least one creative decision visibly traceable to it.

Return JSON with:
core_insight, messaging_angle, creative_direction, headline, primary_copy, cta, creative_concept,
storyboard (optional creative blueprint; omit for simple static ads unless useful),
evidence_reasoning, memory_influence, risks_uncertainties.
"""
