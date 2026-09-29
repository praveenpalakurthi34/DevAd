import logging
import re
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Relevance weights
# ---------------------------------------------------------------------------

RELEVANCE_WEIGHTS = {
    "product_category": 0.30,
    "audience": 0.25,
    "platform": 0.15,
    "objective": 0.15,
    "creative_format": 0.15,
}


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    """Normalize text for comparison."""
    if not text:
        return ""

    return re.sub(
        r"[^a-z0-9\s]",
        "",
        str(text).lower().strip(),
    )


def _word_overlap(a: str, b: str) -> float:
    """Calculate word overlap score between two strings."""
    words_a = set(_normalize(a).split())
    words_b = set(_normalize(b).split())

    if not words_a or not words_b:
        return 0.0

    intersection = words_a & words_b
    union = words_a | words_b

    return len(intersection) / len(union) if union else 0.0


def _memory_content(memory: Dict[str, Any]) -> str:
    """
    Hindsight recall results use `text`, while some internal callers
    may use `content`.
    """
    return str(
        memory.get("content")
        or memory.get("text")
        or ""
    ).strip()


def _extract_campaign_reference(content: str) -> str:
    """
    Extract a useful campaign/brand reference from memory text.

    The Hindsight memories in DevAd commonly contain names such as
    AstraFit, but may not use a literal 'Campaign:' field.
    """

    if not content:
        return "Unknown"

    # Explicit Campaign: field
    campaign_match = re.search(
        r"Campaign\s*:\s*([^\n|.]+)",
        content,
        re.IGNORECASE,
    )

    if campaign_match:
        return campaign_match.group(1).strip()

    # Common DevAd brand/product references
    known_entities = [
        "AstraFit",
    ]

    for entity in known_entities:
        if entity.lower() in content.lower():
            return entity

    # Generic "X campaign" pattern
    generic_match = re.search(
        r"\b([A-Z][A-Za-z0-9&-]{2,})\s+(?:marketing\s+)?campaign\b",
        content,
    )

    if generic_match:
        return generic_match.group(1).strip()

    return "Historical campaign"


# Public alias used by orchestration/UI code.
extract_campaign_reference = _extract_campaign_reference


# ---------------------------------------------------------------------------
# Relevance
# ---------------------------------------------------------------------------

def calculate_relevance_breakdown(
    memory_content: str,
    campaign: Dict[str, Any],
) -> Dict[str, Any]:
    """Return transparent component matches used by the relevance score."""
    content_lower = memory_content.lower()
    product_terms = _normalize(f"{campaign.get('product', '')} {campaign.get('brand', '')}").split()
    product_match = sum(1 for term in product_terms if term in content_lower) / max(len(product_terms), 1)
    audience_match = _word_overlap(campaign.get('audience', ''), content_lower)
    platform_match = _word_overlap(campaign.get('platform', ''), content_lower)
    objective_match = _word_overlap(campaign.get('objective', ''), content_lower)
    format_match = _word_overlap(campaign.get('creative_format', ''), content_lower)
    components = {
        'product_category': round(min(product_match * 1.5, 1.0), 3),
        'audience': round(audience_match, 3),
        'platform': round(platform_match, 3),
        'objective': round(objective_match, 3),
        'creative_format': round(format_match, 3),
    }
    weighted = sum(components[k] * RELEVANCE_WEIGHTS[k] for k in components)
    return {
        'components': components,
        'weighted_score': round(weighted, 3),
        'weights': RELEVANCE_WEIGHTS.copy(),
    }


