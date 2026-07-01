from collections.abc import Callable
from http import HTTPStatus
from typing import Annotated

from fastapi import Depends, HTTPException, Request

from app.auth.current_user import CurrentUser
from app.authz.service import AuthzServiceDep


async def get_current_permissions(
    request: Request,
    current_user: CurrentUser,
    service: AuthzServiceDep,
) -> set[str]:
    cached = getattr(request.state, "permissions", None)
    if cached is not None:
        return cached
    perms = await service.resolve_permissions(current_user)
    request.state.permissions = perms
    return perms


CurrentPermissions = Annotated[set[str], Depends(get_current_permissions)]


def require(*codes: str) -> Callable:
    async def _checker(permissions: CurrentPermissions) -> None:
        missing = [c for c in codes if c not in permissions]
        if missing:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail=f"Permissão necessária: {', '.join(missing)}",
            )

    return _checker
