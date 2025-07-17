from queue import PriorityQueue
import re
from fastapi import FastAPI, Depends, HTTPException, APIRouter, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from auth.authentication import oauth2_scheme, get_current_user, create_access_token
from models.user import User
from Database.users import verify_user_credentials, get_user_by_username, create_user, delete_user, get_user_by_id, get_user_by_username_and_password, update_user
from Database.getConnection import engine
from sqlalchemy import JSON, text
import uuid
import os

IS_LOCAL = os.getenv("ENV") == "dev"

router = APIRouter()

@router.post("/register", tags=["Login & Register"])
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

@router.post("/token", tags=["Login & Register"])

async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    if verify_user_credentials(form_data.username, form_data.password):
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
            content={"message": "Login successful, session stored in cookie.", "Token": access_token, "ID": user.id},
        )
        
        response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        )
        
        return response

@router.get("/protected", tags=["Login & Register"])
async def protected_route(username: str = Depends(get_current_user)):
    print("🧪 Usuario autenticado:", username)
    return {"message": f"Hello, {username}! This is a protected resource."}

@router.get("/logout", tags=["Login & Register"])
async def logout(current_user: str = Depends(get_current_user)):
    return {"message": f"Logged out {current_user}"}

@router.get("/getUsers", tags=["Login & Register"])
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

@router.get("/getUserByID", tags=["Login & Register"])
async def get_user_by_id_endpoint(id: str):
    user = get_user_by_id(id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user

@router.put("/updateUser", tags=["Login & Register"])
async def update_user_endpoint(id: str, user: User):
    user_db = get_user_by_id(id)
    if not user_db:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    success = update_user(id, user.username, user.password, user.rol, user.local)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Error updating user"
        )
    return {"message": "User updated successfully"}

@router.delete("/deleteUser", tags=["Login & Register"])
async def delete_user_endpoint(id: str):
    success = delete_user(id)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Error deleting user"
        )
    return {"message": "User deleted successfully"}
