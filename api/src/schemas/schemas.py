from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    description: str


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    role_id: int
    password: Optional[str] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role_id: int
    password: str
