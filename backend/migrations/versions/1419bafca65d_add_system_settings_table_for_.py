"""Add system_settings table for persistent configuration

Revision ID: 1419bafca65d
Revises: 90697f8177cc
Create Date: 2026-04-02 09:12:03.835458

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1419bafca65d'
down_revision: Union[str, None] = '90697f8177cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create system_settings table
    op.create_table(
        'system_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('llm_provider', sa.String(length=50), nullable=False),
        sa.Column('llm_model', sa.String(length=100), nullable=False),
        sa.Column('llm_temperature', sa.Float(), nullable=False),
        sa.Column('max_tokens', sa.Integer(), nullable=False),
        sa.Column('rag_enabled', sa.Boolean(), nullable=False),
        sa.Column('rag_top_k', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_system_settings'))
    )

    op.execute(
        """
        INSERT INTO system_settings (
            id, llm_provider, llm_model, llm_temperature, max_tokens,
            rag_enabled, rag_top_k, updated_at
        ) VALUES (
            1,
            'claude',
            'claude-sonnet-4-20250514',
            0.7,
            1024,
            true,
            3,
            CURRENT_TIMESTAMP
        )
        """
    )


def downgrade() -> None:
    # Drop the system_settings table
    op.drop_table('system_settings')
