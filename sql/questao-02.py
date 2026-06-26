# Questão 2 — SQLAlchemy Expression Language
#
# Equivalente da consulta SQL da questão 1.
# Retorna: name, email, role description, claim description

from sqlalchemy import select
from api.src.db.tables import users, roles, claims, user_claims

stmt = (
    select(
        users.c.name,
        users.c.email,
        roles.c.description.label("role"),
        claims.c.description.label("claim"),
    )
    .join(roles,       roles.c.id        == users.c.role_id)
    .join(user_claims, user_claims.c.user_id == users.c.id)
    .join(claims,      claims.c.id       == user_claims.c.claim_id)
    .where(claims.c.active == True)
)

# Execução:
#   from api.src.db.engine import engine
#   with engine.connect() as conn:
#       results = conn.execute(stmt).fetchall()
