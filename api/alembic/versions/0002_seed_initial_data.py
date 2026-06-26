"""seed initial data

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-01 00:01:00
"""
from alembic import op
from sqlalchemy.sql import table, column
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

roles_table = table("roles", column("description", sa.String()))
claims_table = table("claims", column("description", sa.String()), column("active", sa.Boolean()))


def upgrade() -> None:
    op.bulk_insert(roles_table, [
        {"description": "admin"},
        {"description": "editor"},
        {"description": "viewer"},
    ])

    op.bulk_insert(claims_table, [
        {"description": "users:read",   "active": True},
        {"description": "users:write",  "active": True},
        {"description": "roles:read",   "active": True},
        {"description": "roles:write",  "active": True},
        {"description": "reports:read", "active": True},
    ])


def downgrade() -> None:
    op.execute("DELETE FROM claims")
    op.execute("DELETE FROM roles")
