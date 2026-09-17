from fastapi import UploadFile, File
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.utils.cloudinary_storage import upload_optimized_image
from app.models.category import Category
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
)


router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)


@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=201
)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db)
):
    existing = (
        db.query(Category)
        .filter(Category.slug == category.slug)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Category with this slug already exists"
        )

    new_category = Category(
    name=category.name,
    slug=category.slug,
    description=category.description,
)

    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    return new_category


@router.get(
    "/",
    response_model=list[CategoryResponse]
)
def get_categories(
    db: Session = Depends(get_db)
):
    return db.query(Category).order_by(Category.id.desc()).all()


@router.get(
    "/{category_id}",
    response_model=CategoryResponse
)
def get_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    category = (
        db.query(Category)
        .filter(Category.id == category_id)
        .first()
    )

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    return category


@router.put(
    "/{category_id}",
    response_model=CategoryResponse
)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db)
):
    category = (
        db.query(Category)
        .filter(Category.id == category_id)
        .first()
    )

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    if data.name is not None:
        category.name = data.name

    if data.slug is not None:
        category.slug = data.slug

    if data.description is not None:
        category.description = data.description

    if data.image_url is not None:
        category.image_url = data.image_url

    db.commit()
    db.refresh(category)

    return category


@router.delete(
    "/{category_id}"
)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    category = (
        db.query(Category)
        .filter(Category.id == category_id)
        .first()
    )

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    db.delete(category)
    db.commit()

    return {
        "message": "Category deleted successfully"
    }

@router.post("/{category_id}/image")
def upload_category_image(
    category_id: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    category = (
        db.query(Category)
        .filter(Category.id == category_id)
        .first()
    )

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    try:
        stored = upload_optimized_image(
            image,
            folder="categories",
            max_dimension=1200,
            quality=82,
        )

        category.image_url = stored["url"]
        db.commit()
        db.refresh(category)

        return {
            "message": "Category image uploaded and optimized to WebP successfully",
            "image_url": category.image_url,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to process category image") from exc

