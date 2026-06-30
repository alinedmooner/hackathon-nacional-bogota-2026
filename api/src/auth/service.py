from fastapi import HTTPException, status
from src.core.security import create_access_token, verify_password

FAKE_USERS = {
    "admin": {"username": "admin", "password_hash": "$2b$12$/xEfR4k..hUvj7XaMutX0esFpjxPVCxfQkjL7SV0r3vucVM3aAEeO", "role": "admin"},
}


def login(username: str, password: str) -> dict:
    user = FAKE_USERS.get(username)
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return {"access_token": token, "token_type": "bearer"}
