from sqlalchemy import (
    Boolean, Column, Date, Integer, BigInteger,
    MetaData, String, Table, ForeignKey,
)

metadata = MetaData()

roles = Table(
    "roles", metadata,
    Column("id", Integer, primary_key=True),
    Column("description", String, nullable=False),
)

claims = Table(
    "claims", metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("description", String, nullable=False),
    Column("active", Boolean, nullable=False, default=True),
)

users = Table(
    "users", metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("name", String, nullable=False),
    Column("email", String, nullable=False),
    Column("password", String, nullable=False),
    Column("role_id", Integer, ForeignKey("roles.id"), nullable=False),
    Column("created_at", Date, nullable=False),
    Column("updated_at", Date, nullable=True),
)

user_claims = Table(
    "user_claims", metadata,
    Column("user_id", BigInteger, ForeignKey("users.id"), nullable=False),
    Column("claim_id", BigInteger, ForeignKey("claims.id"), nullable=False),
)
