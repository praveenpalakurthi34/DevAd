from app.services.creative import _is_video, _is_carousel
from app.schemas.campaign import CampaignCreate


def test_final_static_formats_do_not_route_to_video():
    assert not _is_video("Static image ad")
    assert not _is_video("Static carousel ad")
    assert _is_carousel("Static carousel ad")
    assert not _is_carousel("Static image ad")


def test_product_image_reference_is_supported():
    campaign = CampaignCreate(
        brand="Pulse",
        product="Pulse Hydration",
        audience="Adults",
        platform="Instagram Feed",
        objective="Conversions",
        creative_format="Static image ad",
        product_image_path="C:/devad/generated/products/product_demo.jpg",
    )
    assert campaign.product_image_path.endswith("product_demo.jpg")
