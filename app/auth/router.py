from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.security import create_access_token, verify_password
from app.usuario.services import UsuarioServiceDep

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}},
)


@router.post("/login")
async def login(
    service: UsuarioServiceDep,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    Endpoint to handle user login.
    It receives a username and password, validates them, and returns an access token.
    """
    user = await service.get_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})

    return {"access_token": access_token, "token_type": "bearer"}
