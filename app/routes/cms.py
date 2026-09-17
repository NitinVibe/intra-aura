import os, uuid, json
from pathlib import Path
from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException
from app.template_config import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
from app.routes.auth import require_admin
from app.content.store import load_content, save_content
from app.utils.image_optimizer import save_optimized_webp
from app.utils.cloudinary_storage import (
    cloudinary_configured,
    upload_optimized_image,
    list_cloudinary_media,
    delete_stored_image,
)

router = APIRouter(prefix="/admin", tags=["Admin Website"], dependencies=[Depends(require_admin)])
templates = Jinja2Templates(directory="app/templates")
UPLOAD_DIR = Path("app/static/uploads/site")

@router.get("/website")
def website_editor(request: Request):
    return templates.TemplateResponse(request=request, name="admin/website.html", context={"content": load_content()})

@router.post("/website/terms")
async def website_terms_save(request: Request):
    """Save only Terms & Conditions fields without touching the rest of the website content."""
    form = await request.form()
    data = load_content()
    terms = data.setdefault("terms", {})

    def val(name, default=""):
        value = form.get(name, default)
        return str(value).strip()

    # Preserve every existing term unless the corresponding field was actually submitted.
    for field in ("eyebrow", "title", "intro", "last_updated", "note"):
        key = f"terms_{field}"
        if key in form:
            terms[field] = val(key, terms.get(field, ""))

    existing = terms.get("sections", [])
    sections = []
    for i in range(1, 8):
        old = existing[i - 1] if isinstance(existing, list) and len(existing) >= i else ["", ""]
        old_title = old[0] if isinstance(old, (list, tuple)) and len(old) > 0 else ""
        old_text = old[1] if isinstance(old, (list, tuple)) and len(old) > 1 else ""
        title_key = f"terms_section_{i}_title"
        text_key = f"terms_section_{i}_text"
        title = val(title_key, old_title) if title_key in form else old_title
        text = val(text_key, old_text) if text_key in form else old_text
        sections.append([title, text])
    terms["sections"] = sections

    save_content(data)
    return RedirectResponse("/admin/website?saved=1#terms", status_code=303)

@router.post("/website")
async def website_save(request: Request):
    form = await request.form()
    data = load_content()
    def val(name, default=""):
        return str(form.get(name, default)).strip()

    # Header + navigation
    h=data.setdefault("header",{})
    for key in ("announcement_1","announcement_2","announcement_3","logo","cta"):
        h[key]=val(key,h.get(key,""))
    nav=[]
    for i in range(1,8):
        label=val(f"nav_{i}_label","")
        url=val(f"nav_{i}_url","")
        if label or url: nav.append({"label":label,"url":url})
    if nav: h["nav_links"]=nav

    # Home
    home=data.setdefault("home",{})
    for i in range(1,4):
        s=home.setdefault(f"hero_{i}",{})
        for key in ("eyebrow","title_html","description","image","primary","secondary"):
            s[key]=val(f"home_hero_{i}_{key}",s.get(key,""))
    for key in ("featured","categories","services"):
        s=home.setdefault(key,{})
        for field in ("eyebrow","title","description"):
            s[field]=val(f"home_{key}_{field}",s.get(field,""))
    a=home.setdefault("about",{})
    for field in ("eyebrow","title","image","paragraph_1","paragraph_2","highlight_1","highlight_2","highlight_3","button"):
        a[field]=val(f"home_about_{field}",a.get(field,""))
    c=home.setdefault("cta",{})
    for field in ("eyebrow","title_html","description","button"):
        c[field]=val(f"home_cta_{field}",c.get(field,""))

    # About
    about=data.setdefault("about",{})
    for group in ("hero","story","values","closing"):
        s=about.setdefault(group,{})
        for field in ("eyebrow","title_html","title","description","image","paragraph_1","paragraph_2","paragraph_3","button"):
            if f"about_{group}_{field}" in form or field in s:
                s[field]=val(f"about_{group}_{field}",s.get(field,""))
    about["values"]["items"]=[[val(f"about_value_{i}_title"),val(f"about_value_{i}_description")] for i in range(1,5)]

    # Services
    services=data.setdefault("services",{})
    for group in ("hero","intro","cta"):
        s=services.setdefault(group,{})
        for field in ("eyebrow","title_html","title","description","image","button"):
            if f"services_{group}_{field}" in form or field in s:
                s[field]=val(f"services_{group}_{field}",s.get(field,""))
    services["items"]=[[val(f"service_{i}_title"),val(f"service_{i}_description"),val(f"service_{i}_image")] for i in range(1,7)]

    # Portfolio
    portfolio=data.setdefault("portfolio",{})
    for group in ("hero","intro","cta"):
        s=portfolio.setdefault(group,{})
        for field in ("eyebrow","title_html","title","description","image","button"):
            if f"portfolio_{group}_{field}" in form or field in s:
                s[field]=val(f"portfolio_{group}_{field}",s.get(field,""))
    portfolio["projects"]=[[val(f"project_{i}_category"),val(f"project_{i}_title"),val(f"project_{i}_meta"),val(f"project_{i}_image")] for i in range(1,5)]

    contact=data.setdefault("contact",{})
    for field in ("eyebrow","title_html","description"):
        contact[field]=val(f"contact_{field}",contact.get(field,""))

    # Footer + links
    footer=data.setdefault("footer",{})
    for field in ("brand_description","explore_title","company_title","social_title","copyright","bottom_text"):
        footer[field]=val(f"footer_{field}",footer.get(field,""))
    footer["explore_links"]=[{"label":val(f"footer_explore_{i}_label"),"url":val(f"footer_explore_{i}_url")} for i in range(1,8) if val(f"footer_explore_{i}_label") or val(f"footer_explore_{i}_url")]
    footer["company_links"]=[{"label":val(f"footer_company_{i}_label"),"url":val(f"footer_company_{i}_url")} for i in range(1,6) if val(f"footer_company_{i}_label") or val(f"footer_company_{i}_url")]
    footer["social_links"]=[{"label":val(f"footer_social_{i}_label"),"url":val(f"footer_social_{i}_url")} for i in range(1,7) if val(f"footer_social_{i}_label") or val(f"footer_social_{i}_url")]

    # Terms & Conditions
    terms=data.setdefault("terms",{})
    for field in ("eyebrow","title","intro","last_updated","note"):
        terms[field]=val(f"terms_{field}",terms.get(field,""))
    sections=[]
    for i in range(1,8):
        sections.append([val(f"terms_section_{i}_title", ""), val(f"terms_section_{i}_text", "")])
    terms["sections"]=sections

    # Advanced JSON allows adding new content without waiting for a code change.
    raw=val("advanced_json","")
    if raw:
        try:
            extra=json.loads(raw)
            if isinstance(extra,dict):
                def deep_merge(dst,src):
                    for k,v in src.items():
                        if isinstance(v,dict) and isinstance(dst.get(k),dict): deep_merge(dst[k],v)
                        else: dst[k]=v
                deep_merge(data,extra)
        except json.JSONDecodeError as exc:
            raise HTTPException(400,f"Advanced JSON is invalid: {exc}")

    save_content(data)
    return RedirectResponse("/admin/website?saved=1", status_code=303)

