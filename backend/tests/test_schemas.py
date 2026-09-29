import pytest
from pydantic import ValidationError
from app.schemas.campaign import CampaignCreate
from app.schemas.outcome import OutcomeCreate
from app.schemas.generation import GroqCampaignResponse, StoryboardScene


def test_campaign_create_valid():
    data = CampaignCreate(
        brand="Pulse",
        product="Pulse Hydration",
        audience="College students",
        platform="Instagram Reels",
        objective="Conversions",
        creative_format="20-second video",
    )
    assert data.brand == "Pulse"
    assert data.memory_mode is True


def test_campaign_create_missing_required():
    with pytest.raises(ValidationError):
        CampaignCreate(
            brand="Pulse",
            # Missing product, audience, etc.
        )


def test_outcome_create_valid():
    data = OutcomeCreate(
        impressions=100000,
        clicks=5000,
        conversions=250,
        spend=1000.0,
        revenue=5000.0,
    )
    assert data.impressions == 100000


def test_outcome_negative_values():
    with pytest.raises(ValidationError):
        OutcomeCreate(impressions=-100)


def test_groq_response_valid():
    data = GroqCampaignResponse(
        core_insight="Test insight",
        messaging_angle="Test angle",
        creative_direction="Test direction",
        headline="Test Headline",
        primary_copy="Test copy",
        cta="Buy Now",
        creative_concept="Test concept",
        storyboard=[
            StoryboardScene(scene_number=1, time_range="0-5s", visual="Opening"),
        ],
        evidence_reasoning="Test reasoning",
        risks_uncertainties=["Risk 1"],
    )
    assert data.headline == "Test Headline"
