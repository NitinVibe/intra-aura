"""remove legacy product category column

Revision ID: 9c7e7b4f1a2d
Revises: 4435e2596355
Create Date: 2026-09-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9c7e7b4f1a2d"
down_revision: Union[str, Sequence[str], None] = "4435e2596355"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Use product_categories as the sole product-category relationship."""
    op.drop_constraint(
        "products_category_id_fkey",
        "products",
        type_="foreignkey",
    )
    op.drop_index("ix_products_category_id", table_name="products")
    op.drop_column("products", "category_id")


def downgrade() -> None:
    """Restore the legacy column as nullable for a safe rollback."""
    op.add_column(
        "products",
        sa.Column("category_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "products_category_id_fkey",
        "products",
        "categories",
        ["category_id"],
        ["id"],
    )
    op.create_index(
        "ix_products_category_id",
        "products",
        ["category_id"],
        unique=False,
    )
