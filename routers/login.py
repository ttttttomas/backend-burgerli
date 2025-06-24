from fastapi import FastAPI, Depends, HTTPException, APIRouter, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from auth.authentication import oauth2_scheme, get_current_user, create_access_token
from models.user import User
from Database.users import verify_user_credentials, get_user_by_username, create_user, delete_user, get_user_by_id, get_user_by_username_and_password
from Database.getConnection import engine
from sqlalchemy import JSON, text
import uuid
import os

router = APIRouter()

@router.post("/register")
async def register(user: User):
    existing_user = get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    success = create_user(user.username, user.password)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Error creating user"
        )
    return {"message": "User created successfully"}

@router.post("/token")
async def login_for_access_token(
    response: Response,
    ACCESS_TOKEN_EXPIRE_DAYS: int = Cookie(max_age=30),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    # Verificar las credenciales
    if verify_user_credentials(form_data.username, form_data.password):
        # Obtener el usuario pasando ambos parámetros
        user = get_user_by_username_and_password(
            username=form_data.username,
            password=form_data.password
        )
        
        if user is None:
            raise HTTPException(
                status_code=400,
                detail="User  not found after verification"
            )
        
        access_token = create_access_token(
            data={"sub": form_data.username}
        )
        
        response = JSONResponse(
            content={"message": "Login successful, session stored in cookie.", "ID": user.id},
        )
        
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=ACCESS_TOKEN_EXPIRE_DAYS,
            secure=os.getenv("ENV") == "production",
            samesite= None,
        )
        
        return response

@router.get("/protected")
async def protected_route(username: str = Depends(get_current_user)):
    return {"message": f"Hello, {username}! This is a protected resource."}

@router.get("/logout")
async def logout(current_user: str = Depends(get_current_user)):
    return {"message": f"Logged out {current_user}"}

@router.get("/getUsers")
async def get_users():
    try:
        with engine.begin() as conn:
            result = conn.execute(text("SELECT * FROM credentials"))
            rows = result.mappings().all()
            if not rows:
                raise HTTPException(status_code=404, detail="No users found.")
            return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/getUserByID")
async def get_user_by_id_endpoint(id: str):
    user = get_user_by_id(id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user

@router.get("/deleteUser")
async def delete_user_endpoint(id: str):
    success = delete_user(id)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Error deleting user"
        )
    return {"message": "User deleted successfully"}