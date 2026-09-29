import pytest
from app.services.evidence import (
    calculate_relevance_score,
    extract_metrics_from_content,
    classify_performance,
    extract_patterns,
    detect_conflicts,
    analyze_evidence,
    build_recall_query,
)


def test_calculate_relevance_score_full_match():
    content = "Campaign for Pulse Hydration targeting college-age fitness enthusiasts on Instagram Reels for conversions using 20-second short-form video"
    campaign = {
        "product": "Pulse Hydration",
        "brand": "Pulse",
        "audience": "college-age fitness enthusiasts",
        "platform": "Instagram Reels",
        "objective": "conversions",
        "creative_format": "20-second short-form video",
    }
    score = calculate_relevance_score(content, campaign)
    assert score > 0.5


def test_calculate_relevance_score_no_match():
    content = "Campaign for luxury watches targeting seniors on radio"
    campaign = {
        "product": "Pulse Hydration",
        "brand": "Pulse",
        "audience": "college-age fitness enthusiasts",
        "platform": "Instagram Reels",
        "objective": "conversions",
        "creative_format": "20-second short-form video",
    }
    score = calculate_relevance_score(content, campaign)
    assert score < 0.3


def test_extract_metrics_from_content():
    content = "Outcome: CTR 4.9%, CVR 6.4%, CPA $6.25, ROAS 4.8x"
    metrics = extract_metrics_from_content(content)
    assert metrics["ctr"] == 4.9
    assert metrics["cvr"] == 6.4
    assert metrics["roas"] == 4.8
    assert metrics["cpa"] == 6.25


def test_classify_performance_high():
    assert classify_performance({"roas": 4.5, "ctr": 4.0}) == "high"


def test_classify_performance_low():
    assert classify_performance({"roas": 0.9, "ctr": 0.8}) == "low"


def test_classify_performance_unknown():
    assert classify_performance({}) == "unknown"


def test_build_recall_query():
    campaign = {
        "product": "Pulse Hydration",
        "brand": "Pulse",
        "audience": "college students",
        "platform": "TikTok",
        "objective": "conversions",
        "creative_format": "short-form video",
    }
    query = build_recall_query(campaign)
    assert "Pulse Hydration" in query
    assert "TikTok" in query
    assert "college students" in query


def test_analyze_evidence_empty():
    result = analyze_evidence([], {"product": "Test"})
    assert result["memories_recalled"] == 0
    assert "baseline" in result["summary"].lower() or "no historical" in result["summary"].lower()


def test_analyze_evidence_with_memories():
    memories = [
        {"id": "1", "content": "Campaign: Pulse Summer. CTR 4.9%, ROAS 4.8x. Direct CTA worked well.", "type": "experience"},
        {"id": "2", "content": "Campaign: Fizz Grid. CTR 1.1%, ROAS 0.91x. Feature-heavy opening failed.", "type": "experience"},
    ]
    campaign = {"product": "Pulse", "brand": "Pulse", "audience": "students", "platform": "Instagram", "objective": "conversions", "creative_format": "video"}
    result = analyze_evidence(memories, campaign)
    assert result["memories_recalled"] == 2
    assert len(result["high_performing"]) > 0 or len(result["underperforming"]) > 0


def test_relevance_breakdown_exposes_components():
    from app.services.evidence import calculate_relevance_breakdown
    result = calculate_relevance_breakdown(
        "Pulse Hydration campaign for college students on Instagram Reels for conversions",
        {
            "brand": "Pulse",
            "product": "Pulse Hydration",
            "audience": "college students",
            "platform": "Instagram Reels",
            "objective": "conversions",
            "creative_format": "short-form video",
        },
    )
    assert set(result["components"]) == {
        "product_category", "audience", "platform", "objective", "creative_format"
    }
    assert 0 <= result["weighted_score"] <= 1
