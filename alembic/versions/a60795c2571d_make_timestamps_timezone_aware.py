"""Make timestamps timezone aware

Revision ID: a60795c2571d
Revises: f33c4b7feb88
Create Date: 2025-12-24 13:50:48.674817

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a60795c2571d'
down_revision: Union[str, Sequence[str], None] = 'f33c4b7feb88'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
