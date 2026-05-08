from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

# Usuario de prueba — en producción reemplazar con consulta a MongoDB
FAKE_USERS = {
    "admin": {
        "username": "admin",
        "password": "admin123",
        "role": "admin",
    }
}


class LoginRequest(BaseModel):
    username: str = Field(..., examples=["admin"])
    password: str = Field(..., examples=["admin123"])

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesion",
    description="Valida credenciales y entrega un JWT.",
    responses={
        401: {"description": "Credenciales incorrectas"}
    },
)
def login(body: LoginRequest):
    user = FAKE_USERS.get(body.username)

    if not user or body.password != user["password"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return TokenResponse(access_token=token)
