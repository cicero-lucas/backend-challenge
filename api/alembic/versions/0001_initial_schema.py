"""initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = inspector.get_table_names()

    if "roles" not in existing:
        op.create_table(
            "roles",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("description", sa.String(), nullable=False),
        )

    if "claims" not in existing:
        op.create_table(
            "claims",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column("description", sa.String(), nullable=False),
            sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        )

    if "users" not in existing:
        op.create_table(
            "users",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("email", sa.String(), nullable=False),
            sa.Column("password", sa.String(), nullable=False),
            sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id"), nullable=False),
            sa.Column("created_at", sa.Date(), nullable=False),
            sa.Column("updated_at", sa.Date(), nullable=True),
        )

    if "user_claims" not in existing:
        op.create_table(
            "user_claims",
            sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("claim_id", sa.BigInteger(), sa.ForeignKey("claims.id"), nullable=False),
            sa.UniqueConstraint("user_id", "claim_id", name="user_claims_un"),
        )


def downgrade() -> None:
    op.drop_table("user_claims")
    op.drop_table("users")
    op.drop_table("claims")
    op.drop_table("roles")
