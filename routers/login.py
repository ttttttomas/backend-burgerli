from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models.user import User
from models.token import Token
from schemas.user import UserCreate, UserUpdate
from schemas.token import TokenCreate
from jose import jwt
import bcrypt
from Database.getConnection import get_connection
import os

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Configuración para JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = get_connection()
    if db is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database connection failed")
    
    try:
        user = db.query(User).filter(User.email == form_data.username).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
        if not bcrypt.checkpw(form_data.password.encode('utf-8'), user.password.encode('utf-8')):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
        token = jwt.encode({'access_token': user.id}, SECRET_KEY, algorithm='HS256')
        return {"access_token": token, "token_type": "bearer"}
    finally:
        db.close()
