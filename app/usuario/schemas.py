from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UsuarioBase(BaseModel):
    username: str
    email: EmailStr
    nome: str


class UsuarioCreate(UsuarioBase):
    password: str
    role_profile_id: int | None = None


class UsuarioCreateAdmin(BaseModel):
    """Used by admin to create a user inside a tenant (tenant_id comes from the URL)."""

    username: str
    email: EmailStr
    nome: str
    password: str
    role_profile_id: int | None = None


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
    role_profile_id: int | None
    tenant_id: int
    created_at: datetime
    updated_at: datetime


class RoleProfileBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class UsuarioMe(UsuarioPublic):
    role_profile: RoleProfileBrief | None = None
    permissions: list[str] = []
