"""add_gender_message_date_creator_profile

Revision ID: edc403fe1e87
Revises: ccf1187cd090
Create Date: 2026-03-08 00:31:56.492965

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'edc403fe1e87'
down_revision: Union[str, None] = 'ccf1187cd090'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Criar o tipo ENUM no PostgreSQL antes de adicionar a coluna
    leadgender_enum = sa.Enum('F', 'M', 'ND', name='leadgender')
    leadgender_enum.create(op.get_bind(), checkfirst=True)

    op.add_column('leads', sa.Column('gender', sa.Enum('F', 'M', 'ND', name='leadgender'), nullable=True))
    op.add_column('leads', sa.Column('gender_confidence', sa.Integer(), nullable=True))
    op.add_column('leads', sa.Column('message_date', sa.DateTime(), nullable=True))
    op.add_column('leads', sa.Column('creator_profile', sa.String(length=200), nullable=True))


def downgrade() -> None:
    op.drop_column('leads', 'creator_profile')
    op.drop_column('leads', 'message_date')
    op.drop_column('leads', 'gender_confidence')
    op.drop_column('leads', 'gender')
    # Remover o tipo ENUM do PostgreSQL
    sa.Enum(name='leadgender').drop(op.get_bind(), checkfirst=True)
