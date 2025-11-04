from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, status, HTTPException, Request
from fastapi.websockets import WebSocket
from jose import JWTError, jwt, ExpiredSignatureError
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import text
from Database.getConnection import engine

from models.user import User

SECRET_KEY = "MdpuF8KsXiRArNlHtl6pXO2XyLSJMTQ8_Burgerli"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

class WSAuthError(Exception):
    def __init__(self, code: int = 1008, reason: str = ""):
        self.code = code
        self.reason = reason
        super().__init__(reason)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    auto_error=True,
    scheme_name="OAuth2PasswordBearer",
    description="Autenticación mediante usuario y contraseña"
)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(payload)
        if id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload

def get_current_user(request: Request):
    # 👇 la cookie que VOS pusiste. Si se llama distinto, cambiá esto.
    token = request.cookies.get("Authorization")

    # Swagger NO manda cookies ⇒ esto se va a disparar ahí
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token not found in cookies",
        )

    # por si viene como "Bearer xxx"
    if token.startswith("Bearer "):
        token = token[len("Bearer "):]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        # token roto / expirado
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    # acá depende de cómo LO GENERASTE
    user_id = payload.get("id")  # o "sub"
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # buscar en la db
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT id_user, name, role, branch FROM users WHERE id_user = :id"),
            {"id": user_id},
        ).mappings().first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # lo que le va a llegar al endpoint
    return {
        "id": row["id"],
        "username": row["username"],
        "rol": row["rol"],
        "local": row["local"],
    }

async def get_current_user_ws(token: str) -> str:
    if not token:
        raise WSAuthError(1008, "Missing token")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise WSAuthError(1008, "Expired token")
    except JWTError:
        raise WSAuthError(1008, "Invalid token")

    user_id = payload.get("user_id") or payload.get("sub") or payload.get("username")
    if not user_id:
        raise WSAuthError(1008, "Missing user id in token")

    return str(user_id)