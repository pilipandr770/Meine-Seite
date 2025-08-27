"""initial empty baseline

Revision ID: 0001_initial
Revises: 
Create Date: 2025-08-27
"""
from alembic import op

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Baseline (assumes tables already created externally)
    pass


def downgrade():
    # No downgrade for baseline
    pass
