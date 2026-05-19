from fastapi import HTTPException, status
from src.core.security import create_access_token

FAKE_USERS = {
    "admin": {"username": "admin", "password": "admin123", "role": "admin"},
}


def login(username: str, password: str) -> dict:
    user = FAKE_USERS.get(username)
    if not user or password != user["password"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return {"access_token": token, "token_type": "bearer"}
