"""Zero-cost product-grounded creative renderer.

Static and carousel ads are rendered locally from the user's real product photo.
No paid image/video API is required. Groq supplies the creative direction/copy;
PIL creates the final poster with exact text and the exact uploaded product photo.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, List

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[2]
CREATIVE_ROOT = ROOT / "generated" / "creative"
CREATIVE_ROOT.mkdir(parents=True, exist_ok=True)


def _is_video(fmt: str) -> bool:
    return any(x in (fmt or "").lower() for x in ("video", "reel", "pre-roll", "preroll"))


def _is_carousel(fmt: str) -> bool:
    return "carousel" in (fmt or "").lower()


def _font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> List[str]:
    words = str(text or "").split()
    if not words:
        return []
    lines: List[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _palette(image: Image.Image) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    sample = image.convert("RGB").resize((1, 1), Image.Resampling.LANCZOS)
    r, g, b = sample.getpixel((0, 0))
    # Keep the generated backdrop soft and readable rather than copying a harsh source color.
    base = (max(18, int(r * 0.72)), max(22, int(g * 0.72)), max(28, int(b * 0.72)))
    accent = (min(255, r + 45), min(255, g + 45), min(255, b + 45))
    return base, accent


def _category_style(campaign: Dict[str, Any]) -> tuple[tuple[int, int, int], tuple[int, int, int], str]:
    text = " ".join(str(campaign.get(k) or "") for k in ("product", "brief_context", "audience")).lower()
    if any(k in text for k in ("hydration", "drink", "beverage", "water", "juice")):
        return (14, 55, 78), (47, 196, 190), "fresh, energetic"
    if any(k in text for k in ("skin", "sunscreen", "serum", "cream", "beauty", "cosmetic")):
        return (92, 54, 55), (242, 164, 137), "clean, premium"
    if any(k in text for k in ("laptop", "phone", "tech", "software", "headphone", "earbuds")):
        return (18, 28, 50), (84, 151, 255), "modern, technical"
    if any(k in text for k in ("food", "snack", "coffee", "restaurant", "meal")):
        return (76, 43, 25), (237, 159, 74), "warm, appetizing"
    if any(k in text for k in ("shoe", "fashion", "shirt", "clothing", "apparel")):
        return (38, 35, 46), (192, 166, 255), "editorial, confident"
    return (28, 31, 42), (120, 170, 230), "premium, confident"


def _canvas_size(platform: str) -> tuple[int, int]:
    return (1080, 1920) if "story" in (platform or "").lower() else (1080, 1350)


def _remove_light_border_background(img: Image.Image) -> Image.Image:
    """Remove only a light background connected to the image border.

    This keeps white/light product details that are enclosed by the product while
    turning common white e-commerce backdrops transparent. If the corners are not
    light, the original image is returned unchanged.
    """
    rgba = img.convert("RGBA")
    small = rgba.copy()
    small.thumbnail((320, 320), Image.Resampling.LANCZOS)
    w, h = small.size
    px = small.load()
    corners = [px[0, 0][:3], px[w - 1, 0][:3], px[0, h - 1][:3], px[w - 1, h - 1][:3]]
    avg = tuple(sum(c[i] for c in corners) // 4 for i in range(3))
    if min(avg) < 205 or max(avg) - min(avg) > 28:
        return rgba

    from collections import deque
    q = deque()
    seen = set()
    for x, y in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        q.append((x, y))
        seen.add((x, y))

    def is_bg(x: int, y: int) -> bool:
        r, g, b, _ = px[x, y]
        return r > 188 and g > 188 and b > 188 and max(r, g, b) - min(r, g, b) < 48 and abs(r - avg[0]) + abs(g - avg[1]) + abs(b - avg[2]) < 125

    while q:
        x, y = q.popleft()
        if not is_bg(x, y):
            continue
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen:
                seen.add((nx, ny))
                q.append((nx, ny))

    if len(seen) < (w * h) * 0.08:
        return rgba

    mask_small = Image.new("L", (w, h), 255)
    mp = mask_small.load()
    for x, y in seen:
        if is_bg(x, y):
            mp[x, y] = 0
    mask = mask_small.resize(rgba.size, Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(0.8))
    rgba.putalpha(mask)
    return rgba


def _fit_product(source: Image.Image, max_w: int, max_h: int) -> Image.Image:
    img = _remove_light_border_background(source.convert("RGBA"))
    img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    return img


def _render_local_static(product_image: Path, campaign: Dict[str, Any], ad: Dict[str, Any], output: Path, variant: int = 1) -> Dict[str, Any]:
    W, H = _canvas_size(str(campaign.get("platform") or ""))
    source = Image.open(product_image).convert("RGBA")
    base_color, accent, vibe = _category_style(campaign)
    sampled_base, sampled_accent = _palette(source)
    # Blend category style with the product photo so every product gets a distinct, coherent palette.
    bg1 = tuple(int(base_color[i] * 0.72 + sampled_base[i] * 0.28) for i in range(3))
    bg2 = tuple(int(accent[i] * 0.72 + sampled_accent[i] * 0.28) for i in range(3))

    # Photographic backdrop: the actual product photo is enlarged, blurred and darkened behind the clean hero.
    backdrop = ImageOps.fit(source.convert("RGB"), (W, H), method=Image.Resampling.LANCZOS)
    backdrop = backdrop.filter(ImageFilter.GaussianBlur(radius=26))
    overlay = Image.new("RGBA", (W, H), (*bg1, 210))
    backdrop_rgba = backdrop.convert("RGBA")
    backdrop_rgba = Image.blend(backdrop_rgba, overlay, 0.82)
    canvas = backdrop_rgba.convert("RGB")

    # Soft editorial gradient bands.
    draw = ImageDraw.Draw(canvas, "RGBA")
    for i in range(12):
        alpha = max(0, 42 - i * 3)
        draw.rounded_rectangle((40 + i * 5, 40 + i * 5, W - 40 - i * 5, H - 40 - i * 5), radius=70, outline=(*bg2, alpha), width=3)

    brand = str(campaign.get("brand") or "Brand")
    product = str(campaign.get("product") or "Product")
    headline = str(ad.get("headline") or product)
    copy = str(ad.get("primary_copy") or "")
    offer = str(campaign.get("offer") or "")
    cta = str(ad.get("cta") or "Learn more")

    # Different variants have distinct compositions, while preserving the exact product image.
    if variant == 1:
        product_box = (W // 2 - 330, 250, W // 2 + 330, 850 if H < 1600 else 1080)
        text_y = 900 if H < 1600 else 1160
    elif variant == 2:
        product_box = (W // 2 - 390, 420, W // 2 + 390, 940 if H < 1600 else 1120)
        text_y = 790 if H < 1600 else 1190
    else:
        product_box = (W // 2 - 340, 170, W // 2 + 340, 720 if H < 1600 else 920)
        text_y = 770 if H < 1600 else 1010

    product_layer = _fit_product(source, product_box[2] - product_box[0], product_box[3] - product_box[1])
    px = (W - product_layer.width) // 2
    py = product_box[1] + max(0, ((product_box[3] - product_box[1]) - product_layer.height) // 2)

    # Ground shadow gives the actual product a physical placement on the poster.
    shadow = Image.new("RGBA", (product_layer.width + 100, 120), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow, "RGBA")
    sd.ellipse((10, 20, shadow.width - 10, 90), fill=(0, 0, 0, 125))
    shadow = shadow.filter(ImageFilter.GaussianBlur(24))
    canvas.paste(shadow, (px - 50, py + product_layer.height - 15), shadow)
    canvas.paste(product_layer, (px, py), product_layer)

    # Exact typography is rendered locally so offers/CTAs are never hallucinated or distorted.
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rounded_rectangle((56, 52, min(W - 56, 56 + max(250, len(brand) * 24)), 116), radius=30, fill=(255, 255, 255, 220))
    draw.text((86, 69), brand[:28], font=_font(31, True), fill=(*bg1, 255))

    headline_font = _font(58 if W == 1080 and H < 1600 else 66, True)
    lines = _wrap(draw, headline, headline_font, W - 130)[:3]
    yy = text_y
    for line in lines:
        draw.text((65, yy), line, font=headline_font, fill=(255, 255, 255, 255))
        yy += headline_font.size + 8

    if copy:
        body_font = _font(27 if H < 1600 else 30)
        for line in _wrap(draw, copy, body_font, W - 150)[:3]:
            draw.text((68, yy + 12), line, font=body_font, fill=(239, 244, 250, 225))
            yy += body_font.size + 6

    if offer:
        offer_y = H - 190
        draw.rounded_rectangle((58, offer_y, W - 58, offer_y + 72), radius=24, fill=(*bg2, 238))
        draw.text((86, offer_y + 18), offer[:55], font=_font(27, True), fill=(255, 255, 255, 255))

    button_y = H - 98
    draw.rounded_rectangle((W - 360, button_y, W - 58, button_y + 58), radius=29, fill=(255, 255, 255, 238))
    draw.text((W - 209, button_y + 14), cta[:22], font=_font(24, True), fill=(*bg1, 255), anchor="ma")

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format="PNG", optimize=True)
    return {
        "status": "completed",
        "provider": "local-product-poster",
        "image_url": f"/media/creative/{output.name}",
        "file_path": str(output),
        "real_product_reference": True,
        "realistic_visuals": True,
        "human_generation": False,
        "zero_cost_api": True,
        "vibe": vibe,
        "variant": variant,
        "message": "Zero-cost poster uses the exact uploaded product photo, photographic backdrop treatment, realistic shadowing, and locally rendered exact text. No paid image/video API is required.",
    }


async def generate_static_or_carousel(campaign_id: int, campaign: Dict[str, Any], ad: Dict[str, Any], product_image: Path) -> List[Dict[str, Any]]:
    count = 3 if _is_carousel(campaign.get("creative_format", "")) else 1
    assets: List[Dict[str, Any]] = []
    for variant in range(1, count + 1):
        output = CREATIVE_ROOT / f"campaign_{campaign_id}_static_{variant}.png"
        result = await asyncio.to_thread(_render_local_static, product_image, campaign, ad, output, variant)
        result["variant"] = variant
        result["asset_type"] = "carousel_image" if count > 1 else "static_image"
        assets.append(result)
    return assets


async def generate_creative(campaign_id: int, storyboard: List[Dict[str, Any]], campaign: Dict[str, Any], ad: Dict[str, Any], product_image: Path | None) -> Dict[str, Any]:
    fmt = campaign.get("creative_format", "")
    if _is_video(fmt):
        raise RuntimeError("Video/Reel generation is intentionally disabled in the zero-cost final build. Choose Static image ad or Static carousel ad.")
    if not product_image:
        raise RuntimeError("A product image is required for static and carousel creatives.")
    assets = await generate_static_or_carousel(campaign_id, campaign, ad, product_image)
    return {
        "status": "completed",
        "provider": assets[0].get("provider"),
        "creative_format": fmt,
        "assets": assets,
        "asset_count": len(assets),
        "real_product_reference": True,
        "realistic_visuals": True,
        "human_generation": False,
        "zero_cost_api": True,
        "message": "Product-grounded static creative generated locally at zero additional API cost. The exact uploaded product photo is preserved and all marketing text is rendered deterministically.",
    }
