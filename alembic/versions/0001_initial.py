"""initial empty baseline

Revision ID: 0001_initial
Revises: 
Create Date: 2025-08-27
"""
from alembic import op
import sqlalchemy as sa
import os

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Shop schema guard
    shop_schema = os.environ.get('POSTGRES_SCHEMA_SHOP')
    table_args = {'schema': shop_schema} if shop_schema else {}
    op.create_table(
        'coupons',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('code', sa.String(50), unique=True, nullable=False),
        sa.Column('description', sa.String(255)),
        sa.Column('discount_type', sa.String(20), nullable=False),
        sa.Column('discount_value', sa.Float, nullable=False),
        sa.Column('valid_from', sa.DateTime),
        sa.Column('valid_to', sa.DateTime),
        sa.Column('usage_limit', sa.Integer),
        sa.Column('times_used', sa.Integer, default=0),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        **table_args
    )

    # Orders table
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('order_number', sa.String(50), unique=True, nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(100), nullable=False),
        sa.Column('phone', sa.String(50)),
        sa.Column('address_line1', sa.String(255)),
        sa.Column('address_line2', sa.String(255)),
        sa.Column('city', sa.String(100)),
        sa.Column('postal_code', sa.String(20)),
        sa.Column('country', sa.String(2)),
        sa.Column('payment_method', sa.String(50), nullable=False),
        sa.Column('payment_status', sa.String(50), default='pending'),
        sa.Column('payment_reference', sa.String(255)),
        sa.Column('order_status', sa.String(50), default='pending'),
        sa.Column('subtotal', sa.Float, nullable=False),
        sa.Column('discount', sa.Float, default=0.0),
        sa.Column('tax', sa.Float, default=0.0),
        sa.Column('total', sa.Float, nullable=False),
        sa.Column('notes', sa.Text),
        sa.Column('coupon_id', sa.Integer, sa.ForeignKey(f'{shop_schema}.coupons.id' if shop_schema else 'coupons.id')),
        sa.Column('coupon_code', sa.String(50)),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('rozoom_schema.users.id')),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        **table_args
    )

    # OrderItems table
    op.create_table(
        'order_items',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('order_id', sa.Integer, sa.ForeignKey(f'{shop_schema}.orders.id' if shop_schema else 'orders.id'), nullable=False),
        sa.Column('product_id', sa.Integer, sa.ForeignKey(f'{shop_schema}.products.id' if shop_schema else 'products.id')),
        sa.Column('product_name', sa.String(255), nullable=False),
        sa.Column('product_slug', sa.String(255)),
        sa.Column('product_duration', sa.Integer),
        sa.Column('price_per_unit', sa.Float, nullable=False),
        sa.Column('quantity', sa.Integer, default=1),
        sa.Column('total_price', sa.Float, nullable=False),
        **table_args
    )

    # Payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('order_id', sa.Integer, sa.ForeignKey(f'{shop_schema}.orders.id' if shop_schema else 'orders.id'), nullable=False),
        sa.Column('amount', sa.Float, nullable=False),
        sa.Column('currency', sa.String(10), default='EUR'),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('provider', sa.String(50)),
        sa.Column('provider_payment_id', sa.String(255)),
        sa.Column('created_at', sa.DateTime),
        **table_args
    )
    import sqlalchemy as sa
    import os
    # Shop schema guard
    shop_schema = os.environ.get('POSTGRES_SCHEMA_SHOP')
    table_args = {'schema': shop_schema} if shop_schema else {}

    # Categories table
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(100), unique=True, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('image', sa.String(255)),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        **table_args
    )

    # Products table
    op.create_table(
        'products',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), unique=True, nullable=False),
        sa.Column('sku', sa.String(50), unique=True),
        sa.Column('short_description', sa.Text),
        sa.Column('description', sa.Text),
        sa.Column('price', sa.Float, nullable=False),
        sa.Column('sale_price', sa.Float),
        sa.Column('image', sa.String(255)),
        sa.Column('stock', sa.Integer, default=0),
        sa.Column('duration', sa.Integer),
        sa.Column('format', sa.String(100)),
        sa.Column('language', sa.String(50)),
        sa.Column('prerequisites', sa.Text),
        sa.Column('includes', sa.Text),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('stripe_url', sa.String(255)),
        sa.Column('is_featured', sa.Boolean, default=False),
        sa.Column('in_stock', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('category_id', sa.Integer, sa.ForeignKey(f'{shop_schema}.categories.id' if shop_schema else 'categories.id')),
        **table_args
    )

    # ProductImages table
    op.create_table(
        'product_images',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('product_id', sa.Integer, sa.ForeignKey(f'{shop_schema}.products.id' if shop_schema else 'products.id'), nullable=False),
        sa.Column('url', sa.String(255)),
        sa.Column('alt', sa.String(255)),
        sa.Column('data', sa.LargeBinary),
        sa.Column('filename', sa.String(255)),
        sa.Column('content_type', sa.String(100)),
        sa.Column('sort_order', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime),
        **table_args
    )

    # ProductReviews table
    op.create_table(
        'product_reviews',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('product_id', sa.Integer, sa.ForeignKey(f'{shop_schema}.products.id' if shop_schema else 'products.id'), nullable=False),
        sa.Column('rating', sa.Integer, nullable=False),
        sa.Column('author_name', sa.String(100)),
        sa.Column('author_email', sa.String(100)),
        sa.Column('content', sa.Text),
        sa.Column('is_approved', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime),
        **table_args
    )

    # Carts table
    op.create_table(
        'carts',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('session_id', sa.String(128), unique=True, nullable=True),
        sa.Column('user_id', sa.Integer, nullable=True),
        sa.Column('status', sa.String(20), default='open'),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        **table_args
    )

    # CartItems table
    op.create_table(
        'cart_items',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('cart_id', sa.Integer, sa.ForeignKey(f'{shop_schema}.carts.id' if shop_schema else 'carts.id'), nullable=False),
        sa.Column('product_id', sa.Integer, sa.ForeignKey(f'{shop_schema}.products.id' if shop_schema else 'products.id'), nullable=False),
        sa.Column('quantity', sa.Integer, default=1),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        **table_args
    )


def downgrade():
    # No downgrade for baseline
    pass
