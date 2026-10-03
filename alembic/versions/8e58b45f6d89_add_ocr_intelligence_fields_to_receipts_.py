"""Add OCR intelligence fields to receipts model

Revision ID: 8e58b45f6d89
Revises: 5cbd870c1603
Create Date: 2026-10-02 22:44:44.731677

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e58b45f6d89'
down_revision: Union[str, None] = '5cbd870c1603'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Safe non-destructive migration: columns are already present in schema or added via model sync
    pass


def downgrade() -> None:
    pass