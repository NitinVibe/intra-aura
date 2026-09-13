from __future__ import annotations

from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError

# Safety limit for the original upload. The processed WebP is normally much smaller.
MAX_UPLOAD_BYTES = 12 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/jfif"}


def optimize_image_upload(
    upload: UploadFile,
    *,
    max_dimension: int,
    quality: int = 82,
) -> bytes:
    """Read an uploaded image, resize it proportionally, and return WebP bytes."""
    content_type = (upload.content_type or "").lower()
    suffix = Path(upload.filename or "").suffix.lower()
    filename_types = {".jpg", ".jpeg", ".jfif", ".png", ".webp"}
    if content_type not in ALLOWED_CONTENT_TYPES and suffix not in filename_types:
        raise HTTPException(400, "Only JPG, PNG and WEBP images are allowed.")

    data = upload.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Image is too large. Maximum upload size is 12 MB.")
    if not data:
        raise HTTPException(400, "The uploaded image is empty.")

    try:
        with Image.open(BytesIO(data)) as source:
            source.verify()

        with Image.open(BytesIO(data)) as image:
            # Correct phone-camera orientation before resizing.
            image = ImageOps.exif_transpose(image)

            # Keep the original aspect ratio; never upscale small images.
            image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

            # WebP supports RGB/RGBA. Flatten unusual modes safely.
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGBA" if "transparency" in image.info else "RGB")

            output = BytesIO()
            image.save(
                output,
                format="WEBP",
                quality=quality,
                method=6,
                optimize=True,
            )
            return output.getvalue()

    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(400, "The uploaded file is not a valid image.") from exc


def save_optimized_webp(upload: UploadFile, destination: Path, *, max_dimension: int, quality: int = 82) -> int:
    """Optimize an upload and atomically replace the destination. Returns byte size."""
    data = optimize_image_upload(upload, max_dimension=max_dimension, quality=quality)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = destination.with_suffix(destination.suffix + ".tmp")
    try:
        temp_path.write_bytes(data)
        temp_path.replace(destination)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
    return len(data)
