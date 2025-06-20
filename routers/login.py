from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from auth.authentication import oauth2_scheme, get_current_user, create_access_token
from models.user import User
from Database.users import verify_user_credentials, get_user_by_username, create_user
from Database.getConnection import engine
from sqlalchemy import text

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

@router.post("/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    if not verify_user_credentials(form_data.username, form_data.password):
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password"
        )
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

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