def calculate_relevance_score(
    memory_content: str,
    campaign: Dict[str, Any],
) -> float:
    """
    Calculate contextual relevance score for a memory against a campaign brief.

    Uses transparent heuristic weights.
    """

    content_lower = memory_content.lower()
    score = 0.0

    # Product/category match
    product_terms = _normalize(
        f"{campaign.get('product', '')} "
        f"{campaign.get('brand', '')}"
    ).split()

    product_match = sum(
        1
        for term in product_terms
        if term in content_lower
    ) / max(len(product_terms), 1)

    score += RELEVANCE_WEIGHTS["product_category"] * min(
        product_match * 1.5,
        1.0,
    )

    # Audience match
    audience_score = _word_overlap(
        campaign.get("audience", ""),
        content_lower,
    )

    score += RELEVANCE_WEIGHTS["audience"] * min(
        audience_score * 2,
        1.0,
    )

    # Platform match
    platform = _normalize(
        campaign.get("platform", "")
    )

    platform_match = (
        1.0
        if platform and platform in content_lower
        else 0.0
    )

    score += RELEVANCE_WEIGHTS["platform"] * platform_match

    # Objective match
    objective = _normalize(
        campaign.get("objective", "")
    )

    objective_match = (
        1.0
        if objective and objective in content_lower
        else 0.0
    )

    score += RELEVANCE_WEIGHTS["objective"] * objective_match

    # Creative format match
    format_score = _word_overlap(
        campaign.get("creative_format", ""),
        content_lower,
    )

    score += RELEVANCE_WEIGHTS["creative_format"] * min(
        format_score * 2,
        1.0,
    )

    return round(min(score, 1.0), 3)


# ---------------------------------------------------------------------------
# Metric extraction
# ---------------------------------------------------------------------------

def _parse_number(value: str) -> Optional[float]:
    """Convert strings such as 420,000 or 2.9 into floats."""
    if value is None:
        return None

    try:
        cleaned = (
            str(value)
            .replace(",", "")
            .replace("₹", "")
            .replace("$", "")
            .strip()
        )

        return float(cleaned)

    except (ValueError, TypeError):
        return None


