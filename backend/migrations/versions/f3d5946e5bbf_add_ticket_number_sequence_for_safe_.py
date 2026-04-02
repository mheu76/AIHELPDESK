"""Add ticket_number sequence for safe concurrent ticket creation

Revision ID: f3d5946e5bbf
Revises: 001
Create Date: 2026-04-02 09:01:04.871497

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3d5946e5bbf'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create sequence for ticket numbers (PostgreSQL only)
    # SQLite does not support sequences, so we skip this for SQLite
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        op.execute("""
            CREATE SEQUENCE IF NOT EXISTS ticket_number_seq
            START WITH 1
            INCREMENT BY 1
            NO MINVALUE
            NO MAXVALUE
            CACHE 1
        """)

        # Set sequence to current max ticket_number + 1 if tickets exist
        op.execute("""
            SELECT setval('ticket_number_seq',
                COALESCE((SELECT MAX(ticket_number) FROM tickets), 0) + 1,
                false)
        """)


def downgrade() -> None:
    # Drop the sequence (PostgreSQL only)
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        op.execute("DROP SEQUENCE IF EXISTS ticket_number_seq")
