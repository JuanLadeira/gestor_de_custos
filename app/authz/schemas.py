from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PermissionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    grupo: str
    descricao: str | None


class RoleCreate(BaseModel):
    nome: str
    descricao: str | None = None
    permission_codes: list[str] = []


class RoleUpdate(BaseModel):
    nome: str | None = None
    descricao: str | None = None
    permission_codes: list[str] | None = None


class RolePublic(BaseModel):
    id: int
    nome: str
    descricao: str | None
    is_system: bool
    permission_codes: list[str]
    created_at: datetime
    updated_at: datetime


class ProfileCreate(BaseModel):
    nome: str
    descricao: str | None = None
    role_ids: list[int] = []


class ProfileUpdate(BaseModel):
    nome: str | None = None
    descricao: str | None = None
    role_ids: list[int] | None = None


class ProfilePublic(BaseModel):
    id: int
    nome: str
    descricao: str | None
    is_system: bool
    is_protected: bool
    role_ids: list[int]
    created_at: datetime
    updated_at: datetime


class AssignProfileRequest(BaseModel):
    role_profile_id: int
