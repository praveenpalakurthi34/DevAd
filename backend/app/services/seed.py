"""Demo data seeding service."""
import json
import logging
import copy
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from ..models import Campaign, CampaignMetric, Outcome, LearningEvent, CampaignEvidence, GenerationJob, GeneratedAsset
from ..services.hindsight import retain_campaign_experience

logger = logging.getLogger(__name__)

DEMO_CAMPAIGNS = [
    {
        "brand": "Pulse Hydration",
        "product": "Pulse Hydration",
        "audience": "College-age fitness enthusiasts",
        "platform": "Instagram Reels",
        "objective": "Conversions",
        "offer": "20% launch discount",
        "budget": 5000.0,
        "creative_format": "20-second short-form video",
        "brand_voice": "Energetic, direct, authentic",
        "brief_context": "Summer campaign for campus fitness market",
        "memory_mode": True,
        "status": "completed",
        "strategy": json.dumps({
            "core_insight": "College athletes value immediate energy payoff over ingredient education",
            "messaging_angle": "Instant energy for your next set",
            "creative_direction": "Fast lifestyle cuts with product payoff in first 2 seconds",
            "creative_concept": "Quick gym montage showing product in action",
            "evidence_reasoning": "Based on direct performance correlation with immediate product visibility",
            "risks_uncertainties": ["Summer seasonality may affect results"],
        }),
        "generated_ad": json.dumps({
            "headline": "Your Workout's Missing Ingredient",
            "primary_copy": "Pulse Hydration hits different. Clean energy, zero crash, designed for athletes who don't stop. Grab your 20% launch discount before it's gone.",
            "cta": "Shop Now — 20% Off",
        }),
        "metrics": {
            "impressions": 245000,
            "clicks": 12005,
            "conversions": 768,
            "spend": 4800.0,
            "revenue": 23040.0,
            "ctr": 4.9,
            "cvr": 6.4,
            "cpa": 6.25,
            "roas": 4.8,
        },
        "lesson": "Immediate product payoff in first 2 seconds and direct CTA were associated with strong performance for college fitness audience on Instagram Reels.",
    },
    {
        "brand": "Pulse Hydration",
        "product": "Pulse Hydration Night Run",
        "audience": "Urban night runners aged 22-35",
        "platform": "TikTok",
        "objective": "Brand Awareness",
        "offer": "Free sample with first order",
        "budget": 3500.0,
        "creative_format": "15-second short-form video",
        "brand_voice": "Bold, adventurous, inspiring",
        "brief_context": "Night running community campaign",
        "memory_mode": True,
        "status": "completed",
        "strategy": json.dumps({
            "core_insight": "Night runners form tight communities around shared experience",
            "messaging_angle": "Own the night",
            "creative_direction": "Cinematic night city running with neon aesthetics",
            "creative_concept": "Solo runner transitioning to group, product as the connector",
            "evidence_reasoning": "Community-driven content resonates with running audiences",
            "risks_uncertainties": ["Niche audience may limit scale"],
        }),
        "generated_ad": json.dumps({
            "headline": "Own the Night",
            "primary_copy": "When the city sleeps, you run. Pulse Hydration keeps you going through every midnight mile. Join the night run crew.",
            "cta": "Get Your Free Sample",
        }),
        "metrics": {
            "impressions": 380000,
            "clicks": 15200,
            "conversions": 456,
            "spend": 3200.0,
            "revenue": 8640.0,
            "ctr": 4.0,
            "cvr": 3.0,
            "cpa": 7.02,
            "roas": 2.7,
        },
        "lesson": "Community-driven content resonated well for awareness but conversion optimization needed. Night aesthetic visuals drove high engagement but did not directly translate to purchases.",
    },
    {
        "brand": "Pulse Hydration",
        "product": "Pulse Campus Energy",
        "audience": "College students during exam season",
        "platform": "Instagram Stories",
        "objective": "Conversions",
        "offer": "Study pack bundle — 30% off",
        "budget": 2800.0,
        "creative_format": "10-second story ad",
        "brand_voice": "Relatable, supportive, witty",
        "brief_context": "Exam season energy campaign on campus",
        "memory_mode": True,
        "status": "completed",
        "strategy": json.dumps({
            "core_insight": "Students need reliable energy without the jitters during high-pressure periods",
            "messaging_angle": "Your study session's secret weapon",
            "creative_direction": "Relatable library/study scenes with product placement",
            "creative_concept": "Split screen: with vs without Pulse during studying",
            "evidence_reasoning": "Relatable student scenarios drive engagement in this demographic",
            "risks_uncertainties": ["Seasonal — limited to exam periods"],
        }),
        "generated_ad": json.dumps({
            "headline": "Finals Week? We Got You.",
            "primary_copy": "Clean focus. No crash. Pulse Campus Energy was made for the 2am study grind. Study pack bundles now 30% off.",
            "cta": "Grab the Study Pack",
        }),
        "metrics": {
            "impressions": 185000,
            "clicks": 8510,
            "conversions": 621,
            "spend": 2600.0,
            "revenue": 14280.0,
            "ctr": 4.6,
            "cvr": 7.3,
            "cpa": 4.19,
            "roas": 5.49,
        },
        "lesson": "Relatable student scenarios with clear product benefit drove exceptional conversion rates. Bundle offers performed strongly during high-intent periods like exam season.",
    },
    {
        "brand": "Fizz",
        "product": "Fizz Campus Fest",
        "audience": "College students at campus events",
        "platform": "Instagram Reels",
        "objective": "Brand Awareness",
        "offer": "Free Fizz at partner events",
        "budget": 8000.0,
        "creative_format": "30-second short-form video",
        "brand_voice": "Fun, social, energetic",
        "brief_context": "Campus festival sponsorship campaign",
        "memory_mode": True,
        "status": "completed",
        "strategy": json.dumps({
            "core_insight": "College events are prime moments for trial and social sharing",
            "messaging_angle": "The official drink of campus good times",
            "creative_direction": "UGC-style festival montage with product integration",
            "creative_concept": "Multi-campus event highlights reel",
            "evidence_reasoning": "Event-based content drives organic sharing and trial",
            "risks_uncertainties": ["Dependent on event partnerships"],
        }),
        "generated_ad": json.dumps({
            "headline": "Campus Runs on Fizz",
            "primary_copy": "From tailgates to late nights, Fizz is where the fun is. Find us at your next campus event — free samples all semester.",
            "cta": "Find Events Near You",
        }),
        "metrics": {
            "impressions": 520000,
            "clicks": 18200,
            "conversions": 364,
            "spend": 7500.0,
            "revenue": 10920.0,
            "ctr": 3.5,
            "cvr": 2.0,
            "cpa": 20.60,
            "roas": 1.46,
        },
        "lesson": "UGC-style event content drove high impressions and engagement but conversions were low. Awareness objective was partially met but cost per acquisition was high. Event-dependent strategy limits scalability.",
    },
    {
        "brand": "Fizz",
        "product": "Fizz Feature Grid",
        "audience": "Health-conscious millennials",
        "platform": "Facebook Feed",
        "objective": "Conversions",
        "offer": "Subscribe & save 25%",
        "budget": 4500.0,
        "creative_format": "Static carousel ad",
        "brand_voice": "Clean, informative, trustworthy",
        "brief_context": "Feature-focused campaign highlighting ingredients",
        "memory_mode": True,
        "status": "completed",
        "strategy": json.dumps({
            "core_insight": "Health-conscious buyers want transparent ingredient information",
            "messaging_angle": "Know exactly what you're drinking",
            "creative_direction": "Clean feature-heavy grid layout with ingredient callouts",
            "creative_concept": "Carousel of ingredient benefits with product shots",
            "evidence_reasoning": "Feature-heavy approach for health audience on Facebook",
            "risks_uncertainties": ["Feature-heavy creative may not capture attention quickly"],
        }),
        "generated_ad": json.dumps({
            "headline": "Clean Ingredients. Real Energy.",
            "primary_copy": "No artificial colors. No synthetic caffeine. Just clean, plant-based energy that your body actually wants. See what's inside every can of Fizz.",
            "cta": "Subscribe & Save 25%",
        }),
        "metrics": {
            "impressions": 290000,
            "clicks": 3190,
            "conversions": 127,
            "spend": 4200.0,
            "revenue": 3810.0,
            "ctr": 1.1,
            "cvr": 3.98,
            "cpa": 33.07,
            "roas": 0.91,
        },
        "lesson": "Feature-heavy opening on Facebook carousel underperformed significantly. Low CTR suggests the informational approach failed to capture attention in feed. Health-conscious audience may respond better to lifestyle imagery paired with brief feature highlights.",
    },
    {
        "brand": "Nova Protein",
        "product": "Nova Protein Launch",
        "audience": "Gym-going professionals aged 25-40",
        "platform": "YouTube Shorts",
        "objective": "Conversions",
        "offer": "First bag 40% off",
        "budget": 6000.0,
        "creative_format": "20-second short-form video",
        "brand_voice": "Premium, confident, results-driven",
        "brief_context": "Product launch for premium protein powder",
        "memory_mode": True,
        "status": "completed",
        "strategy": json.dumps({
            "core_insight": "Professional athletes want results-focused messaging, not hype",
            "messaging_angle": "Premium fuel for premium results",
            "creative_direction": "High-production gym footage with athlete testimonials",
            "creative_concept": "Before/after training montage with product integration",
            "evidence_reasoning": "Testimonial-driven content with product demonstration converted well for fitness audiences",
            "risks_uncertainties": ["Premium positioning may limit initial trial"],
        }),
        "generated_ad": json.dumps({
            "headline": "Fuel the Difference",
            "primary_copy": "Nova Protein: 30g premium whey, zero fillers, designed for athletes who measure results. Your first bag is 40% off.",
            "cta": "Try Nova — 40% Off",
        }),
        "metrics": {
            "impressions": 310000,
            "clicks": 13330,
            "conversions": 840,
            "spend": 5600.0,
            "revenue": 25200.0,
            "ctr": 4.3,
            "cvr": 6.3,
            "cpa": 6.67,
            "roas": 4.5,
        },
        "lesson": "Product demonstration with testimonials drove strong conversions for premium fitness products. Direct CTA with aggressive discount overcame premium pricing hesitation. YouTube Shorts performed well for gym audience.",
    },
    {
        "brand": "Nova Protein",
        "product": "Nova Morning Routine",
        "audience": "Working professionals aged 28-45",
        "platform": "Instagram Feed",
        "objective": "Brand Awareness",
        "offer": "Free shaker with subscription",
        "budget": 3000.0,
        "creative_format": "Static image ad",
        "brand_voice": "Aspirational, clean, lifestyle",
        "brief_context": "Lifestyle integration campaign for morning protein routine",
        "memory_mode": True,
        "status": "completed",
        "strategy": json.dumps({
            "core_insight": "Busy professionals want protein to fit seamlessly into their morning",
            "messaging_angle": "Start every morning stronger",
            "creative_direction": "Clean lifestyle photography — kitchen, protein shake, heading out",
            "creative_concept": "Day-in-the-life morning routine featuring Nova",
            "evidence_reasoning": "Lifestyle creative worked for awareness campaigns targeting professionals",
            "risks_uncertainties": ["Static image may underperform vs video in feed"],
        }),
        "generated_ad": json.dumps({
            "headline": "Your Morning, Upgraded",
            "primary_copy": "30 seconds to mix. 30g of protein. Zero excuses. Nova fits your morning routine like it was made for it. Free premium shaker when you subscribe.",
            "cta": "Start Your Routine",
        }),
        "metrics": {
            "impressions": 420000,
            "clicks": 10080,
            "conversions": 201,
            "spend": 2800.0,
            "revenue": 6030.0,
            "ctr": 2.4,
            "cvr": 2.0,
            "cpa": 13.93,
            "roas": 2.15,
        },
        "lesson": "Lifestyle creative achieved solid awareness metrics but conversion was moderate. Static image on Instagram feed had decent CTR but video likely would have performed better. Subscription CTA may have been too high-commitment for awareness stage.",
    },
    {
        "brand": "AquaFlow",
        "product": "AquaFlow Electrolyte",
        "audience": "Marathon runners and endurance athletes",
        "platform": "YouTube Pre-roll",
        "objective": "Conversions",
        "offer": "Race day bundle — buy 2 get 1 free",
        "budget": 7000.0,
        "creative_format": "15-second pre-roll ad",
        "brand_voice": "Scientific, credible, performance-focused",
        "brief_context": "Pre-marathon season campaign",
        "memory_mode": True,
        "status": "completed",
        "strategy": json.dumps({
            "core_insight": "Endurance athletes trust science-backed nutrition claims",
            "messaging_angle": "Scientifically formulated for the last mile",
            "creative_direction": "Data-driven visuals with athlete performance shots",
            "creative_concept": "Split screen showing hydration data alongside race footage",
            "evidence_reasoning": "Scientific credibility drives purchase in endurance sports",
            "risks_uncertainties": ["15-second format limits information delivery"],
        }),
        "generated_ad": json.dumps({
            "headline": "Formulated for the Last Mile",
            "primary_copy": "AquaFlow Electrolyte: optimal sodium-potassium ratio for maximum absorption. Trusted by 10,000+ marathon finishers. Get your race day bundle.",
            "cta": "Build Your Race Bundle",
        }),
        "metrics": {
            "impressions": 180000,
            "clicks": 5400,
            "conversions": 378,
            "spend": 6500.0,
            "revenue": 18900.0,
            "ctr": 3.0,
            "cvr": 7.0,
            "cpa": 17.20,
            "roas": 2.91,
        },
        "lesson": "Scientific credibility messaging drove strong conversion rate for endurance athletes. Pre-roll format was challenging for complex messaging but targeted audience had high intent. Bundle offers performed well for repeat-purchase products.",
    },
    {
        "brand": "AquaFlow",
        "product": "AquaFlow Recovery",
        "audience": "CrossFit enthusiasts aged 22-38",
        "platform": "TikTok",
        "objective": "Conversions",
        "offer": "50% off first order",
        "budget": 4000.0,
        "creative_format": "20-second short-form video",
        "brand_voice": "Intense, authentic, community-driven",
        "brief_context": "Recovery product launch for CrossFit community",
        "memory_mode": True,
        "status": "completed",
        "strategy": json.dumps({
            "core_insight": "CrossFit athletes prioritize recovery as part of their training identity",
            "messaging_angle": "Recover like you train — with intensity",
            "creative_direction": "Raw WOD footage transitioning to recovery with product",
            "creative_concept": "CrossFit WOD ending → immediate recovery with AquaFlow",
            "evidence_reasoning": "Authentic community content resonates with CrossFit audience",
            "risks_uncertainties": ["CrossFit community can be skeptical of newcomer brands"],
        }),
        "generated_ad": json.dumps({
            "headline": "Recover As Hard As You Train",
            "primary_copy": "After the WOD, recovery starts. AquaFlow Recovery: engineered for athletes who push limits. 50% off your first order — no excuses.",
            "cta": "Recover Now — 50% Off",
        }),
        "metrics": {
            "impressions": 275000,
            "clicks": 12375,
            "conversions": 742,
            "spend": 3800.0,
            "revenue": 18550.0,
            "ctr": 4.5,
            "cvr": 6.0,
            "cpa": 5.12,
            "roas": 4.88,
        },
        "lesson": "Authentic community-driven content with product demonstration drove exceptional performance for CrossFit audience. Aggressive discount with direct CTA converted very well. TikTok short-form with fast cuts and raw footage outperformed polished content.",
    },
    {
        "brand": "ZenTea",
        "product": "ZenTea Focus Blend",
        "audience": "Remote workers and digital nomads",
        "platform": "Instagram Feed",
        "objective": "Conversions",
        "offer": "Starter kit — $19.99",
        "budget": 2500.0,
        "creative_format": "Static carousel ad",
        "brand_voice": "Calm, sophisticated, mindful",
        "brief_context": "Focus tea for remote work productivity",
        "memory_mode": True,
        "status": "completed",
        "strategy": json.dumps({
            "core_insight": "Remote workers seek calm productivity without stimulant crash",
            "messaging_angle": "Focus without the frenzy",
            "creative_direction": "Minimalist workspace setup with tea as hero",
            "creative_concept": "Clean desk, open laptop, ZenTea — the productive workspace",
            "evidence_reasoning": "Minimalist aesthetic resonates with digital worker audience",
            "risks_uncertainties": ["Carousel may be too slow for Instagram feed engagement"],
        }),
        "generated_ad": json.dumps({
            "headline": "Focus Without the Frenzy",
            "primary_copy": "L-theanine + premium matcha = calm, sustained focus. ZenTea Focus Blend was crafted for the deep work sessions that matter. Start with our $19.99 starter kit.",
            "cta": "Get Your Starter Kit",
        }),
        "metrics": {
            "impressions": 155000,
            "clicks": 4030,
            "conversions": 282,
            "spend": 2400.0,
            "revenue": 5640.0,
            "ctr": 2.6,
            "cvr": 7.0,
            "cpa": 8.51,
            "roas": 2.35,
        },
        "lesson": "Minimalist creative with clear product benefit drove good conversion rate but moderate ROAS. Low-price entry point (starter kit) reduced purchase barrier. Carousel performed adequately but video format likely would improve CTR.",
    },
    {
        "brand": "ZenTea",
        "product": "ZenTea Evening Calm",
        "audience": "Stressed professionals aged 30-50",
        "platform": "Facebook Feed",
        "objective": "Brand Awareness",
        "offer": "Free sample pack",
        "budget": 2000.0,
        "creative_format": "Single image ad",
        "brand_voice": "Warm, comforting, gentle",
        "brief_context": "Evening relaxation tea campaign",
        "memory_mode": True,
        "status": "completed",
        "strategy": json.dumps({
            "core_insight": "Stressed professionals need permission to slow down",
            "messaging_angle": "Your evening reset button",
            "creative_direction": "Warm evening lighting, cozy setting, tea as ritual",
            "creative_concept": "Cozy evening scene with tea steaming on side table",
            "evidence_reasoning": "Emotional comfort messaging works for relaxation products",
            "risks_uncertainties": ["Facebook feed competition may reduce visibility"],
        }),
        "generated_ad": json.dumps({
            "headline": "Tonight, Just Breathe",
            "primary_copy": "Chamomile, lavender, and a moment that's just for you. ZenTea Evening Calm — because you deserve the reset. Free sample pack available.",
            "cta": "Claim Your Free Sample",
        }),
        "metrics": {
            "impressions": 340000,
            "clicks": 5100,
            "conversions": 102,
            "spend": 1900.0,
            "revenue": 2040.0,
            "ctr": 1.5,
            "cvr": 2.0,
            "cpa": 18.63,
            "roas": 1.07,
        },
        "lesson": "Comfort-focused messaging achieved awareness goals but conversion was weak. Single image format on Facebook was not engaging enough. Free sample offer generated some trial but overall ROAS barely broke even. Consider video format and more targeted audience.",
    },
    {
        "brand": "Pulse Hydration",
        "product": "Pulse Hydration Yoga",
        "audience": "Yoga practitioners aged 25-45",
        "platform": "Instagram Reels",
        "objective": "Conversions",
        "offer": "Yoga starter pack — 35% off",
        "budget": 3500.0,
        "creative_format": "20-second short-form video",
        "brand_voice": "Calm, balanced, mindful",
        "brief_context": "Hydration product positioned for yoga community",
        "memory_mode": True,
        "status": "completed",
        "strategy": json.dumps({
            "core_insight": "Yoga practitioners value balance and natural ingredients",
            "messaging_angle": "Hydration in harmony with your practice",
            "creative_direction": "Slow, intentional movements with natural lighting",
            "creative_concept": "Studio yoga flow with product integration between poses",
            "evidence_reasoning": "Slow intentional creative for mindful audiences may differ from fast-cut fitness content",
            "risks_uncertainties": ["Slow pacing may underperform on Reels algorithm", "Hydration positioning for yoga is less obvious than intense sports"],
        }),
        "generated_ad": json.dumps({
            "headline": "Flow. Hydrate. Repeat.",
            "primary_copy": "Pure electrolytes for your practice. Pulse Hydration Yoga is formulated for mindful athletes who care about what goes in. Yoga starter pack now 35% off.",
            "cta": "Shop the Yoga Pack",
        }),
        "metrics": {
            "impressions": 165000,
            "clicks": 2805,
            "conversions": 112,
            "spend": 3200.0,
            "revenue": 3920.0,
            "ctr": 1.7,
            "cvr": 3.99,
            "cpa": 28.57,
            "roas": 1.23,
        },
        "lesson": "Slow-paced creative underperformed on Instagram Reels where fast cuts dominate. Yoga audience had moderate conversion but low CTR suggests the creative didn't capture attention in the feed. Hydration positioning for yoga was less compelling than for intense sports. Consider faster-paced creative even for calm audiences on short-form platforms.",
    },
]


