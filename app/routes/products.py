from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from fastapi import UploadFile, File

from app.config.database import get_db
from app.utils.cloudinary_storage import upload_optimized_image, delete_stored_image
from app.models.category import Category
from app.models.product import Product, ProductImage
from app.schemas.product import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)
from fastapi.responses import JSONResponse


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


# ============================================================
# CREATE PRODUCT
# ============================================================

@router.post(
    "/",
    response_model=ProductResponse,
    status_code=201
)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    # Create product (original flow without additional diagnostic logging)
        # --------------------------------------------------------
        # CHECK CATEGORIES
        # --------------------------------------------------------

        categories = (
            db.query(Category)
            .filter(
                Category.id.in_(product.category_ids)
            )
            .all()
        )

        if len(categories) != len(set(product.category_ids)):
            raise HTTPException(
                status_code=404,
                detail="One or more categories not found"
            )

        # --------------------------------------------------------
        # CHECK DUPLICATE SLUG
        # --------------------------------------------------------

        existing = (
            db.query(Product)
            .filter(
                Product.slug == product.slug
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Product with this slug already exists"
            )

        # --------------------------------------------------------
        # VALIDATE DISCOUNT PRICE
        # --------------------------------------------------------

        if (
            product.discount_price is not None
            and product.discount_price >= product.price
        ):
            raise HTTPException(
                status_code=400,
                detail="Discount price must be lower than regular price"
            )

        # --------------------------------------------------------
        # CREATE PRODUCT
        # --------------------------------------------------------

        new_product = Product(
            name=product.name,
            slug=product.slug,
            description=product.description,
            price=product.price,
            discount_price=product.discount_price,
            stock=product.stock,
            material=product.material,
            color=product.color,

            # MULTIPLE CATEGORIES
            categories=categories
        )

        db.add(new_product)

        db.commit()

        db.refresh(new_product)

        # Return the ORM object and let Pydantic/FastAPI serialize it
        return new_product


# ============================================================
# GET PRODUCTS
# ============================================================

@router.get(
    "/",
    response_model=list[ProductResponse]
)
def get_products(
    search: str | None = Query(default=None),
    category_id: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):

    query = db.query(Product)

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if search:

        query = query.filter(
            Product.name.ilike(
                f"%{search}%"
            )
        )

    # --------------------------------------------------------
    # CATEGORY FILTER
    # --------------------------------------------------------

    if category_id and category_id != "all":

        try:
            category_id_int = int(category_id)

        except ValueError:

            raise HTTPException(
                status_code=400,
                detail="Invalid category"
            )

        query = (
            query
            .join(Product.categories)
            .filter(
                Category.id == category_id_int
            )
        )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return (
        query
        .order_by(Product.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ============================================================
# GET SINGLE PRODUCT
# ============================================================

@router.get(
    "/{product_id}",
    response_model=ProductResponse
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):

    product = (
        db.query(Product)
        .filter(
            Product.id == product_id
        )
        .first()
    )

    if not product:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product


# ============================================================
# UPDATE PRODUCT
# ============================================================

@router.put(
    "/{product_id}",
    response_model=ProductResponse
)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db)
):

    product = (
        db.query(Product)
        .filter(
            Product.id == product_id
        )
        .first()
    )

    if not product:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # --------------------------------------------------------
    # UPDATE CATEGORIES
    # --------------------------------------------------------

    if data.category_ids is not None:

        categories = (
            db.query(Category)
            .filter(
                Category.id.in_(data.category_ids)
            )
            .all()
        )

        if len(categories) != len(set(data.category_ids)):

            raise HTTPException(
                status_code=404,
                detail="One or more categories not found"
            )

        # Replace old categories
        product.categories = categories

    # --------------------------------------------------------
    # UPDATE BASIC FIELDS
    # --------------------------------------------------------

    if data.name is not None:
        product.name = data.name

    if data.slug is not None:

        existing = (
            db.query(Product)
            .filter(
                Product.slug == data.slug,
                Product.id != product_id
            )
            .first()
        )

        if existing:

            raise HTTPException(
                status_code=400,
                detail="Product with this slug already exists"
            )

        product.slug = data.slug

    if data.description is not None:
        product.description = data.description

    if data.price is not None:
        product.price = data.price

    if data.discount_price is not None:
        product.discount_price = data.discount_price

    if data.stock is not None:
        product.stock = data.stock

    if data.material is not None:
        product.material = data.material

    if data.color is not None:
        product.color = data.color

    if data.is_active is not None:
        product.is_active = data.is_active

    # --------------------------------------------------------
    # VALIDATE DISCOUNT
    # --------------------------------------------------------

    if (
        product.discount_price is not None
        and product.discount_price >= product.price
    ):

        raise HTTPException(
            status_code=400,
            detail="Discount price must be lower than regular price"
        )

    db.commit()

    db.refresh(product)

    return product


# ============================================================
# DELETE PRODUCT
# ============================================================

@router.delete(
    "/{product_id}"
)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):

    product = (
        db.query(Product)
        .filter(
            Product.id == product_id
        )
        .first()
    )

    if not product:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    db.delete(product)

    db.commit()

    return {
        "message": "Product deleted successfully"
    }


