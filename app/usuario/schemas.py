from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UsuarioBase(BaseModel):
    username: str
    email: EmailStr
    nome: str
    tenant_id: int


class UsuarioCreate(UsuarioBase):
    password: str


class UsuarioUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    nome: str | None = None
    password: str | None = None
    ativo: bool | None = None


class UsuarioPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    nome: str
    ativo: bool
    tenant_id: int
    created_at: datetime
    updated_at: datetime