async def seed_demo_data(db: AsyncSession) -> int:
    """Seed demo campaign data once; use reset before reseeding."""
    existing = await db.scalar(select(Campaign.id).limit(1))
    if existing is not None:
        return 0
    count = 0
    
    for original_campaign_data in DEMO_CAMPAIGNS:
        # Never mutate the module-level demo fixtures; seed can be run repeatedly.
        campaign_data = copy.deepcopy(original_campaign_data)
        metrics_data = campaign_data.pop("metrics", {})
        lesson = campaign_data.pop("lesson", "")
        
        # Create campaign
        campaign = Campaign(**campaign_data)
        db.add(campaign)
        await db.flush()  # Get the ID
        
        # Add metrics
        if metrics_data:
            metric = CampaignMetric(campaign_id=campaign.id, **metrics_data)
            db.add(metric)
        
        # Add outcome
        if metrics_data:
            outcome = Outcome(
                campaign_id=campaign.id,
                impressions=metrics_data.get("impressions"),
                clicks=metrics_data.get("clicks"),
                conversions=metrics_data.get("conversions"),
                spend=metrics_data.get("spend"),
                revenue=metrics_data.get("revenue"),
                ctr=metrics_data.get("ctr"),
                cvr=metrics_data.get("cvr"),
                cpa=metrics_data.get("cpa"),
                roas=metrics_data.get("roas"),
                lesson_learned=lesson,
            )
            db.add(outcome)
        
        # Add learning event
        if lesson:
            learning = LearningEvent(
                campaign_id=campaign.id,
                lesson=lesson,
                hindsight_status="pending",
            )
            db.add(learning)
        
        # Attempt to retain in Hindsight
        try:
            memory_content = _build_memory_content(campaign_data, metrics_data, lesson)
            memory_id = await retain_campaign_experience(memory_content)
            if memory_id:
                # Update learning event
                result = await db.execute(
                    select(LearningEvent)
                    .where(LearningEvent.campaign_id == campaign.id)
                    .order_by(LearningEvent.created_at.desc())
                )
                le = result.scalars().first()
                if le:
                    le.hindsight_status = "retained"
                    le.hindsight_memory_id = str(memory_id)
        except Exception as e:
            logger.warning(f"Failed to retain seed data in Hindsight: {e}")
        
        count += 1
    
    await db.commit()
    return count


def _build_memory_content(campaign_data, metrics_data, lesson):
    metrics_str = ""
    if metrics_data:
        parts = []
        if metrics_data.get("ctr"): parts.append(f"CTR {metrics_data['ctr']}%")
        if metrics_data.get("cvr"): parts.append(f"CVR {metrics_data['cvr']}%")
        if metrics_data.get("cpa"): parts.append(f"CPA ${metrics_data['cpa']}")
        if metrics_data.get("roas"): parts.append(f"ROAS {metrics_data['roas']}x")
        metrics_str = ", ".join(parts)
    
    strategy = {}
    if campaign_data.get("strategy"):
        import json
        strategy = json.loads(campaign_data["strategy"])
    
    ad = {}
    if campaign_data.get("generated_ad"):
        import json
        ad = json.loads(campaign_data["generated_ad"])
    
    return (
        f"Campaign: {campaign_data['product']}.\n"
        f"Brand: {campaign_data['brand']}.\n"
        f"Audience: {campaign_data['audience']}.\n"
        f"Platform: {campaign_data['platform']}.\n"
        f"Objective: {campaign_data['objective']}.\n"
        f"Creative format: {campaign_data['creative_format']}.\n"
        f"Offer: {campaign_data.get('offer', 'N/A')}.\n"
        f"Creative direction: {strategy.get('creative_direction', 'N/A')}.\n"
        f"Headline: {ad.get('headline', 'N/A')}.\n"
        f"CTA: {ad.get('cta', 'N/A')}.\n"
        f"Outcome: {metrics_str}.\n"
        f"Lesson: {lesson}"
    )


async def reset_demo_data(db: AsyncSession):
    """Reset all demo data."""
    await db.execute(delete(LearningEvent))
    await db.execute(delete(Outcome))
    await db.execute(delete(CampaignEvidence))
    await db.execute(delete(GeneratedAsset))
    await db.execute(delete(GenerationJob))
    await db.execute(delete(CampaignMetric))
    await db.execute(delete(Campaign))
    await db.commit()
