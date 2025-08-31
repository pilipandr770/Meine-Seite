"""add product_images blob columns

Revision ID: 0002_add_productimage_blob
Revises: 0001_initial
Create Date: 2025-08-30
"""
from alembic import op
import sqlalchemy as sa
import os

revision = '0002_add_productimage_blob'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade():
    schema = os.environ.get('POSTGRES_SCHEMA_SHOP')
    table_args = {'schema': schema} if schema else {}
    # Add columns to product_images
    op.add_column('product_images', sa.Column('data', sa.LargeBinary()), **table_args)
    op.add_column('product_images', sa.Column('filename', sa.String(length=255)), **table_args)
    op.add_column('product_images', sa.Column('content_type', sa.String(length=100)), **table_args)


def downgrade():
    schema = os.environ.get('POSTGRES_SCHEMA_SHOP')
    table_args = {'schema': schema} if schema else {}
    op.drop_column('product_images', 'content_type', **table_args)
    op.drop_column('product_images', 'filename', **table_args)
    op.drop_column('product_images', 'data', **table_args)
