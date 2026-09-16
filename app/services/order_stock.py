from app.models.order import Order
from app.models.product import Product


def release_order_stock(db, order: Order) -> bool:
    """
    Release reserved stock exactly once for an unpaid order.
    Returns True when stock was released by this call.
    """
    if order.stock_released:
        return False

    for item in order.items:
        if not item.product_id:
            continue

        product = (
            db.query(Product)
            .filter(Product.id == item.product_id)
            .with_for_update()
            .first()
        )

        if product:
            product.stock += item.quantity

    order.stock_released = True
    return True
