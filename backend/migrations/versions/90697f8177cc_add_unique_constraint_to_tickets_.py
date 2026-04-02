"""Add unique constraint to tickets.session_id

Revision ID: 90697f8177cc
Revises: f3d5946e5bbf
Create Date: 2026-04-02 09:08:00.125857

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '90697f8177cc'
down_revision: Union[str, None] = 'f3d5946e5bbf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # First, clean up any existing duplicate tickets per session
    # Keep the oldest ticket for each session and delete duplicates
    conn = op.get_bind()

    # Check if tickets table exists
    inspector = sa.inspect(conn)
    if 'tickets' not in inspector.get_table_names():
        # Table doesn't exist yet, skip this migration
        # This can happen if running migrations from scratch
        return

    if conn.dialect.name == 'postgresql':
        # PostgreSQL version
        op.execute("""
            DELETE FROM tickets
            WHERE id IN (
                SELECT t1.id
                FROM tickets t1
                INNER JOIN tickets t2 ON t1.session_id = t2.session_id AND t1.id > t2.id
                WHERE t1.session_id IS NOT NULL
            )
        """)

        # Add unique constraint
        op.create_unique_constraint(
            'uq_tickets_session_id',
            'tickets',
            ['session_id']
        )
    else:
        # SQLite version - SQLite doesn't support the same DELETE syntax
        op.execute("""
            DELETE FROM tickets
            WHERE rowid NOT IN (
                SELECT MIN(rowid)
                FROM tickets
                WHERE session_id IS NOT NULL
                GROUP BY session_id
            )
            AND session_id IS NOT NULL
        """)

        # SQLite: Create unique index (equivalent to constraint)
        op.create_index(
            'uq_tickets_session_id',
            'tickets',
            ['session_id'],
            unique=True
        )


def downgrade() -> None:
    # Remove the unique constraint/index
    conn = op.get_bind()

    if conn.dialect.name == 'postgresql':
        op.drop_constraint('uq_tickets_session_id', 'tickets', type_='unique')
    else:
        op.drop_index('uq_tickets_session_id', 'tickets')
