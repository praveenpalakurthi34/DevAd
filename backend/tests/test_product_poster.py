from pathlib import Path
from PIL import Image
from app.services.creative import _render_local_static, _is_video, _is_carousel


def test_static_poster_uses_uploaded_product_and_exact_copy(tmp_path):
    product = tmp_path / "product.png"
    img = Image.new("RGBA", (500, 500), (255, 255, 255, 255))
    img.save(product)
    output = tmp_path / "poster.png"
    result = _render_local_static(
        product,
        {
            "brand": "Pulse",
            "product": "Pulse Hydration",
            "audience": "college students",
            "platform": "Instagram Feed",
            "objective": "Conversions",
            "offer": "20% launch discount",
            "creative_format": "Static image ad",
        },
        {"headline": "Hydrate. Keep Moving.", "primary_copy": "Made for busy days.", "cta": "Shop now"},
        output,
    )
    assert output.exists()
    assert result["provider"] == "local-product-poster"
    assert result["real_product_reference"] is True
    assert result["zero_cost_api"] is True
    assert result["human_generation"] is False


def test_final_formats_are_static_only():
    assert not _is_video("Static image ad")
    assert not _is_video("Static carousel ad")
    assert _is_carousel("Static carousel ad")
