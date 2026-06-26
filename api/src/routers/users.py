import secrets
import bcrypt
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.engine import Connection
from ..db.session import get_db
from ..db.tables import users, roles
from ..schemas.schemas import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(payload: UserCreate, db: Connection = Depends(get_db)):
    role = db.execute(roles.select().where(roles.c.id == payload.role_id)).fetchone()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    plain_password = payload.password or secrets.token_urlsafe(12)

    result = db.execute(
        users.insert().values(
            name=payload.name,
            email=payload.email,
            password=hash_password(plain_password),
            role_id=payload.role_id,
            created_at=datetime.now(timezone.utc).date(),
        )
    )
    db.commit()
    row = db.execute(users.select().where(users.c.id == result.inserted_primary_key[0])).fetchone()
    data = dict(row._mapping)
    data["password"] = plain_password
    return data


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Connection = Depends(get_db)):
    row = db.execute(users.select().where(users.c.id == user_id)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return row._mapping
