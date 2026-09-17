from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from app.config.settings import settings
from app.utils.image_optimizer import optimize_image_upload, save_optimized_webp


def cloudinary_configured() -> bool:
    return bool(
        settings.CLOUDINARY_CLOUD_NAME
        and settings.CLOUDINARY_API_KEY
        and settings.CLOUDINARY_API_SECRET
    )


def _cloudinary_base() -> str:
    if not cloudinary_configured():
        raise HTTPException(
            status_code=503,
            detail="Cloudinary image storage is not configured. Add CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET.",
        )
    return f"https://api.cloudinary.com/v1_1/{settings.CLOUDINARY_CLOUD_NAME}"


def _basic_auth_header() -> str:
    raw = f"{settings.CLOUDINARY_API_KEY}:{settings.CLOUDINARY_API_SECRET}".encode()
    return "Basic " + base64.b64encode(raw).decode()


def _multipart(fields: dict[str, str], file_field: str, filename: str, data: bytes, content_type: str = "image/webp") -> tuple[bytes, str]:
    boundary = f"----IntraAuraBoundary{uuid4().hex}"
    chunks: list[bytes] = []

    for name, value in fields.items():
        chunks.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                f"{value}\r\n"
            ).encode()
        )

    chunks.append(
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode()
    )
    chunks.append(data)
    chunks.append(f"\r\n--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def _request_json(request: urllib.request.Request, timeout: int = 30) -> dict:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
        return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Cloudinary HTTP {exc.code}: {detail}") from exc
    except Exception as exc:
        raise RuntimeError(f"Cloudinary request failed: {exc}") from exc


def cloudinary_upload_bytes(data: bytes, *, public_id: str) -> dict:
    url = f"{_cloudinary_base()}/image/upload"
    fields = {
        "public_id": public_id,
        "format": "webp",
        "timestamp": str(int(time.time())),
    }

    # Signed upload: the signature covers the signed parameters only.
    to_sign = "&".join(
        f"{k}={fields[k]}"
        for k in sorted(fields)
    )
    signature = hashlib.sha1(
        (to_sign + settings.CLOUDINARY_API_SECRET).encode("utf-8")
    ).hexdigest()

    fields["api_key"] = settings.CLOUDINARY_API_KEY
    fields["signature"] = signature

    body, content_type = _multipart(fields, "file", f"{Path(public_id).name}.webp", data)
    request = urllib.request.Request(url, data=body, method="POST")
    request.add_header("Authorization", _basic_auth_header())
    request.add_header("Content-Type", content_type)

    return _request_json(request)


def upload_optimized_image(
    upload: UploadFile,
    *,
    folder: str,
    max_dimension: int,
    quality: int = 82,
) -> dict:
    data = optimize_image_upload(
        upload,
        max_dimension=max_dimension,
        quality=quality,
    )

    if cloudinary_configured():
        public_id = f"{folder.strip('/')}/{uuid4().hex}"
        try:
            result = cloudinary_upload_bytes(data, public_id=public_id)
            return {
                "url": result["secure_url"],
                "public_id": result.get("public_id", public_id),
                "cloudinary": True,
            }
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail="Image upload to cloud storage failed. Check Cloudinary settings.",
            ) from exc

    # Local development fallback. Vercel must use persistent cloud storage.
    if os.getenv("VERCEL") and not cloudinary_configured():
        raise HTTPException(
            status_code=503,
            detail="Cloudinary image storage is not configured for Vercel.",
        )

    if folder == "site":
        local_dir = Path("app/static/uploads/site")
        local_url = "/static/uploads/site"
    elif folder == "products":
        local_dir = Path("app/static/images/products")
        local_url = "/static/images/products"
    elif folder == "categories":
        local_dir = Path("app/static/uploads/categories")
        local_url = "/static/uploads/categories"
    else:
        local_dir = Path("app/static/uploads") / folder
        local_url = f"/static/uploads/{folder}"

    filename = f"{uuid4().hex}.webp"
    destination = local_dir / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        destination.write_bytes(data)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to save image. Configure Cloudinary for persistent production storage.",
        ) from exc

    return {
        "url": f"{local_url}/{filename}",
        "public_id": None,
        "cloudinary": False,
        "filename": filename,
        "path": destination,
    }


def _cloudinary_public_id_from_url(url: str) -> str | None:
    if not url or "res.cloudinary.com/" not in url or "/image/upload/" not in url:
        return None

    try:
        after = url.split("/image/upload/", 1)[1]
        parts = after.split("/")
        # Remove transformation segments and version segment.
        while parts and (
            re.match(r"^(?:c_|w_|h_|ar_|q_|f_|g_|dpr_|e_|fl_|bo_|bg_|r_|x_|y_|z_|t_)", parts[0])
            or parts[0].startswith("v") and parts[0][1:].isdigit()
        ):
            parts.pop(0)
        if not parts:
            return None
        public_id = "/".join(parts)
        if "." in public_id:
            public_id = public_id.rsplit(".", 1)[0]
        return public_id
    except Exception:
        return None


def delete_stored_image(url: str, local_path: Path | None = None) -> None:
    public_id = _cloudinary_public_id_from_url(url or "")
    if public_id and cloudinary_configured():
        timestamp = str(int(time.time()))
        params = f"invalidate=true&public_id={urllib.parse.quote_plus(public_id)}&timestamp={timestamp}"
        signature = hashlib.sha1(
            (
                f"invalidate=true&public_id={public_id}&timestamp={timestamp}"
                + settings.CLOUDINARY_API_SECRET
            ).encode("utf-8")
        ).hexdigest()

        data = urllib.parse.urlencode(
            {
                "public_id": public_id,
                "timestamp": timestamp,
                "invalidate": "true",
                "api_key": settings.CLOUDINARY_API_KEY,
                "signature": signature,
            }
        ).encode()
        request = urllib.request.Request(
            f"{_cloudinary_base()}/image/destroy",
            data=data,
            method="POST",
        )
        request.add_header("Authorization", _basic_auth_header())
        request.add_header("Content-Type", "application/x-www-form-urlencoded")
        try:
            _request_json(request)
        except Exception:
            # Deleting the DB reference should not fail just because CDN deletion
            # is temporarily unavailable.
            pass
        return

    if local_path:
        try:
            if local_path.exists() and local_path.is_file():
                local_path.unlink()
        except OSError:
            pass


def list_cloudinary_media(prefix: str = "site", max_results: int = 500) -> list[dict]:
    url = (
        f"{_cloudinary_base()}/resources/image/upload?"
        + urllib.parse.urlencode({"prefix": prefix, "max_results": max_results})
    )
    request = urllib.request.Request(url, method="GET")
    request.add_header("Authorization", _basic_auth_header())
    result = _request_json(request)
    files = []
    for item in result.get("resources", []):
        public_id = item.get("public_id", "")
        files.append(
            {
                "name": public_id.split("/")[-1] or public_id,
                "file": public_id,
                "url": item.get("secure_url") or item.get("url"),
            }
        )
    return files
