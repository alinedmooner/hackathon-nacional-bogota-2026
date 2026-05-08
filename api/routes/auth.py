from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

# Usuario de prueba — en producción reemplazar con consulta a MongoDB
FAKE_USERS = {
    "admin": {
        "username": "admin",
        "hashed_password": "$2b$12$yt3iVRZuXTDKD63S/zNOeOLie3ad51n1vaMRsXvAy13cyC8NgGV02",
        "role": "admin",
    }
}


class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    user = FAKE_USERS.get(body.username)

    if not user or not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return TokenResponse(access_token=token)
