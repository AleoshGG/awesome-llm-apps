"""add sales and cart

Revision ID: b2717db98d45
Revises: 85be4b0934aa
Create Date: 2026-10-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2717db98d45"
down_revision: Union[str, None] = "85be4b0934aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cart_items",
        sa.Column("product_id", sa.String(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "quantity > 0",
            name="ck_cart_items_quantity_positive",
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("product_id"),
    )
    op.create_table(
        "sales",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sales_created_at", "sales", ["created_at"])
    op.create_table(
        "sale_items",
        sa.Column("sale_id", sa.String(), nullable=False),
        sa.Column("product_id", sa.String(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "quantity > 0",
            name="ck_sale_items_quantity_positive",
        ),
        sa.ForeignKeyConstraint(
            ["sale_id"],
            ["sales.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("sale_id", "product_id"),
    )


def downgrade() -> None:
    op.drop_table("sale_items")
    op.drop_index("ix_sales_created_at", table_name="sales")
    op.drop_table("sales")
    op.drop_table("cart_items")
