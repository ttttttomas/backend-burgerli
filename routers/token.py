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
import jwt
import bcrypt
from Database.getConnection import get_connection
import os

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Configuración para JWT
SECRET_KEY = os.getenv("SECRET_KEY", "MdpuF8KsXiRArNlHtl6pXO2XyLSJMTQ8_Burgerli")

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = get_connection()
    if db is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database connection failed")