def extract_metrics_from_content(
    content: str,
) -> Dict[str, Optional[float]]:
    """
    Extract campaign metrics mentioned in Hindsight memory text.

    Supports:
    - CTR
    - CVR
    - ROAS
    - CPA
    - impressions
    - clicks
    - conversions
    - spend
    - revenue

    Also derives:
    - CTR from clicks / impressions
    - CVR from conversions / clicks
    - ROAS from revenue / spend
    """

    metrics: Dict[str, Optional[float]] = {}

    if not content:
        return metrics

    text = str(content)

    # ------------------------------------------------------------------
    # CTR
    # Supports:
    #   CTR: 4.2%
    #   CTR 4.2%
    # ------------------------------------------------------------------

    ctr_match = re.search(
        r"\bCTR\s*[:\-]?\s*([\d.]+)\s*%",
        text,
        re.IGNORECASE,
    )

    if ctr_match:
        metrics["ctr"] = _parse_number(
            ctr_match.group(1)
        )

    # ------------------------------------------------------------------
    # CVR
    # Supports:
    #   CVR: 5.0%
    #   CVR 5.0%
    # ------------------------------------------------------------------

    cvr_match = re.search(
        r"\bCVR\s*[:\-]?\s*([\d.]+)\s*%",
        text,
        re.IGNORECASE,
    )

    if cvr_match:
        metrics["cvr"] = _parse_number(
            cvr_match.group(1)
        )

    # ------------------------------------------------------------------
    # ROAS
    # Supports:
    #   ROAS: 2.9x
    #   ROAS 2.9x
    #   2.90x ROAS
    #   2.9 ROAS
    # ------------------------------------------------------------------

    roas_match = re.search(
        r"(?:"
        r"\bROAS\s*[:\-]?\s*([\d.]+)\s*x?"
        r"|"
        r"\b([\d.]+)\s*x\s*ROAS\b"
        r")",
        text,
        re.IGNORECASE,
    )

    if roas_match:
        roas_value = (
            roas_match.group(1)
            or roas_match.group(2)
        )

        metrics["roas"] = _parse_number(
            roas_value
        )

    # ------------------------------------------------------------------
    # CPA
    # Supports:
    #   CPA: $56.69
    #   CPA $56.69
    #   CPA: ₹56.69
    # ------------------------------------------------------------------

    cpa_match = re.search(
        r"\bCPA\s*[:\-]?\s*(?:₹|\$)?\s*([\d.,]+)",
        text,
        re.IGNORECASE,
    )

    if cpa_match:
        metrics["cpa"] = _parse_number(
            cpa_match.group(1)
        )

    # ------------------------------------------------------------------
    # Impressions
    # Supports:
    #   420,000 impressions
    #   420000 impressions
    # ------------------------------------------------------------------

    impressions_match = re.search(
        r"\b([\d,]+)\s+impressions\b",
        text,
        re.IGNORECASE,
    )

    if impressions_match:
        metrics["impressions"] = _parse_number(
            impressions_match.group(1)
        )

    # ------------------------------------------------------------------
    # Clicks
    # Supports:
    #   17,640 clicks
    #   17640 clicks
    # ------------------------------------------------------------------

    clicks_match = re.search(
        r"\b([\d,]+)\s+clicks\b",
        text,
        re.IGNORECASE,
    )

    if clicks_match:
        metrics["clicks"] = _parse_number(
            clicks_match.group(1)
        )

    # ------------------------------------------------------------------
    # Conversions
    # Supports:
    #   882 conversions
    # ------------------------------------------------------------------

    conversions_match = re.search(
        r"\b([\d,]+)\s+conversions\b",
        text,
        re.IGNORECASE,
    )

    if conversions_match:
        metrics["conversions"] = _parse_number(
            conversions_match.group(1)
        )

    # ------------------------------------------------------------------
    # Spend
    # Supports:
    #   50,000 spend
    #   ₹50,000 spend
    #   $50,000 spend
    #   on a 50,000 spend
    # ------------------------------------------------------------------

    spend_match = re.search(
        r"\b(?:on\s+(?:a\s+)?)?"
        r"(?:₹|\$)?\s*([\d.,]+)\s+spend\b",
        text,
        re.IGNORECASE,
    )

    if spend_match:
        metrics["spend"] = _parse_number(
            spend_match.group(1)
        )

    # ------------------------------------------------------------------
    # Revenue
    # Supports:
    #   ₹145,000 revenue
    #   $145,000 revenue
    #   145,000 revenue
    # ------------------------------------------------------------------

    revenue_match = re.search(
        r"\b(?:₹|\$)?\s*([\d.,]+)\s+revenue\b",
        text,
        re.IGNORECASE,
    )

    if revenue_match:
        metrics["revenue"] = _parse_number(
            revenue_match.group(1)
        )

    # ------------------------------------------------------------------
    # Derived CTR
    #
    # CTR = clicks / impressions * 100
    #
    # AstraFit:
    # 17,640 / 420,000 * 100 = 4.2%
    # ------------------------------------------------------------------

    impressions = metrics.get("impressions")
    clicks = metrics.get("clicks")

    if (
        metrics.get("ctr") is None
        and impressions is not None
        and clicks is not None
        and impressions > 0
    ):
        metrics["ctr"] = round(
            (clicks / impressions) * 100,
            2,
        )

    # ------------------------------------------------------------------
    # Derived CVR
    #
    # CVR = conversions / clicks * 100
    #
    # AstraFit:
    # 882 / 17,640 * 100 = 5.0%
    # ------------------------------------------------------------------

    conversions = metrics.get("conversions")

    if (
        metrics.get("cvr") is None
        and clicks is not None
        and conversions is not None
        and clicks > 0
    ):
        metrics["cvr"] = round(
            (conversions / clicks) * 100,
            2,
        )

    # ------------------------------------------------------------------
    # Derived ROAS
    #
    # ROAS = revenue / spend
    #
    # AstraFit:
    # 145,000 / 50,000 = 2.9x
    # ------------------------------------------------------------------

    spend = metrics.get("spend")
    revenue = metrics.get("revenue")

    if (
        metrics.get("roas") is None
        and revenue is not None
        and spend is not None
        and spend > 0
    ):
        metrics["roas"] = round(
            revenue / spend,
            2,
        )

    # ------------------------------------------------------------------
    # Return only successfully extracted metrics
    # ------------------------------------------------------------------

    return {
        key: value
        for key, value in metrics.items()
        if value is not None
    }


# ---------------------------------------------------------------------------
# Performance classification
# ---------------------------------------------------------------------------

def classify_performance(
    metrics: Dict[str, Optional[float]],
) -> str:
    """
    Classify campaign performance based on available metrics.

    Thresholds are deliberately simple and transparent:
    - ROAS >= 2.5 -> high
    - ROAS >= 1.5 -> medium
    - CTR >= 3% -> high
    - CTR >= 1% -> medium
    - CVR >= 4% -> high
    - CVR >= 2% -> medium
    """

    signals: List[str] = []

    roas = metrics.get("roas")

    if roas is not None:
        if roas >= 2.5:
            signals.append("high")
        elif roas >= 1.5:
            signals.append("medium")
        else:
            signals.append("low")

    ctr = metrics.get("ctr")

    if ctr is not None:
        if ctr >= 3.0:
            signals.append("high")
        elif ctr >= 1.0:
            signals.append("medium")
        else:
            signals.append("low")

    cvr = metrics.get("cvr")

    if cvr is not None:
        if cvr >= 4.0:
            signals.append("high")
        elif cvr >= 2.0:
            signals.append("medium")
        else:
            signals.append("low")

    if not signals:
        return "unknown"

    highs = signals.count("high")
    lows = signals.count("low")

    if highs > lows:
        return "high"

    if lows > highs:
        return "low"

    return "medium"


# ---------------------------------------------------------------------------
# Lesson / strategy detection
# ---------------------------------------------------------------------------

def _extract_positive_lessons(
    content: str,
) -> List[str]:
    """
    Detect useful positive lessons directly from Hindsight memory text.
    """

    content_lower = content.lower()
    patterns: List[str] = []

    positive_rules = [
        (
            ["short-form", "short form"],
            "Short-form content was associated with effective campaign performance.",
        ),
        (
            ["product demonstration", "product demo", "demonstration"],
            "Practical product demonstrations were associated with effective performance.",
        ),
        (
            ["first-purchase discount", "20% discount", "discount"],
            "A clear first-purchase discount/offer was associated with stronger purchase performance.",
        ),
        (
            ["direct cta", "offer-focused cta", "direct offer"],
            "Direct offer-focused CTAs were identified as useful for future campaigns.",
        ),
        (
            ["effective for driving purchases"],
            "The recalled campaign identified this approach as effective for driving purchases.",
        ),
        (
            ["performed well"],
            "The recalled creative approach was identified as performing well.",
        ),
        (
            ["drove conversions"],
            "The recalled approach was associated with driving conversions.",
        ),
        (
            ["future campaigns"],
            "The memory contains a lesson intended to influence future campaign planning.",
        ),
    ]

    for keywords, statement in positive_rules:
        if any(keyword in content_lower for keyword in keywords):
            if statement not in patterns:
                patterns.append(statement)

    return patterns


def extract_patterns(
    memories: List[Dict[str, Any]],
    campaign: Dict[str, Any],
) -> Dict[str, List[str]]:
    """
    Extract positive and negative patterns from campaign memories.

    This now works with both metric memories and lesson/observation
    memories that do not contain numeric performance data.
    """

    positive_patterns: List[str] = []
    negative_patterns: List[str] = []

    high_perf_contents: List[str] = []
    low_perf_contents: List[str] = []

    for mem in memories:
        content = _memory_content(mem)

        metrics = extract_metrics_from_content(content)
        performance = classify_performance(metrics)

        if performance == "high":
            high_perf_contents.append(content)

        elif performance == "low":
            low_perf_contents.append(content)

        # Lessons can be useful even when they contain no metrics.
        for lesson in _extract_positive_lessons(content):
            if lesson not in positive_patterns:
                positive_patterns.append(lesson)

    # ------------------------------------------------------------------
    # Positive patterns from high-performing memories
    # ------------------------------------------------------------------

    pattern_keywords = {
        "direct cta": "Direct CTA performed well.",
        "offer-focused cta": "Offer-focused CTA was identified as effective.",
        "product visible": "Product was visible early in the creative.",
        "first 2 seconds": "Product payoff was emphasized in the first 2 seconds.",
        "lifestyle": "Lifestyle creative approach worked.",
        "ugc": "User-generated content style resonated.",
        "authentic": "Authentic tone performed well.",
        "testimonial": "Testimonials boosted engagement.",
        "discount": "Discount/offer messaging drove conversions.",
        "urgency": "Urgency messaging was effective.",
        "short-form": "Short-form content performed well.",
        "short form": "Short-form content performed well.",
        "fast cuts": "Fast-paced editing engaged viewers.",
        "demonstration": "Product demonstration converted well.",
        "product demo": "Product demonstration converted well.",
    }

    negative_keywords = {
        "feature-heavy": "Feature-heavy opening underperformed.",
        "long intro": "Long introductory sequence lost viewers.",
        "explanatory": "Explanatory/educational approach underperformed.",
        "slow": "Slow pacing lost audience attention.",
        "generic": "Generic messaging did not resonate.",
        "complex": "Complex messaging confused the audience.",
    }

    for content in high_perf_contents:
        content_lower = content.lower()

        for keyword, pattern in pattern_keywords.items():
            if keyword in content_lower and pattern not in positive_patterns:
                positive_patterns.append(pattern)

    for content in low_perf_contents:
        content_lower = content.lower()

        for keyword, pattern in negative_keywords.items():
            if keyword in content_lower and pattern not in negative_patterns:
                negative_patterns.append(pattern)

    return {
        "positive": positive_patterns,
        "negative": negative_patterns,
    }


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def detect_conflicts(
    memories: List[Dict[str, Any]],
) -> List[str]:
    """Detect conflicting evidence in memories."""

    conflicts: List[str] = []

    high_ctr_strategies: List[str] = []
    low_ctr_strategies: List[str] = []

    for mem in memories:
        content = _memory_content(mem)

        metrics = extract_metrics_from_content(content)

        ctr = metrics.get("ctr")

        if ctr is not None and ctr > 3.0:
            if "lifestyle" in content.lower():
                high_ctr_strategies.append("lifestyle")

            if (
                "product demo" in content.lower()
                or "demonstration" in content.lower()
            ):
                high_ctr_strategies.append("product_demo")

        elif ctr is not None and ctr < 1.5:
            if "lifestyle" in content.lower():
                low_ctr_strategies.append("lifestyle")

            if (
                "product demo" in content.lower()
                or "demonstration" in content.lower()
            ):
                low_ctr_strategies.append("product_demo")

    overlaps = (
        set(high_ctr_strategies)
        & set(low_ctr_strategies)
    )

    for strategy in overlaps:
        conflicts.append(
            f"Conflicting evidence: '{strategy}' approach showed "
            f"both high and low CTR in different campaigns. "
            f"Context such as audience, platform, and creative likely matters."
        )

    return conflicts


# ---------------------------------------------------------------------------
# Evidence analysis
# ---------------------------------------------------------------------------

def analyze_evidence(
    memories: List[Dict[str, Any]],
    campaign: Dict[str, Any],
    db_campaigns: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Run the Evidence Engine analysis.

    Returns structured evidence package for Groq and the UI.
    """

    if not memories:
        return {
            "memories_recalled": 0,
            "relevant_campaigns": 0,
            "high_performing": [],
            "underperforming": [],
            "positive_patterns": [],
            "negative_patterns": [],
            "conflicts": [],
            "evidence_items": [],
            "summary": (
                "No historical campaign data available. "
                "Generating baseline campaign."
            ),
            "relevance_breakdown": None,
        }

    # ------------------------------------------------------------------
    # Score memories
    # ------------------------------------------------------------------

    scored_memories: List[Dict[str, Any]] = []

    for mem in memories:
        content = _memory_content(mem)

        relevance = calculate_relevance_score(
            content,
            campaign,
        )

        metrics = extract_metrics_from_content(
            content
        )

        performance = classify_performance(
            metrics
        )

        campaign_name = _extract_campaign_reference(
            content
        )

        scored_memories.append(
            {
                "memory_id": mem.get(
                    "id",
                    mem.get("memory_id", ""),
                ),
                "content": content,
                "relevance_score": relevance,
                "metrics": metrics,
                "performance": performance,
                "evidence_type": mem.get(
                    "type",
                    mem.get("fact_type", "experience"),
                ),
                "campaign_name": campaign_name,
            }
        )

    # ------------------------------------------------------------------
    # Sort by relevance
    # ------------------------------------------------------------------

    scored_memories.sort(
        key=lambda x: x["relevance_score"],
        reverse=True,
    )

    # ------------------------------------------------------------------
    # Classify performance
    # ------------------------------------------------------------------

    high_performing = [
        memory
        for memory in scored_memories
        if memory["performance"] == "high"
    ]

    underperforming = [
        memory
        for memory in scored_memories
        if memory["performance"] == "low"
    ]

    # ------------------------------------------------------------------
    # Extract patterns
    # ------------------------------------------------------------------

    patterns = extract_patterns(
        memories,
        campaign,
    )

    # ------------------------------------------------------------------
    # Detect conflicts
    # ------------------------------------------------------------------

    conflicts = detect_conflicts(
        memories
    )

    # ------------------------------------------------------------------
    # Build evidence items
    # ------------------------------------------------------------------

    evidence_items: List[Dict[str, Any]] = []

    for memory in scored_memories[:10]:
        item = {
            "memory_id": memory["memory_id"],
            "campaign_name": memory["campaign_name"],
            "relevance_score": memory["relevance_score"],
            "performance": memory["performance"],
            "metrics": memory["metrics"],
            "evidence_type": memory["evidence_type"],
            "summary": memory["content"],
            "relevance_breakdown": calculate_relevance_breakdown(memory["content"], campaign),
        }

        evidence_items.append(item)

    # ------------------------------------------------------------------
    # Build summary
    # ------------------------------------------------------------------

    summary_parts = [
        f"{len(scored_memories)} historical memories analyzed."
    ]

    if high_performing:
        summary_parts.append(
            f"{len(high_performing)} high-performing memories identified."
        )

    if underperforming:
        summary_parts.append(
            f"{len(underperforming)} underperforming memories identified."
        )

    if patterns["positive"]:
        summary_parts.append(
            "Positive patterns: "
            + "; ".join(
                patterns["positive"][:4]
            )
            + "."
        )

    if patterns["negative"]:
        summary_parts.append(
            "Patterns to avoid: "
            + "; ".join(
                patterns["negative"][:3]
            )
            + "."
        )

    if conflicts:
        summary_parts.append(
            f"Note: {len(conflicts)} conflicting evidence point(s) detected."
        )

    # ------------------------------------------------------------------
    # Final structured package
    # ------------------------------------------------------------------

    return {
        "memories_recalled": len(scored_memories),

        "relevant_campaigns": len(
            [
                memory
                for memory in scored_memories
                if memory["relevance_score"] > 0.1
            ]
        ),

        "high_performing": [
            {
                "campaign_name": memory["campaign_name"],
                "metrics": memory["metrics"],
                "relevance_score": memory["relevance_score"],
                "evidence_type": memory["evidence_type"],
                "summary": memory["content"],
            }
            for memory in high_performing[:5]
        ],

        "underperforming": [
            {
                "campaign_name": memory["campaign_name"],
                "metrics": memory["metrics"],
                "relevance_score": memory["relevance_score"],
                "evidence_type": memory["evidence_type"],
                "summary": memory["content"],
            }
            for memory in underperforming[:5]
        ],

        "positive_patterns": patterns["positive"],

        "negative_patterns": patterns["negative"],

        "conflicts": conflicts,

        "evidence_items": evidence_items,

        "summary": " ".join(summary_parts),
    }


# ---------------------------------------------------------------------------
# Recall query builder
# ---------------------------------------------------------------------------

def build_recall_query(
    campaign: Dict[str, Any],
) -> str:
    """Build a high-quality recall query for Hindsight."""

    parts = [
        "Find previous campaigns",
    ]

    if campaign.get("creative_format"):
        parts.append(
            f"using {campaign['creative_format']}"
        )

    if campaign.get("platform"):
        parts.append(
            f"on {campaign['platform']}"
        )

    if campaign.get("product") or campaign.get("brand"):
        product_terms = (
            f"{campaign.get('product', '')} "
            f"{campaign.get('brand', '')}"
        ).strip()

        parts.append(
            f"for {product_terms} or similar products"
        )

    if campaign.get("audience"):
        parts.append(
            f"targeting {campaign['audience']}"
        )

    if campaign.get("objective"):
        parts.append(
            f"optimized for {campaign['objective']}"
        )

    parts.append(
        "Return relevant campaign experiences, outcomes, "
        "observations, performance metrics and creative lessons."
    )

    return " ".join(parts)