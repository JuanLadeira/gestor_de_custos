from http import HTTPStatus
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import DecodeError, ExpiredSignatureError, decode

from app.settings import Settings
from app.usuario.models import Usuario
from app.usuario.services import UsuarioServiceDep

settings = Settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", refreshUrl="auth/refresh")

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM


async def get_current_user(
    service: UsuarioServiceDep,
    token: str = Depends(oauth2_scheme),
) -> Usuario:
    credentials_exception = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        if not username:
            raise credentials_exception

    except DecodeError:
        raise credentials_exception

    except ExpiredSignatureError:
        raise credentials_exception

    user = await service.get_by_username(username)
    if not user:
        raise credentials_exception

    return user


CurrentUser = Annotated[Usuario, Depends(get_current_user)]
