from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PRODUCT_ROOT = ROOT / "generated" / "products"
PRODUCT_ROOT.mkdir(parents=True, exist_ok=True)

router = APIRouter()
ALLOWED = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = 10 * 1024 * 1024


@router.post("/assets/product-image")
async def upload_product_image(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED:
        raise HTTPException(status_code=400, detail="Upload a JPG, PNG, or WebP product image.")
    data = await file.read()
    if not data or len(data) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="Product image must be between 1 byte and 10 MB.")
    suffix = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[file.content_type]
    path = PRODUCT_ROOT / f"product_{uuid4().hex}{suffix}"
    try:
        from io import BytesIO
        image = Image.open(BytesIO(data))
        image.verify()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid image.") from exc
    path.write_bytes(data)
    return {
        "path": str(path),
        "url": f"/media/products/{path.name}",
        "filename": path.name,
        "content_type": file.content_type,
        "size_bytes": len(data),
    }
