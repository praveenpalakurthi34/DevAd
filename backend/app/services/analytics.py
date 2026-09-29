"""Analytics service for campaign data analysis."""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from ..models import Campaign, CampaignMetric


async def get_campaign_analytics(db: AsyncSession) -> Dict[str, Any]:
    """Get aggregate analytics across all campaigns."""
    result = await db.execute(
        select(Campaign).options(selectinload(Campaign.metrics))
    )
    campaigns = result.scalars().all()
    
    total = len(campaigns)
    with_metrics = [c for c in campaigns if c.metrics]
    
    avg_ctr = None
    avg_roas = None
    if with_metrics:
        ctrs = [c.metrics.ctr for c in with_metrics if c.metrics.ctr is not None]
        roases = [c.metrics.roas for c in with_metrics if c.metrics.roas is not None]
        if ctrs:
            avg_ctr = round(sum(ctrs) / len(ctrs), 2)
        if roases:
            avg_roas = round(sum(roases) / len(roases), 2)
    
    # Platform breakdown
    platforms = {}
    for c in campaigns:
        p = c.platform
        if p not in platforms:
            platforms[p] = {"count": 0, "avg_ctr": [], "avg_roas": []}
        platforms[p]["count"] += 1
        if c.metrics:
            if c.metrics.ctr is not None:
                platforms[p]["avg_ctr"].append(c.metrics.ctr)
            if c.metrics.roas is not None:
                platforms[p]["avg_roas"].append(c.metrics.roas)
    
    platform_stats = []
    for name, data in platforms.items():
        stat = {"platform": name, "count": data["count"]}
        if data["avg_ctr"]:
            stat["avg_ctr"] = round(sum(data["avg_ctr"]) / len(data["avg_ctr"]), 2)
        if data["avg_roas"]:
            stat["avg_roas"] = round(sum(data["avg_roas"]) / len(data["avg_roas"]), 2)
        platform_stats.append(stat)
    
    return {
        "total_campaigns": total,
        "campaigns_with_metrics": len(with_metrics),
        "avg_ctr": avg_ctr,
        "avg_roas": avg_roas,
        "platform_stats": platform_stats,
    }