@router.get("/media")
def media_library(request: Request):
    if not cloudinary_configured() and os.getenv("VERCEL"):
        raise HTTPException(
            status_code=503,
            detail="Cloudinary image storage is not configured for Vercel.",
        )
    if cloudinary_configured():
        try:
            files = list_cloudinary_media(prefix="site")
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail="Could not load Cloudinary media. Check Cloudinary settings.",
            ) from exc
    else:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        files = []
        for p in sorted(UPLOAD_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if p.is_file():
                files.append({
                    "name": p.name,
                    "file": p.name,
                    "url": f"/static/uploads/site/{p.name}",
                })

    return templates.TemplateResponse(
        request=request,
        name="admin/media.html",
        context={"files": files},
    )


@router.get("/media/json")
def media_json():
    if not cloudinary_configured() and os.getenv("VERCEL"):
        raise HTTPException(
            status_code=503,
            detail="Cloudinary image storage is not configured for Vercel.",
        )
    if cloudinary_configured():
        try:
            return JSONResponse(list_cloudinary_media(prefix="site"))
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail="Could not load Cloudinary media.",
            ) from exc

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    files = [
        {
            "name": p.name,
            "file": p.name,
            "url": f"/static/uploads/site/{p.name}",
        }
        for p in sorted(UPLOAD_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)
        if p.is_file()
    ]
    return JSONResponse(files)


@router.post("/media/upload")
async def media_upload(image: UploadFile = File(...)):
    try:
        upload_optimized_image(
            image,
            folder="site",
            max_dimension=1920,
            quality=82,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, "Failed to process image") from exc

    return RedirectResponse("/admin/media?uploaded=1", status_code=303)


@router.delete("/media/{filename:path}")
def media_delete(filename: str):
    if cloudinary_configured():
        # In Cloudinary mode the picker sends the public_id as `file`.
        delete_stored_image(f"https://res.cloudinary.com/x/image/upload/{filename}")
        return {"message": "Media deleted"}

    safe = Path(filename).name
    path = UPLOAD_DIR / safe
    if path.exists() and path.is_file():
        path.unlink()
    return {"message": "Media deleted"}

