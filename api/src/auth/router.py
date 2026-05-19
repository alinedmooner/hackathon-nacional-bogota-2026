from fastapi import APIRouter
from pydantic import BaseModel, Field
from src.auth import service as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str = Field(..., examples=["admin"])
    password: str = Field(..., examples=["admin123"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse,
             summary="Iniciar sesion",
             responses={401: {"description": "Credenciales incorrectas"}})
def login(body: LoginRequest):
    return auth_service.login(body.username, body.password)
