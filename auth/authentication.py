from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, Request
from fastapi.websockets import WebSocket
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

from models.user import User

SECRET_KEY = "MdpuF8KsXiRArNlHtl6pXO2XyLSJMTQ8_Burgerli"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

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
    token = request.cookies.get("Authorization")
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Token not found in cookies",
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = payload.get("user_id")
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user_ws(websocket: WebSocket, token: str) -> str:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception
