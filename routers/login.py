from fastapi import FastAPI, Depends, HTTPException, APIRouter, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from auth.authentication import oauth2_scheme, get_current_user, create_access_token
from models.user import User
from Database.users import verify_user_credentials, get_user_by_username, create_user, delete_user, get_user_by_id
from Database.getConnection import engine
from sqlalchemy import text
import uuid

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
    ACCESS_TOKEN_EXPIRE_DAYS: int = Cookie(default=30, max_age=30),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = verify_user_credentials(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(
        data={"sub": form_data.username}
    )
    
    response.set_cookie(
        key="access_token", 
        value=access_token,  
        httponly=True,       
        max_age=ACCESS_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  
        expires=ACCESS_TOKEN_EXPIRE_DAYS * 24 * 60 * 60, 
        secure=True,        
        samesite="lax"     
    )
    
    return {
        "message": "Login successful, session stored in cookie.",
        "ID": user.id
    }

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