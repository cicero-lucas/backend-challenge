from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.engine import Connection
from ..db.session import get_db
from ..db.tables import roles
from ..schemas.schemas import RoleResponse

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("/{role_id}", response_model=RoleResponse)
def get_role(role_id: int, db: Connection = Depends(get_db)):
    row = db.execute(roles.select().where(roles.c.id == role_id)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Role not found")
    return row._mapping
