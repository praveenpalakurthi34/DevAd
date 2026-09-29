from fastapi import APIRouter
import shutil
from ..config import settings
from ..services.hindsight import health_check as hindsight_health

router = APIRouter()


def _configured(value: str) -> bool:
    return bool(value and not value.lower().startswith("your-") and "placeholder" not in value.lower())


@router.get("/system/status")
async def system_status():
    hindsight = await hindsight_health()
    return {
        "service": "DevAd",
        "llm": {
            "primary": "groq",
            "model": settings.GROQ_MODEL,
            "configured": _configured(settings.GROQ_API_KEY),
        },
        "hindsight": hindsight,
        "visual_generation": {
            "provider": "local-product-poster",
            "configured": True,
            "paid_api_required": False,
            "product_reference_required": True,
            "human_generation": False,
            "formats": ["static_image", "static_carousel"],
        },
        "reel_renderer": {
            "provider": "disabled-in-zero-cost-final-build",
            "ffmpeg_available": shutil.which("ffmpeg") is not None,
            "ffprobe_available": shutil.which("ffprobe") is not None,
            "note": "FFmpeg remains available for future video assembly but is not used to turn static ads into Reels.",
        },
    }