# ============================================================
# UPLOAD PRODUCT IMAGE
# ============================================================

@router.post("/{product_id}/images")
def upload_product_image(
    product_id: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    stored = None
    try:
        stored = upload_optimized_image(
            image,
            folder="products",
            max_dimension=1600,
            quality=82,
        )

        existing_images = (
            db.query(ProductImage)
            .filter(ProductImage.product_id == product_id)
            .count()
        )

        new_image = ProductImage(
            product_id=product_id,
            image_url=stored["url"],
            is_primary=(existing_images == 0),
            sort_order=existing_images,
        )

        db.add(new_image)
        db.commit()
        db.refresh(new_image)

        return {
            "message": "Image uploaded and optimized to WebP successfully",
            "image": {
                "id": new_image.id,
                "image_url": new_image.image_url,
                "is_primary": new_image.is_primary,
                "sort_order": new_image.sort_order,
            },
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        if stored and stored.get("path"):
            try:
                stored["path"].unlink(missing_ok=True)
            except OSError:
                pass
        raise HTTPException(status_code=500, detail="Failed to process image") from exc


# ============================================================
# DELETE PRODUCT IMAGE
# ============================================================

@router.delete("/{product_id}/images/{image_id}")
def delete_product_image(
    product_id: int,
    image_id: int,
    db: Session = Depends(get_db)
):

    image = (
        db.query(ProductImage)
        .filter(
            ProductImage.id == image_id,
            ProductImage.product_id == product_id
        )
        .first()
    )

    if not image:

        raise HTTPException(
            status_code=404,
            detail="Image not found"
        )

    was_primary = image.is_primary

    image_url = image.image_url

    db.delete(image)

    db.commit()

    # Remove the corresponding cloud asset when this image is stored remotely.
    delete_stored_image(image_url)

    if was_primary:

        next_image = (
            db.query(ProductImage)
            .filter(
                ProductImage.product_id == product_id
            )
            .order_by(
                ProductImage.sort_order.asc()
            )
            .first()
        )

        if next_image:

            next_image.is_primary = True

            db.commit()

    return {
        "message": "Image deleted successfully"
    }


# ============================================================
# SET PRIMARY IMAGE
# ============================================================

@router.put("/{product_id}/images/{image_id}/primary")
def set_primary_product_image(
    product_id: int,
    image_id: int,
    db: Session = Depends(get_db)
):

    image = (
        db.query(ProductImage)
        .filter(
            ProductImage.id == image_id,
            ProductImage.product_id == product_id
        )
        .first()
    )

    if not image:

        raise HTTPException(
            status_code=404,
            detail="Image not found"
        )

    db.query(ProductImage).filter(
        ProductImage.product_id == product_id
    ).update({
        ProductImage.is_primary: False
    })

    image.is_primary = True

    db.commit()

    return {
        "message": "Primary image updated successfully"
    }
